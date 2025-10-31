# --- JRAVIS Daily Report: full orchestrator + scheduler ---
import os
import logging
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict

from fastapi import Query, HTTPException
from fastapi.responses import JSONResponse

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
import schedule

# ENV / defaults
ADMIN_CODE = os.getenv("REPORT_API_CODE", "2040")
VA_EMAIL = os.getenv("VA_EMAIL")
VA_EMAIL_PASS = os.getenv("VA_EMAIL_PASS")
LOCK_CODE = os.getenv("LOCK_CODE", "2040")
RECIPIENT = os.getenv("REPORT_RECIPIENT", "nrveeresh327@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "Dhruvayu - VA BOT")
BASE_URL = os.getenv("BASE_URL", "https://jravis-backend.onrender.com")

logging.basicConfig(level=logging.INFO)

# In-memory simple token store for approvals
approval_tokens: Dict[str, Dict] = {}
approval_lock = threading.Lock()


# ---- PDF helpers ----
def create_simple_pdf(title: str, lines: list, out_path: str):
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, title)
    y -= 28
    c.setFont("Helvetica", 10)
    for line in lines:
        c.drawString(72, y, line)
        y -= 14
        if y < 72:
            c.showPage()
            y = height - 72
    c.showPage()
    c.save()


def encrypt_pdf(input_path: str, output_path: str, password: str):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    # user password to open file
    writer.encrypt(user_pwd=password, owner_pwd=None, use_128bit=True)
    with open(output_path, "wb") as f:
        writer.write(f)


