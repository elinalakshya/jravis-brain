#!/usr/bin/env python3
"""
JRAVIS Phase-1 Report + Invoice Generator (Cloud)
- Generates summary + invoices PDFs
- Encrypts the summary PDF with a lock code
- Emails both PDFs to REPORT_RECIPIENT via SMTP
Usage:
  python report_invoice_cloud.py --daily
  python report_invoice_cloud.py --weekly
  python report_invoice_cloud.py            # does a quick run (useful for testing)
"""

import os
import io
import sys
import smtplib
import traceback
from datetime import datetime, timedelta
from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter
from tinydb import TinyDB, where
from email.message import EmailMessage
from email.utils import formataddr

# ----------------------------
# Config via environment vars
# ----------------------------
SMTP_SERVER = os.environ.get("SMTP_SERVER")  # e.g. smtp.gmail.com
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")  # SMTP username
SMTP_PASS = os.environ.get("SMTP_PASS")  # SMTP password or app password
REPORT_LOCK_CODE = os.environ.get("REPORT_LOCK_CODE", "1234")
REPORT_RECIPIENT = os.environ.get("REPORT_RECIPIENT", "nrveeresh327@gamil.com")
FROM_NAME = os.environ.get("FROM_NAME", "JRAVIS Bot")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER or "noreply@jravis.local")

DB_PATH = os.environ.get("JR_MEMORY_PATH", "jr_memory.json")
REPORTS_DIR = os.environ.get("REPORTS_DIR", "/tmp/jravis_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


# ----------------------------
# Helpers: PDF creation
# ----------------------------
class SimplePDF:

    def __init__(self, title="JRAVIS Report"):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.title = title

    def add_title(self, text):
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 16)
        self.pdf.cell(0, 10, text, ln=True)
        self.pdf.ln(6)

    def add_paragraph(self, text):
        self.pdf.set_font("Arial", size=11)
        self.pdf.multi_cell(0, 7, text)
        self.pdf.ln(3)

    def save_to_bytes(self):
        buf = io.BytesIO(self.pdf.output(dest="S").encode("latin1"))
        return buf

    def save_to_file(self, path):
        self.pdf.output(path)


# ----------------------------
# Build reports from TinyDB
# ----------------------------
def load_db(path=DB_PATH):
    return TinyDB(path)


def build_daily_summary(db):
    # Collect simple statistics for today (or most recent)
    reports = db.table("reports").all()
    earnings = db.table("earnings").all()

    today = datetime.utcnow().date().isoformat()
    summary = SimplePDF("JRAVIS Daily Summary")
    summary.add_title(f"JRAVIS — Daily Summary ({today})")

    # Example summary content (customize as needed)
    total_earnings = sum(
        e.get("amount", 0) for e in earnings
        if e.get("date", "").startswith(today))
    summary.add_paragraph(f"Date: {today}")
    summary.add_paragraph(
        f"Total reported earnings (today): ₹{total_earnings:,}")
    summary.add_paragraph(f"Number of earnings records: {len(earnings)}")
    summary.add_paragraph("Recent reports:")
    for r in reports[-10:]:
        summary.add_paragraph(
            f"- {r.get('date','?')} — {str(r.get('summary','')).strip()[:100]}"
        )

    # Save files
    fname = os.path.join(REPORTS_DIR, f"daily_summary_{today}.pdf")
    summary.save_to_file(fname)
    return fname


def build_weekly_invoice(db):
    # Build a simple invoices PDF (last 7 days)
    earnings = db.table("earnings").all()
    a_week_ago = (datetime.utcnow() - timedelta(days=7)).date().isoformat()

    invoice = SimplePDF("JRAVIS Weekly Invoices")
    invoice.add_title(
        f"JRAVIS — Weekly Invoice ({a_week_ago} to {datetime.utcnow().date().isoformat()})"
    )

    weekly_earnings = [e for e in earnings if e.get("date", "") >= a_week_ago]
    total = sum(e.get("amount", 0) for e in weekly_earnings)

    invoice.add_paragraph(f"Period start: {a_week_ago}")
    invoice.add_paragraph(f"Total weekly earnings: ₹{total:,}")
    invoice.add_paragraph("Details:")
    for e in weekly_earnings:
        invoice.add_paragraph(
            f"- {e.get('date')} : {e.get('amount')} — {e.get('note','')[:120]}"
        )

    fname = os.path.join(
        REPORTS_DIR,
        f"weekly_invoices_{datetime.utcnow().date().isoformat()}.pdf")
    invoice.save_to_file(fname)
    return fname


