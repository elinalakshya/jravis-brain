# ============================================================
# JRAVIS Backend – Daily & Weekly Report Automation (FastAPI)
# ============================================================

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import os, logging, tempfile, threading, time, uuid, smtplib, schedule, requests
from datetime import datetime, timedelta
from typing import Dict
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ------------------------------------------------------------
# App & global setup
# ------------------------------------------------------------
app = FastAPI(title="JRAVIS Backend – Reports Service")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

# Environment variables
ADMIN_CODE = os.getenv("REPORT_API_CODE", "2040")
VA_EMAIL = os.getenv("VA_EMAIL")
VA_EMAIL_PASS = os.getenv("VA_EMAIL_PASS")
LOCK_CODE = os.getenv("LOCK_CODE", "2040")
RECIPIENT = os.getenv("REPORT_RECIPIENT", "nrveeresh327@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "Dhruvayu - VA BOT")
BASE_URL = os.getenv("BASE_URL", "https://jravis-backend.onrender.com")

# Token store for approvals
approval_tokens: Dict[str, Dict] = {}
approval_lock = threading.Lock()


# ------------------------------------------------------------
# PDF helpers
# ------------------------------------------------------------
def create_pdf(title: str, lines: list, out_path: str):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4
    y = h - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, title)
    y -= 28
    c.setFont("Helvetica", 10)
    for line in lines:
        c.drawString(72, y, line)
        y -= 14
        if y < 72:
            c.showPage()
            y = h - 72
    c.showPage()
    c.save()


def encrypt_pdf(src: str, dst: str, password: str):
    reader = PdfReader(src)
    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)
    writer.encrypt(user_pwd=password, owner_pwd=None, use_128bit=True)
    with open(dst, "wb") as f:
        writer.write(f)


# ------------------------------------------------------------
# Email helper
# ------------------------------------------------------------
def send_email(subject: str, html_body: str, attachments: Dict[str, bytes]):
    if not VA_EMAIL or not VA_EMAIL_PASS:
        raise RuntimeError("Missing VA_EMAIL or VA_EMAIL_PASS in environment")
    msg = MIMEMultipart()
    msg["From"] = f"{FROM_NAME} <{VA_EMAIL}>"
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    for name, data in attachments.items():
        part = MIMEApplication(data, Name=name)
        part["Content-Disposition"] = f'attachment; filename="{name}"'
        msg.attach(part)
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(VA_EMAIL, VA_EMAIL_PASS)
        s.send_message(msg)
    logging.info("📧 Email sent successfully")


# ------------------------------------------------------------
# Core business action
# ------------------------------------------------------------
def perform_daily_tasks(tag: str):
    logging.info(f"Running JRAVIS tasks for {tag} ...")
    time.sleep(1)
    logging.info("JRAVIS tasks completed ✅")


# ------------------------------------------------------------
# Orchestrator (daily / weekly)
# ------------------------------------------------------------
def orchestrate_report(mode: str, report_date: datetime):
    label = report_date.strftime("%d-%m-%Y")
    week_label = report_date.strftime("Week-%W %Y")
    tag = week_label if mode == "weekly" else label
    logging.info(f"🌀 Starting {mode.upper()} report for {tag}")

    with tempfile.TemporaryDirectory() as td:
        s_plain = os.path.join(td, f"{mode}_summary.pdf")
        s_enc = os.path.join(td, f"{mode}_summary_enc.pdf")
        inv_path = os.path.join(td, f"{mode}_invoice.pdf")

        # placeholder lines – replace later with live JRAVIS data
        summary_lines = [
            f"{mode.capitalize()} Summary — {tag}",
            "-------------------------------------------",
            "1) Completed tasks: ...", "2) Earnings: ₹XXXXX",
            "3) Pending / issues: ...", "4) Next goals: ...", "",
            "Summary is encrypted with your lock code."
        ]
        invoice_lines = [
            f"{mode.capitalize()} Invoice — {tag}",
            "-------------------------------------------", "Details...",
            "Total: ₹XXXXX"
        ]

        create_pdf(f"JRAVIS {mode.capitalize()} Summary", summary_lines,
                   s_plain)
        create_pdf(f"JRAVIS {mode.capitalize()} Invoice", invoice_lines,
                   inv_path)
        encrypt_pdf(s_plain, s_enc, LOCK_CODE)

        with open(s_enc, "rb") as f:
            s_bytes = f.read()
        with open(inv_path, "rb") as f:
            inv_bytes = f.read()

        token = str(uuid.uuid4())
        approve_link = f"{BASE_URL}/api/approve?token={token}"
        with approval_lock:
            approval_tokens[token] = {
                "approved": False,
                "expiry": datetime.utcnow() + timedelta(minutes=10)
            }

        subj = f"✅ JRAVIS {mode.capitalize()} Report — {tag}"
        body = f"""
        <p>Boss, here’s your {mode} JRAVIS report ({tag}).</p>
        <p><b>Summary:</b> Encrypted with your lock code.<br>
           <b>Invoice:</b> Attached (no lock).</p>
        <p><a href="{approve_link}" style="padding:10px 16px;
           background:#0b74de;color:#fff;text-decoration:none;border-radius:6px;">Approve Now</a></p>
        <p>If no approval in 10 minutes, VA BOT will auto-resume work.</p>
        """

        attachments = {
            f"{tag} summary.pdf": s_bytes,
            f"{tag} invoices.pdf": inv_bytes
        }
        try:
            send_email(subj, body, attachments)
        except Exception as e:
            logging.error(f"Email failed: {e}")

        waited, approved = 0, False
        while waited < 600:
            with approval_lock:
                if approval_tokens.get(token, {}).get("approved"):
                    approved = True
                    break
            time.sleep(3)
            waited += 3

        if approved: logging.info(f"{mode.title()} report approved.")
        else: logging.info(f"{mode.title()} auto-resumed (no approval).")
        perform_daily_tasks(tag)
        with approval_lock:
            approval_tokens.pop(token, None)


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.get("/")
def home():
    return {"status": "JRAVIS backend is live ✅"}


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/api/send_daily_report")
def send_daily_report(code: str = Query(...)):
    if code != ADMIN_CODE:
        raise HTTPException(status_code=401, detail="Invalid code")
    threading.Thread(target=orchestrate_report,
                     args=("daily", datetime.now()),
                     daemon=True).start()
    return JSONResponse({
        "detail": "Daily report orchestrator started",
        "date": datetime.now().strftime("%d-%m-%Y")
    })


@app.get("/api/approve")
def approve(token: str = Query(...)):
    with approval_lock:
        t = approval_tokens.get(token)
        if not t:
            return JSONResponse({"detail": "Invalid or expired token."},
                                status_code=404)
        t["approved"] = True
    return JSONResponse({"detail": "Approval recorded. VA BOT will proceed."})


# ------------------------------------------------------------
# Scheduler – daily & weekly
# ------------------------------------------------------------
def trigger_daily():
    orchestrate_report("daily", datetime.now())


def trigger_weekly():
    orchestrate_report("weekly", datetime.now())


schedule.every().day.at("10:00").do(trigger_daily)
schedule.every().sunday.at("00:00").do(trigger_weekly)


def scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(60)


threading.Thread(target=scheduler_loop, daemon=True).start()
# ------------------------------------------------------------
# End of file
# ------------------------------------------------------------
