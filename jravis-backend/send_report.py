import os
import time
import uuid
import threading
import tempfile
from datetime import datetime, timedelta
from typing import Dict

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

LOCK_CODE = os.getenv("LOCK_CODE", "2040")
VA_EMAIL = os.getenv("VA_EMAIL")
VA_EMAIL_PASS = os.getenv("VA_EMAIL_PASS")
RECIPIENT = os.getenv("REPORT_RECIPIENT", "nrveeresh327@gmail.com")

approval_tokens: Dict[str, Dict] = {}
approval_lock = threading.Lock()

def create_pdf(lines, path):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 72
    c.setFont("Helvetica", 12)
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
        if y < 72:
            c.showPage()
            y = height - 72
    c.save()

def encrypt_pdf(src, dest, pwd):
    reader = PdfReader(src)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    writer.encrypt(pwd)
    with open(dest, "wb") as f:
        writer.write(f)

def send_email(subject, html_body, attachments):
    msg = MIMEMultipart()
    msg["From"] = f"JRAVIS BOT <{VA_EMAIL}>"
    msg["To"] = RECIPIENT
    msg["Subject"] = subject

    msg.attach(MIMEText(html_body, "html"))

    for filename, data in attachments.items():
        part = MIMEApplication(data, Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(VA_EMAIL, VA_EMAIL_PASS)
        s.send_message(msg)

def perform_real_tasks(date):
    time.sleep(1)

def orchestrate_daily(date_str):
    with tempfile.TemporaryDirectory() as td:
        plain = f"{td}/summary_plain.pdf"
        encrypted = f"{td}/summary.pdf"
        invoice = f"{td}/invoice.pdf"

        summary_lines = [
            f"Daily Report for {date_str}",
            "Yesterday's tasks: ...",
            "Today's plan: ...",
            "Tomorrow's plan: ...",
            "Total earnings: ₹XXXXX",
        ]

        invoice_lines = [
            "Invoice Details",
            "Amount: ₹XXXX",
            f"Date: {date_str}"
        ]

        create_pdf(summary_lines, plain)
        create_pdf(invoice_lines, invoice)
        encrypt_pdf(plain, encrypted, LOCK_CODE)

        with open(encrypted, "rb") as f:
            summary_bytes = f.read()
        with open(invoice, "rb") as f:
            invoice_bytes = f.read()

        token = str(uuid.uuid4())
        link = f"{os.getenv('BASE_URL','https://jravis-backend.onrender.com')}/api/approve?token={token}"

        with approval_lock:
            approval_tokens[token] = {
                "approved": False,
                "expiry": datetime.utcnow() + timedelta(minutes=10)
            }

        body = f"""
        <p>Boss, here is your daily report ({date_str}).</p>
        <p><a href="{link}" style="padding:8px 14px;background:#007bff;color:#fff;text-decoration:none;border-radius:6px;">Approve Now</a></p>
        """

        send_email(f"JRAVIS Daily Report — {date_str}", body, {
            f"{date_str} summary.pdf": summary_bytes,
            f"{date_str} invoice.pdf": invoice_bytes
        })

        waited = 0
        approved = False
        while waited < 600:
            with approval_lock:
                if approval_tokens[token]["approved"]:
                    approved = True
                    break
            time.sleep(3)
            waited += 3

        perform_real_tasks(date_str)

        with approval_lock:
            approval_tokens.pop(token, None)

def orchestrate_weekly():
    body = "Weekly report sent"
    send_email("JRAVIS Weekly Report", body, {})
