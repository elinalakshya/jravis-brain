# JRAVIS Phase-1.6 + 1.7 + 1.8 — Secure Reports + Auto Invoice Attachments

import os, smtplib, schedule, time, sqlite3, glob
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime, timedelta
from threading import Thread
from PyPDF2 import PdfReader, PdfWriter

# ---------- CONFIG ----------
EMAIL_USER = os.getenv("EMAIL_USER", "your_email@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "your_app_password")
LOCK_CODE = os.getenv("LOCK_CODE", "2040passcode")
TO_EMAIL = "nrveeresh327@gmail.com"
DB_PATH = "./jravis_core.db"
INVOICE_DIR = "./invoices"


# ---------- PDF CREATION ----------
def create_pdf_summary(file_name, report_type):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("SELECT stream, SUM(amount) FROM income GROUP BY stream;")
        income = cur.fetchall()
    except Exception:
        income = []

    try:
        cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status;")
        tasks = cur.fetchall()
    except Exception:
        tasks = []

    try:
        cur.execute(
            "SELECT ts, level, message FROM logs ORDER BY ts DESC LIMIT 10;")
        logs = cur.fetchall()
    except Exception:
        logs = []

    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"JRAVIS {report_type} Summary Report", ln=True, align="C")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0,
             8,
             f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Income Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    if income:
        for s, a in income:
            pdf.cell(0, 8, f"• {s}: ₹{a:.2f}", ln=True)
    else:
        pdf.cell(0, 8, "No income records found.", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Task Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    if tasks:
        for s, c in tasks:
            pdf.cell(0, 8, f"• {s}: {c}", ln=True)
    else:
        pdf.cell(0, 8, "No task records found.", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Recent Logs", ln=True)
    pdf.set_font("Helvetica", "", 10)
    if logs:
        for ts, level, msg in logs:
            pdf.multi_cell(0, 6, f"[{level}] {msg}")
    else:
        pdf.multi_cell(0, 6, "No logs available.")
    pdf.ln(5)

    temp_file = "temp_" + file_name
    pdf.output(temp_file)

    # 🔒 Encrypt the PDF
    writer = PdfWriter()
    reader = PdfReader(temp_file)
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(LOCK_CODE)

    with open(file_name, "wb") as f:
        writer.write(f)
    os.remove(temp_file)

    print(f"[Report] Created and locked (PyPDF2) {file_name}")
    return file_name


# ---------- INVOICE FINDER ----------
def collect_invoice_files(days=1):
    """Find invoices in ./invoices/YYYY-MM-DD folders"""
    collected = []
    today = datetime.now().date()

    # check today's and yesterday's folder
    for i in range(days):
        date_folder = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        path = os.path.join(INVOICE_DIR, date_folder)
        if os.path.exists(path):
            for f in glob.glob(os.path.join(path, "*.pdf")):
                collected.append(f)
    return collected


# ---------- EMAIL ----------
def send_email_with_attachments(subject, body, file_path, invoices=None):
    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    # Add main summary
    with open(file_path, "rb") as f:
        data = f.read()
        msg.add_attachment(data,
                           maintype="application",
                           subtype="pdf",
                           filename=os.path.basename(file_path))

    # Add invoices if any
    if invoices:
        for inv in invoices:
            try:
                with open(inv, "rb") as f:
                    msg.add_attachment(
                        f.read(),
                        maintype="application",
                        subtype="pdf",
                        filename=os.path.basename(inv),
                    )
                print(f"[Attach] Added invoice: {os.path.basename(inv)}")
            except Exception as e:
                print(f"[Attach] Failed {inv}: {e}")

    # Send via Gmail
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

    print(
        f"[Email] Sent: {subject} ({len(invoices) if invoices else 0} invoices attached)"
    )


# ---------- JOBS ----------
def daily_report():
    # after send_email_with_attachments(...)
    os.system("python report_drive_backup.py &")
    name = datetime.now().strftime("%d-%m-%Y") + "_daily_summary.pdf"
    file_path = create_pdf_summary(name, "Daily")
    invoices = collect_invoice_files(days=1)
    send_email_with_attachments(
        "JRAVIS Daily Report", "Attached is your daily summary and invoices.",
        file_path, invoices)


def weekly_report():
    # after send_email_with_attachments(...)
    os.system("python report_drive_backup.py &")
    name = datetime.now().strftime("%d-%m-%Y") + "_weekly_summary.pdf"
    file_path = create_pdf_summary(name, "Weekly")
    invoices = collect_invoice_files(days=7)
    send_email_with_attachments(
        "JRAVIS Weekly Report",
        "Attached is your weekly summary and invoices.", file_path, invoices)


# ---------- SCHEDULER ----------
schedule.every().day.at("10:00").do(daily_report)
schedule.every().sunday.at("00:00").do(weekly_report)


def scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    print("[JRAVIS Email System] Scheduler active 📨 (Reports + Invoices)")
    Thread(target=scheduler_loop).start()