# ----------------------------
# PDF encryption
# ----------------------------
def encrypt_pdf(input_path, output_path, password):
    writer = PdfWriter()
    reader = PdfReader(input_path)
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with open(output_path, "wb") as fh:
        writer.write(fh)
    return output_path


# ----------------------------
# Email sending
# ----------------------------
def send_email(subject, body, attachments=None, recipient=REPORT_RECIPIENT):
    if attachments is None:
        attachments = []

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
    msg["To"] = recipient
    msg.set_content(body)

    # attach files
    for path in attachments:
        try:
            with open(path, "rb") as f:
                data = f.read()
            maintype = "application"
            subtype = "pdf"
            msg.add_attachment(data,
                               maintype=maintype,
                               subtype=subtype,
                               filename=os.path.basename(path))
        except Exception as e:
            print("⚠️ Attachment failed:", path, e)

    # send
    if not SMTP_SERVER or not SMTP_USER or not SMTP_PASS:
        raise EnvironmentError(
            "Missing SMTP configuration. Set SMTP_SERVER, SMTP_USER, SMTP_PASS in environment."
        )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as s:
        s.ehlo()
        if SMTP_PORT == 587:
            s.starttls()
            s.ehlo()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    return True


# ----------------------------
# Orchestration
# ----------------------------
def run_daily_flow():
    try:
        db = load_db()
        summary_pdf = build_daily_summary(db)
        encrypted_summary = os.path.splitext(summary_pdf)[0] + "_locked.pdf"
        encrypt_pdf(summary_pdf, encrypted_summary, REPORT_LOCK_CODE)

        invoices_pdf = build_weekly_invoice(
            db)  # reuses weekly builder for attachments
        subject = f"JRAVIS Daily Summary — {datetime.utcnow().date().isoformat()}"
        body = ("JRAVIS Daily Summary attached (locked). "
                "Invoices attached as separate file.\n\n"
                "If you are the Boss, use your lock code to open the summary.")
        send_email(subject,
                   body,
                   attachments=[encrypted_summary, invoices_pdf])
        print("✅ Daily flow complete. Email sent.")

    except Exception:
        print("❌ Daily flow failed:")
        traceback.print_exc()


def run_weekly_flow():
    try:
        db = load_db()
        summary_pdf = build_daily_summary(
            db)  # weekly summary can reuse daily builder or create longer
        encrypted_summary = os.path.splitext(summary_pdf)[0] + "_locked.pdf"
        encrypt_pdf(summary_pdf, encrypted_summary, REPORT_LOCK_CODE)

        invoices_pdf = build_weekly_invoice(db)
        subject = f"JRAVIS Weekly Summary — week ending {datetime.utcnow().date().isoformat()}"
        body = "JRAVIS Weekly Summary attached (locked) and invoices attached."
        send_email(subject,
                   body,
                   attachments=[encrypted_summary, invoices_pdf])
        print("✅ Weekly flow complete. Email sent.")

    except Exception:
        print("❌ Weekly flow failed:")
        traceback.print_exc()


# ----------------------------
# CLI entry
# ----------------------------
def usage_and_exit():
    print("Usage: python report_invoice_cloud.py [--daily|--weekly]")
    sys.exit(1)


if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "--test"

    if arg in ("--daily", "--test"):
        print("Running daily flow (or test) ...")
        run_daily_flow()
    elif arg == "--weekly":
        print("Running weekly flow ...")
        run_weekly_flow()
    else:
        usage_and_exit()
