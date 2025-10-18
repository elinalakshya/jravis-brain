import json
import io
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
from datetime import datetime
import requests
import logging


# send_email_with_pdfs() - generate PDFs from memory and send via SMTP
def send_email_with_pdfs():
    logging.info("📨 Preparing Mission 2040 Daily Report PDFs...")

    # 1) Try to load memory data from local file, then fallback to JRAVIS API
    memory = None
    try:
        mem_path = os.getenv("JRAVIS_MEMORY_DB", "memory_data.json")
        if os.path.exists(mem_path):
            with open(mem_path, "r") as f:
                memory = json.load(f)
            logging.info(f"📥 Loaded memory data from {mem_path}")
        else:
            # fallback to JRAVIS endpoint
            JRAVIS_URL = os.getenv("JRAVIS_URL",
                                   "https://jravis-brain.onrender.com")
            try:
                r = requests.get(f"{JRAVIS_URL}/api/memory_snapshot",
                                 timeout=10)
                if r.ok:
                    memory = r.json()
                    logging.info("📥 Loaded memory snapshot from JRAVIS API")
            except Exception as e:
                logging.warning(
                    "⚠️ Could not fetch memory snapshot from JRAVIS: %s" % e)
    except Exception as e:
        logging.error("❌ Error reading memory: %s" % e)

    if not memory:
        memory = {"income_history": [], "recent_activity": []}
        logging.warning("⚠️ No memory found — generating empty reports")

    # 2) Build summary content
    summary_ts = datetime.utcnow().isoformat() + "Z"
    history = memory.get("income_history", [])
    activity = memory.get("recent_activity", [])

    # compute totals (best-effort)
    total_earnings = 0
    for day in history:
        # day may be dict with structure; try to find a numeric value
        if isinstance(day, dict):
            # allow both data and earnings
            if "earnings" in day:
                total_earnings += float(day.get("earnings", 0) or 0)
            elif "total" in day:
                total_earnings += float(day.get("total", 0) or 0)

    # 3) Create Summary PDF
    def build_summary_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Mission 2040 — Daily Summary", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.ln(4)
        pdf.cell(0, 8, f"Generated: {summary_ts}", ln=True)
        pdf.ln(6)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Earnings Overview", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.ln(2)
        pdf.cell(0,
                 8,
                 f"Total (recent window): ₹ {int(total_earnings):,}",
                 ln=True)
        pdf.ln(6)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Recent Income History", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.ln(2)

        if history:
            for e in history[:20]:
                # flexible formatting
                if isinstance(e, dict):
                    label = e.get("date") or e.get("day") or str(e)
                    val = e.get("earnings") or e.get("total") or ""
                    pdf.cell(0, 7, f"{label} — ₹ {val}", ln=True)
                else:
                    pdf.cell(0, 7, str(e), ln=True)
        else:
            pdf.cell(0, 7, "No history records available.", ln=True)

        pdf.ln(6)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Recent Activity", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.ln(2)
        if activity:
            for a in activity[:20]:
                msg = a.get("event") or a.get("message") or str(a)
                ts = a.get("time") or a.get("timestamp") or ""
                pdf.cell(0, 7, f"{ts} — {msg}", ln=True)
        else:
            pdf.cell(0, 7, "No activity logged.", ln=True)

        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return buf

    # 4) Create Invoice PDF (simple aggregated invoice)
    def build_invoice_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Mission 2040 — Invoice Pack", ln=True)
        pdf.ln(6)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"Issue Date: {summary_ts}", ln=True)
        pdf.ln(6)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Line Items", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.ln(4)

        # If memory has breakdowns, enumerate
        breakdown = None
        # try usual places
        if history and isinstance(history[0], dict) and "data" in history[0]:
            # historical wrapper
            breakdown = history[0]["data"].get("breakdown") if isinstance(
                history[0]["data"], dict) else None

        # fallback: if the memory store has latest data under 'data'
        if not breakdown:
            latest = memory.get("income_history", [])
            if latest and isinstance(latest[0], dict):
                breakdown = latest[0].get("streams") or latest[0].get(
                    "breakdown") or None

        # fallback: no breakdown, make aggregated line
        if breakdown and isinstance(breakdown, dict):
            for k, v in breakdown.items():
                pdf.cell(0, 7, f"{k} — ₹ {v}", ln=True)
        else:
            pdf.cell(0,
                     7,
                     f"Total Earnings — ₹ {int(total_earnings):,}",
                     ln=True)

        pdf.ln(8)
        pdf.set_font("Arial", "", 10)
        pdf.cell(
            0,
            7,
            "Notes: This invoice is auto-generated for Mission 2040 reporting.",
            ln=True)

        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return buf

    summary_pdf_buf = build_summary_pdf()
    invoice_pdf_buf = build_invoice_pdf()

    # 5) Optional PDF encryption using pikepdf — try it, fallback if missing
    def maybe_encrypt(pdf_buf, out_name):
        password = LOCK_CODE if LOCK_CODE else None
        if not password:
            # no lock code set -> return original bytes
            return pdf_buf.getvalue(), False
        try:
            import pikepdf
            # write temp in-memory, pikepdf requires bytes->open via BytesIO not supported directly so use temp files
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False,
                                             suffix=".pdf") as t_in:
                t_in.write(pdf_buf.getvalue())
                t_in.flush()
                tmp_in = t_in.name
            out_path = out_name
            pdf = pikepdf.Pdf.open(tmp_in)
            pdf.save(out_path,
                     encryption=pikepdf.Encryption(owner=password,
                                                   user=password,
                                                   R=4))
            with open(out_path, "rb") as f:
                data = f.read()
            return data, True
        except Exception as e:
            logging.warning(
                f"⚠️ PDF encryption skipped (pikepdf missing or error): {e}")
            return pdf_buf.getvalue(), False

    summary_bytes, summary_encrypted = maybe_encrypt(
        summary_pdf_buf, "summary_report_locked.pdf")
    invoice_bytes, invoice_encrypted = maybe_encrypt(
        invoice_pdf_buf, "invoice_report_locked.pdf")

    # 6) Build and send email
    msg = EmailMessage()
    msg["Subject"] = f"Mission 2040 — Daily Report {datetime.utcnow().date().isoformat()}"
    msg["From"] = EMAIL_USER
    msg["To"] = RECEIVER or EMAIL_USER
    msg.set_content(
        "Attached: Mission 2040 Summary and Invoices. (Lock applied if available)"
    )

    # Attach summary
    msg.add_attachment(summary_bytes,
                       maintype="application",
                       subtype="pdf",
                       filename=("summary_report_locked.pdf" if
                                 summary_encrypted else "summary_report.pdf"))
    # Attach invoice
    msg.add_attachment(invoice_bytes,
                       maintype="application",
                       subtype="pdf",
                       filename=("invoice_report_locked.pdf" if
                                 invoice_encrypted else "invoice_report.pdf"))

    # SMTP send
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        logging.info("✅ Daily report emailed successfully.")
    except Exception as e:
        logging.error(f"❌ Email sending failed: {e}")

    # 7) Save copies locally (for records)
    try:
        with open(
                f"reports/summary_{datetime.utcnow().date().isoformat()}.pdf",
                "wb") as f:
            f.write(summary_bytes)
        with open(
                f"reports/invoice_{datetime.utcnow().date().isoformat()}.pdf",
                "wb") as f:
            f.write(invoice_bytes)
        logging.info("💾 Saved report copies to /reports/")
    except Exception as e:
        logging.warning(f"⚠️ Could not save reports locally: {e}")
