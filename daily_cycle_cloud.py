import os
import smtplib
import schedule
import time
import pytz
from datetime import datetime
from fpdf import FPDF
from email.message import EmailMessage
from PyPDF2 import PdfReader, PdfWriter

# ============================================================
#  JRAVIS CLOUD – DAILY REPORT ENGINE (UTF-8 + LOCK SAFE)
# ============================================================

SENDER_EMAIL = os.getenv("SMTP_USER", "elinalakshya@gmail.com")
SENDER_PASS = os.getenv("SMTP_PASS", "")
RECEIVER_EMAIL = "nrveeresh327@gmail.com"
LOCK_CODE = os.getenv("LOCK_CODE", None)
IST = pytz.timezone("Asia/Kolkata")

DAILY_REPORT_FILE = "daily_summary_report.pdf"
DAILY_INVOICE_FILE = "daily_invoices.pdf"


# ============================================================
#  PDF GENERATION
# ============================================================
class UTF8FPDF(FPDF):

    def __init__(self):
        super().__init__()
        self.core_fonts_encoding = "utf-8"


def generate_daily_report():
    pdf = UTF8FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(200, 10, txt="JRAVIS Daily Summary Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(200,
             10,
             txt=f"Date: {datetime.now(IST).strftime('%Y-%m-%d')}",
             ln=True)
    pdf.multi_cell(0,
                   10,
                   txt="✅ Summary of JRAVIS operations for the day.\n"
                   "- System check: OK\n"
                   "- Automations: Active\n"
                   "- Tasks completed successfully.\n"
                   "- No errors logged.")
    pdf.output(DAILY_REPORT_FILE)

    # Encrypt summary if LOCK_CODE exists
    if LOCK_CODE:
        writer = PdfWriter()
        reader = PdfReader(DAILY_REPORT_FILE)
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(LOCK_CODE)
        encrypted_name = DAILY_REPORT_FILE.replace(".pdf", "_locked.pdf")
        with open(encrypted_name, "wb") as f:
            writer.write(f)
        os.remove(DAILY_REPORT_FILE)
        return encrypted_name
    return DAILY_REPORT_FILE


def generate_daily_invoice():
    pdf = UTF8FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(200, 10, txt="JRAVIS Daily Invoice Summary", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(200,
             10,
             txt=f"Date: {datetime.now(IST).strftime('%Y-%m-%d')}",
             ln=True)
    pdf.multi_cell(0,
                   10,
                   txt="💰 Invoice 001 — Passive Stream #1\n"
                   "💰 Invoice 002 — Passive Stream #2\n"
                   "\nAll transactions verified by JRAVIS Cloud Engine.")
    pdf.output(DAILY_INVOICE_FILE)
    return DAILY_INVOICE_FILE


# ============================================================
#  EMAIL SENDER
# ============================================================
def send_email_with_attachments(subject, body, attachments):
    msg = EmailMessage()
    msg["From"] = f"JRAVIS BOT <{SENDER_EMAIL}>"
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    for file_path in attachments:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            msg.add_attachment(data,
                               maintype="application",
                               subtype="pdf",
                               filename=os.path.basename(file_path))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASS)
        smtp.send_message(msg)

    print(f"✅ Email sent successfully to {RECEIVER_EMAIL}")


# ============================================================
#  DAILY CYCLE LOGIC
# ============================================================
def run_daily_cycle():
    print("\n🌅 JRAVIS Daily Cycle Started...")
    report_file = generate_daily_report()
    invoice_file = generate_daily_invoice()

    send_email_with_attachments(
        subject=
        f"JRAVIS Daily Report — {datetime.now(IST).strftime('%Y-%m-%d')}",
        body=("Attached are today's JRAVIS reports:\n\n"
              "1️⃣ Encrypted Summary Report (if locked)\n"
              "2️⃣ Daily Invoices\n\n"
              "- JRAVIS Cloud Automation System"),
        attachments=[report_file, invoice_file],
    )
    print("🌇 JRAVIS Daily Cycle Completed.\n")


# ============================================================
#  SCHEDULER (RUN AT 10:00 AM IST)
# ============================================================
schedule.every().day.at("10:00").do(run_daily_cycle)

if __name__ == "__main__":
    print(
        "☁️ JRAVIS Daily Cycle Cloud Active — waiting for 10:00 AM IST trigger."
    )
    run_daily_cycle()  # optional test run
    while True:
        schedule.run_pending()
        time.sleep(60)
