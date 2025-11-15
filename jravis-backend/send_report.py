#!/usr/bin/env python3
import os
import sys
import smtplib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime

from reports.utils_pdf import make_summary_pdf, make_invoice_pdf, encrypt_pdf

MODE = sys.argv[1] if len(sys.argv) > 1 else "daily"

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
REPORT_TO_EMAIL = os.getenv("REPORT_TO_EMAIL")
LOCK_CODE = os.getenv("LOCK_CODE", "1234")
APP_BASE = os.getenv("APP_BASE", "")


def collect_data(mode):
    now = datetime.utcnow().isoformat()
    summary = {
        "mode": mode,
        "generated_at_utc": now,
        "yesterday_done": "Auto-inspection cycles: 12",
        "today_plan": "Run Phase-1 tests",
        "tomorrow_plan": "Start Phase-2 rollout",
        "total_earnings_so_far": "₹1,23,456"
    }

    invoices = [{
        "id": "INV-01",
        "amount": "₹12,000"
    }, {
        "id": "INV-02",
        "amount": "₹8,000"
    }]

    return summary, invoices


def send_email(mode, summary_pdf, invoice_pdf):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = REPORT_TO_EMAIL
    msg["Subject"] = f"JRAVIS {mode.capitalize()} Report - {datetime.utcnow().date().isoformat()}"

    approval_link = f"{APP_BASE}/approve?mode={mode}&date={datetime.utcnow().date()}"

    msg.attach(
        MIMEText(
            f"""
        <p>Hello Boss,</p>
        <p>Your {mode} report is attached.</p>
        <p><a href="{approval_link}">Click here to approve</a></p>
        <p>Summary PDF is lock protected.</p>
        <p>— JRAVIS</p>
        """, "html"))

    # Attach encrypted summary PDF
    part_sum = MIMEApplication(summary_pdf, Name="summary.pdf")
    part_sum['Content-Disposition'] = 'attachment; filename="summary.pdf"'
    msg.attach(part_sum)

    # Attach invoice PDF
    part_inv = MIMEApplication(invoice_pdf, Name="invoices.pdf")
    part_inv['Content-Disposition'] = 'attachment; filename="invoices.pdf"'
    msg.attach(part_inv)

    # Send through Gmail
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print("Email sending FAILED:", e)
        return False


if __name__ == "__main__":
    summary, invoices = collect_data(MODE)

    # Build PDFs
    summary_pdf_raw = make_summary_pdf(summary)
    encrypted_summary = encrypt_pdf(summary_pdf_raw, LOCK_CODE)
    invoice_pdf = make_invoice_pdf(invoices)

    ok = send_email(MODE, encrypted_summary, invoice_pdf)

    if not ok:
        sys.exit(1)

    print("Report done.")
