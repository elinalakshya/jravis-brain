import os
import smtplib
import schedule
import time
import logging
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime
import requests
from io import BytesIO

# ==============================================
# 🔧 Setup
# ==============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

LOCK_CODE = os.getenv("LOCK_CODE", "204040")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("App_password")
RECEIVER = os.getenv("DAILY_REPORT_EMAIL")


# ==============================================
# 🧠 Mock Memory (replace with DB later)
# ==============================================
def read_memory():
    """Simulated data source"""
    try:
        # Example mock income data
        return {
            "printify": 12000,
            "meshy": 8000,
            "youtube": 4500,
            "kdp": 2000,
        }
    except Exception as e:
        logging.error(f"❌ Error reading memory: {e}")
        return {}


# ==============================================
# 📄 Safe text (for Unicode handling in FPDF)
# ==============================================
def safe_text(text):
    return text.encode("latin-1", "replace").decode("latin-1")


# ==============================================
# 🧾 Build Summary PDF
# ==============================================
def build_summary_pdf():
    data = read_memory()
    total_earnings = sum(data.values())
    summary_ts = datetime.utcnow().isoformat() + "Z"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_doc_option("core_fonts_encoding", "utf-8")
    pdf.cell(0, 10, safe_text("Mission 2040 — Daily Summary"), ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(4)
    pdf.cell(0, 8, safe_text(f"Generated: {summary_ts}"), ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, safe_text("Earnings Overview"), ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(2)
    for k, v in data.items():
        pdf.cell(0, 8, safe_text(f"{k.title():<15} ₹ {v:,}"), ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, safe_text(f"Total Earnings: ₹ {total_earnings:,}"), ln=True)

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf


# ==============================================
# 🧾 Build Invoice PDF
# ==============================================
def build_invoice_pdf():
    summary_ts = datetime.utcnow().isoformat() + "Z"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_doc_option("core_fonts_encoding", "utf-8")
    pdf.cell(0, 10, safe_text("Mission 2040 — Invoice Pack"), ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, safe_text(f"Issue Date: {summary_ts}"), ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, safe_text("Line Items"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.ln(4)
    pdf.cell(0, 8, safe_text("1. Service Charge — ₹ 500"), ln=True)
    pdf.cell(0, 8, safe_text("2. Tax (18%) — ₹ 90"), ln=True)
    pdf.cell(0, 8, safe_text("3. Net Payable — ₹ 590"), ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0,
             8,
             safe_text("Thank you for your trust in Mission 2040!"),
             ln=True)

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf


# ==============================================
# 🌐 Notify JRAVIS Brain
# ==============================================
def notify_jravis(summary_text):
    """Send report completion update to JRAVIS Brain."""
    try:
        r = requests.post(
            "https://jravis-brain.onrender.com/api/report_status",
            json={
                "summary": summary_text,
                "timestamp": datetime.now().isoformat()
            },
            timeout=10,
        )
        logging.info("📡 Sent report summary to JRAVIS Brain.")
    except Exception as e:
        logging.warning(f"⚠️ JRAVIS Brain notification failed: {e}")


# ==============================================
# ✉️ Send Email with PDFs
# ==============================================
def send_email_with_pdfs():
    logging.info("📨 Preparing Mission 2040 Daily Report PDFs...")

    try:
        msg = EmailMessage()
        msg["Subject"] = "Mission 2040 — Daily Report"
        msg["From"] = EMAIL_USER
        msg["To"] = RECEIVER
        msg.set_content(
            "Attached are today's Mission 2040 Summary Report and Invoice Pack."
        )

        summary_pdf_buf = build_summary_pdf()
        invoice_pdf_buf = build_invoice_pdf()

        msg.add_attachment(
            summary_pdf_buf.read(),
            maintype="application",
            subtype="pdf",
            filename=
            f"{datetime.now().strftime('%d-%m-%Y')} summary report.pdf",
        )

        msg.add_attachment(
            invoice_pdf_buf.read(),
            maintype="application",
            subtype="pdf",
            filename=f"{datetime.now().strftime('%d-%m-%Y')} invoices.pdf",
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)

        logging.info("✅ Daily report emailed successfully.")
        notify_jravis("Daily Mission 2040 report sent successfully.")

    except Exception as e:
        logging.error(f"❌ Failed to send report: {e}")


# ==============================================
# 🕒 Scheduler
# ==============================================
def run_scheduler():
    logging.info("📅 JRAVIS Daily/Weekly Report Scheduler Running...")
    schedule.every().day.at("10:00").do(send_email_with_pdfs)
    schedule.every().sunday.at("00:00").do(send_email_with_pdfs)

    while True:
        schedule.run_pending()
        time.sleep(30)


# ==============================================
# 🚀 Start
# ==============================================
if __name__ == "__main__":
    logging.info(">>> Debug: Mission 2040 worker starting (Render test)")
    send_email_with_pdfs()  # Manual trigger (for testing)
    run_scheduler()