# ---- Email helper ----
def send_email_with_attachments(subject: str, html_body: str,
                                attachments: Dict[str, bytes]):
    if not VA_EMAIL or not VA_EMAIL_PASS:
        logging.error("Missing VA_EMAIL / VA_EMAIL_PASS in env.")
        raise RuntimeError("Missing email credentials")

    msg = MIMEMultipart()
    msg["From"] = f"{FROM_NAME} <{VA_EMAIL}>"
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    for filename, data in attachments.items():
        part = MIMEApplication(data, Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(VA_EMAIL, VA_EMAIL_PASS)
        server.send_message(msg)
    logging.info("📧 Email with attachments sent successfully.")


# ---- Business task executed after approval or auto-resume ----
def perform_daily_tasks(report_date_str: str):
    # <<< Replace this body with real JRAVIS actions: update DB, kick workflows, save logs, etc. >>>
    logging.info(f"Performing JRAVIS daily tasks for {report_date_str} ...")
    # simulate work
    time.sleep(1)
    logging.info("Daily tasks completed.")
    # <<< end replacement area >>>


# ---- Orchestrator ----
def orchestrate_and_wait_for_approval(report_date_str: str, lock_code: str):
    logging.info("Starting orchestrator thread...")
    with tempfile.TemporaryDirectory() as td:
        summary_plain = os.path.join(td, "summary_plain.pdf")
        summary_encrypted = os.path.join(td, "summary_encrypted.pdf")
        invoice_pdf = os.path.join(td, "invoice.pdf")

        # TODO: replace these lines with actual log extraction from your system
        summary_lines = [
            f"Date: {report_date_str}",
            "1) What VA Bot did yesterday: (fill with real data)",
            "2) What VA Bot will do today: (fill with real data)",
            "3) What VA Bot will do tomorrow: (fill with real data)",
            "4) Today's scheduled tasks: (fill with real data)",
            "5) Status of yesterday's tasks: (fill with real data)",
            "6) Areas the team is working on: (fill with real data)",
            "7) Issues / progress updates: (fill with real data)",
            "8) Total earnings so far: ₹X (distance to target: ₹Y)", "",
            "This Summary PDF is locked with your lock code."
        ]
        invoice_lines = [
            f"Invoice Date: {report_date_str}",
            "Invoice details: (fill with real invoice data)", "Total: ₹XXXXX"
        ]

        create_simple_pdf("JRAVIS Summary Report", summary_lines,
                          summary_plain)
        create_simple_pdf("JRAVIS Invoice", invoice_lines, invoice_pdf)

        # Encrypt summary
        encrypt_pdf(summary_plain, summary_encrypted, lock_code)

        with open(summary_encrypted, "rb") as f:
            summary_bytes = f.read()
        with open(invoice_pdf, "rb") as f:
            invoice_bytes = f.read()

        # create approval token and link
        token = str(uuid.uuid4())
        approve_link = f"{BASE_URL}/api/approve?token={token}"

        expiry = datetime.utcnow() + timedelta(minutes=10)
        with approval_lock:
            approval_tokens[token] = {
                "approved": False,
                "expiry": expiry,
                "created_at": datetime.utcnow()
            }

        subject = f"✅ JRAVIS Daily Report — {report_date_str}"
        body_html = f"""
        <p>Boss, VA BOT has completed today's scheduled tasks.</p>
        <p><b>Summary PDF:</b> Encrypted with your lock code.</p>
        <p><b>Invoice PDF:</b> Attached (no lock).</p>
        <p>
          <a href="{approve_link}" style="display:inline-block;padding:10px 16px;
             background:#0b74de;color:#fff;text-decoration:none;border-radius:6px;">
             Approve Now
          </a>
        </p>
        <p>If you do not click approve within 10 minutes, VA BOT will auto-resume work.</p>
        """

        attachments = {
            f"{report_date_str} summary.pdf": summary_bytes,
            f"{report_date_str} invoices.pdf": invoice_bytes,
        }

        try:
            send_email_with_attachments(subject, body_html, attachments)
        except Exception as e:
            logging.exception("Failed to send approval email")
            # still proceed with auto-resume after logging
        logging.info(
            f"Approval email sent with token {token}. Waiting up to 10 minutes."
        )

        # wait up to 10 minutes for approval
        waited = 0
        approved = False
        while waited < 600:
            with approval_lock:
                state = approval_tokens.get(token)
                if state and state.get("approved"):
                    approved = True
                    break
            time.sleep(3)
            waited += 3

        if approved:
            logging.info("Approval received. Proceeding with daily tasks.")
            perform_daily_tasks(report_date_str)
        else:
            logging.info(
                "No approval within 10 minutes. Auto-resuming daily tasks.")
            perform_daily_tasks(report_date_str)

        with approval_lock:
            approval_tokens.pop(token, None)


# ---- HTTP endpoints ----
@app.get("/api/send_daily_report")
def send_daily_report(code: str = Query(...)):
    if code != ADMIN_CODE:
        raise HTTPException(status_code=401, detail="Invalid code")
    report_date_str = datetime.now().strftime("%d-%m-%Y")
    threading.Thread(target=orchestrate_and_wait_for_approval,
                     args=(report_date_str, LOCK_CODE),
                     daemon=True).start()
    return JSONResponse({
        "detail": "Daily report orchestrator started",
        "date": report_date_str
    })


@app.get("/api/approve")
def approve(token: str = Query(...)):
    with approval_lock:
        t = approval_tokens.get(token)
        if not t:
            return JSONResponse({"detail": "Invalid or expired token."},
                                status_code=404)
        t["approved"] = True
    return JSONResponse(
        {"detail": "Approval recorded. VA BOT will proceed immediately."})


# ---- Scheduler: trigger the endpoint daily at 10:00 AM IST ----
def trigger_daily_report():
    try:
        url = f"{BASE_URL}/api/send_daily_report?code={ADMIN_CODE}"
        r = requests.get(url, timeout=30)
        logging.info(
            f"[Scheduler] Triggered daily report: {r.status_code} {r.text}")
    except Exception as e:
        logging.error(f"[Scheduler] Failed to trigger daily report: {e}")


# Schedule job; this runs in background thread and does not block startup
schedule.every().day.at("10:00").do(trigger_daily_report)


def scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(60)


threading.Thread(target=scheduler_loop, daemon=True).start()

# --- end JRAVIS Daily Report block ---


# ---- Weekly Report Scheduler (Sunday 12:00 AM IST) ----
def orchestrate_weekly_report():
    report_date_str = datetime.now().strftime("%d-%m-%Y")
    week_label = datetime.now().strftime("Week-%W %Y")
    logging.info(f"🗓️  Starting Weekly JRAVIS Report for {week_label}")

    with tempfile.TemporaryDirectory() as td:
        weekly_summary_plain = os.path.join(td, "weekly_summary.pdf")
        weekly_summary_encrypted = os.path.join(
            td, "weekly_summary_encrypted.pdf")
        weekly_invoice_pdf = os.path.join(td, "weekly_invoice.pdf")

        # You can replace below with real weekly aggregation later
        summary_lines = [
            f"Weekly Summary Report — {week_label}",
            f"Generated on: {report_date_str}", "",
            "1) Total tasks completed this week: (fill from logs)",
            "2) Weekly earnings: ₹XXXXX",
            "3) Pending actions carried forward:",
            "4) Upcoming goals for next week:", "5) Issues / highlights:", "",
            "This report is encrypted with your lock code."
        ]
        invoice_lines = [
            f"Weekly Invoice — {week_label}",
            f"Generated on: {report_date_str}", "",
            "Invoice details for the week:", "Total Amount: ₹XXXXX", "",
            "Thank you, Boss!"
        ]

        create_simple_pdf("JRAVIS Weekly Summary", summary_lines,
                          weekly_summary_plain)
        create_simple_pdf("JRAVIS Weekly Invoice", invoice_lines,
                          weekly_invoice_pdf)

        encrypt_pdf(weekly_summary_plain, weekly_summary_encrypted, LOCK_CODE)

        with open(weekly_summary_encrypted, "rb") as f:
            summary_bytes = f.read()
        with open(weekly_invoice_pdf, "rb") as f:
            invoice_bytes = f.read()

        token = str(uuid.uuid4())
        approve_link = f"{BASE_URL}/api/approve?token={token}"
        expiry = datetime.utcnow() + timedelta(minutes=10)
        with approval_lock:
            approval_tokens[token] = {
                "approved": False,
                "expiry": expiry,
                "created_at": datetime.utcnow()
            }

        subject = f"📅 JRAVIS Weekly Report — {week_label}"
        body_html = f"""
        <p>Boss, here’s your JRAVIS Weekly Summary and Invoice for {week_label}.</p>
        <p><b>Summary PDF:</b> Encrypted with your lock code.</p>
        <p><b>Invoice PDF:</b> Attached (no lock).</p>
        <p>
          <a href="{approve_link}" style="display:inline-block;padding:10px 16px;
             background:#0b74de;color:#fff;text-decoration:none;border-radius:6px;">
             Approve Now
          </a>
        </p>
        <p>If no approval in 10 minutes, VA BOT will auto-resume work.</p>
        """

        attachments = {
            f"{week_label} summary.pdf": summary_bytes,
            f"{week_label} invoices.pdf": invoice_bytes,
        }

        try:
            send_email_with_attachments(subject, body_html, attachments)
        except Exception as e:
            logging.exception("Failed to send weekly email")

        waited = 0
        approved = False
        while waited < 600:
            with approval_lock:
                state = approval_tokens.get(token)
                if state and state.get("approved"):
                    approved = True
                    break
            time.sleep(3)
            waited += 3

        if approved:
            logging.info("Weekly report approved. Executing weekly tasks.")
            perform_daily_tasks(report_date_str)  # reuse daily task handler
        else:
            logging.info("Weekly report auto-resuming tasks.")
            perform_daily_tasks(report_date_str)

        with approval_lock:
            approval_tokens.pop(token, None)
    logging.info(f"✅ Weekly JRAVIS Report process completed for {week_label}")


# ---- Schedule it: Sunday 12:00 AM IST ----
schedule.every().sunday.at("00:00").do(orchestrate_weekly_report)
