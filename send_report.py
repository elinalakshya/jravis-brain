# send_report.py
import smtplib, ssl, os, sqlite3, time
from email.message import EmailMessage
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime, timezone, timedelta
from threading import Timer

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
TO_EMAIL = "nrveeresh327@gamil.com"  # as saved

DB = "approvals.db"
LOCK_CODE = os.getenv("LOCK_CODE", "1234")  # set secure in env


def encrypt_pdf(in_path, out_path, password):
    reader = PdfReader(in_path)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    writer.encrypt(password)
    with open(out_path, "wb") as f:
        writer.write(f)


def send_email_with_approval(summary_pdf_path, invoices_pdf_path, run_id):
    msg = EmailMessage()
    msg["Subject"] = f"{datetime.now().date().isoformat()} summary report"
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL
    # build body with approval link
    approve_link = f"https://your-domain.example/approve?run_id={run_id}"
    body = f"""
Boss — daily summary attached (code-locked).
Click APPROVE to continue: {approve_link}
If no approval in 10 minutes the system will auto-resume.
"""
    msg.set_content(body)
    # attach files
    with open(summary_pdf_path, "rb") as f:
        msg.add_attachment(f.read(),
                           maintype="application",
                           subtype="pdf",
                           filename=os.path.basename(summary_pdf_path))
    with open(invoices_pdf_path, "rb") as f:
        msg.add_attachment(f.read(),
                           maintype="application",
                           subtype="pdf",
                           filename=os.path.basename(invoices_pdf_path))
    # send
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


# Approval DB helpers
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS approvals(run_id TEXT PRIMARY KEY, created_at INTEGER, approved INTEGER DEFAULT 0)"
    )
    conn.commit()
    conn.close()


def create_run(run_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO approvals(run_id, created_at, approved) VALUES (?, ?, 0)",
        (run_id, int(time.time())))
    conn.commit()
    conn.close()


def check_approve_and_proceed(run_id, timeout_seconds=600):
    # Wait loop: check DB every 5s up to timeout; if not approved => return False (auto-resume)
    start = time.time()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    while time.time() - start < timeout_seconds:
        c.execute("SELECT approved FROM approvals WHERE run_id=?", (run_id, ))
        row = c.fetchone()
        if row and row[0] == 1:
            conn.close()
            return True
        time.sleep(5)
    conn.close()
    return False


if __name__ == "__main__":
    init_db()
    run_id = datetime.utcnow().isoformat()
    # example: encrypt summary
    encrypt_pdf("summary_plain.pdf", "summary_locked.pdf", LOCK_CODE)
    create_run(run_id)
    send_email_with_approval("summary_locked.pdf", "invoices.pdf", run_id)
    approved = check_approve_and_proceed(run_id,
                                         timeout_seconds=600)  # 10 minutes
    if approved:
        print("User approved. Proceeding with daily actions.")
    else:
        print("No approval received — auto-resume triggered.")
