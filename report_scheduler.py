import smtplib, os, schedule, time
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime

print("🚀 Starting JRAVIS Mission 2040 Report Worker...")

LOCK_CODE = os.getenv("LOCK_CODE", "204040")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("App_password")
RECEIVER = os.getenv("DAILY_REPORT_EMAIL")


def generate_summary_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200,
             10,
             "Mission 2040 – Daily Summary Report",
             ln=True,
             align="C")
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(
        0, 10, f"""
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Status: Automated Daily Summary
Progress: Phase 1 systems operational
""")
    file_name = f"{datetime.now().strftime('%d-%m-%Y')}_summary_report.pdf"
    pdf.output(file_name)
    return file_name


def generate_invoice_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Mission 2040 – Daily Invoices", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "Invoices for all income streams will appear here.")
    file_name = f"{datetime.now().strftime('%d-%m-%Y')}_invoices.pdf"
    pdf.output(file_name)
    return file_name


def send_email_with_pdfs():
    summary_file = generate_summary_pdf()
    invoice_file = generate_invoice_pdf()

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = RECEIVER
    msg["Subject"] = f"Mission 2040 Daily Report – {datetime.now().strftime('%d-%m-%Y')}"
    msg.set_content(f"Attached are today's reports.\nLock Code: {LOCK_CODE}")

    for file in [summary_file, invoice_file]:
        with open(file, "rb") as f:
            msg.add_attachment(f.read(),
                               maintype="application",
                               subtype="pdf",
                               filename=file)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)
        print("✅ Daily report emailed successfully.")


# Schedulers
schedule.every().day.at("10:00").do(send_email_with_pdfs)
schedule.every().sunday.at("00:00").do(send_email_with_pdfs)

print("📅 JRAVIS Daily/Weekly Report Scheduler Running...")
while True:
    schedule.run_pending()
    time.sleep(30)

# 🔽 Temporary manual trigger for testing
send_email_with_pdfs()
