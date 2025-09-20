import os, ssl, smtplib, traceback, threading, time, urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from flask import Flask, jsonify
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from DailyReport import phase1

IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")

from pathlib import Path
STATE_FILE = Path("DailyReport/.last_sent.txt")

def _today_str():
    return datetime.now(IST).strftime("%Y-%m-%d")

def sent_today():
    try:
        return STATE_FILE.read_text().strip() == _today_str()
    except FileNotFoundError:
        return False

def mark_sent_today():
    STATE_FILE.write_text(_today_str())


FROM_EMAIL = os.getenv("EMAIL")
APP_PASS = os.getenv("APP_PASS")
TO_EMAIL = "nrveeresh327@gmail.com"


def log(msg):
    print(
        f"[VA BOT] {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')} | {msg}"
    )


if not FROM_EMAIL or not APP_PASS:
    raise SystemExit(
        "❌ EMAIL or APP_PASS missing. Set Replit Secrets (EMAIL, APP_PASS) and press Run again."
    )


def build_files():
    today = datetime.now(IST).strftime("%d-%m-%Y")
    return [
        (f"{today} summary report.pdf", f"{today} summary report.pdf"),
        (f"{today} invoices.pdf", f"{today} invoices.pdf"),
    ]


def attach_file(msg, path, filename):
    p = Path(path)
    if not p.exists() or p.stat().st_size < 1024:
        msg.attach(
            MIMEText(f"⚠️ Skipped attachment: {filename} (missing/too small)",
                     "plain"))
        log(f"⚠️ Skipped attachment: {filename}")
        return
    with open(p, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition",
                    f'attachment; filename="{filename}"')
    msg.attach(part)


def send_email_now():
    try:
        html = f"<p>Boss, daily report for {datetime.now(IST).strftime('%d-%m-%Y')} ✅</p>" + "<p><b>Phase 1:</b><br>" + (run_phase1_now()[2] if False else "Will run at 10:05 AM IST") + "</p>"
        files = build_files()
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = TO_EMAIL
        msg["Subject"] = "VA Bot — Daily Report (Auto)"
        msg.attach(MIMEText(html, "html"))
        for p, n in files:
            attach_file(msg, p, n)
        with smtplib.SMTP_SSL("smtp.gmail.com",
                              465,
                              context=ssl.create_default_context()) as s:
            s.login(FROM_EMAIL, APP_PASS)
            s.sendmail(FROM_EMAIL, [TO_EMAIL], msg.as_string())
        log(f"📧 Sent to {TO_EMAIL}")
        mark_sent_today()
        return True, "sent"
    except Exception:
        log("❌ Send failed:\n" + traceback.format_exc())
        return False, "failed"


app = Flask(__name__)


@app.get("/")
def home():
    ist_now = datetime.now(IST).strftime("%d-%m-%Y %I:%M:%S %p IST")
    utc_now = datetime.now(UTC).strftime("%d-%m-%Y %H:%M:%S UTC")
    return f"""<h1>VA Bot is running ✅</h1>
    <p>IST scheduler: 10:00 AM daily</p>
    <ul>
      <li><a href="/health">/health</a> — status & time</li>
      <li><a href="/send-now">/send-now</a> — send email instantly</li>
      <li><a href="/time">/time</a> — date & time JSON</li>
    </ul>
    <p><b>Date & Time (IST):</b> {ist_now}</p>
    <p><b>Date & Time (UTC):</b> {utc_now}</p>
    """


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "ist_now": datetime.now(IST).isoformat(),
        "utc_now": datetime.now(UTC).isoformat()
    })


@app.get("/time")
def get_time():
    return {
        "ist_now": datetime.now(IST).strftime("%d-%m-%Y %I:%M:%S %p IST"),
        "utc_now": datetime.now(UTC).strftime("%d-%m-%Y %H:%M:%S UTC")
    }


@app.get("/send-now")
def send_now():
    ok, msg = send_email_now()
    return (jsonify({"ok": ok, "msg": msg}), 200 if ok else 500)


# ---- Scheduler: daily 10:00 IST ----
scheduler = BackgroundScheduler(timezone=IST)
scheduler.add_job(send_email_now, CronTrigger(hour=10, minute=0))
scheduler.add_job(lambda: run_phase1_now(), CronTrigger(hour=10, minute=5))  # phase1 at 10:05
scheduler.start()
log("Scheduler started (daily 10:00 AM IST).")


# ---- Self-ping every 10 minutes to stay awake ----
def self_ping(port):
    while True:
        try:
            url = f"http://127.0.0.1:{port}/health"
            with urllib.request.urlopen(url) as r:
                log(f"🔄 Self-ping OK {r.status}")
        except Exception as e:
            log(f"⚠️ Self-ping failed: {e}")
        time.sleep(600)


if __name__ == "__main__":
    import socket
    # Try to use PORT from Replit, else pick a free port automatically
    port = int(os.getenv("PORT", "8000"))
    try:
        # check if port is available
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                log(f"⚠️ Port {port} in use, switching to auto free port.")
                port = 0  # OS picks a free one
    except Exception as e:
        log(f"Port check failed: {e}, falling back to 8000")

    threading.Thread(target=self_ping, args=(port,), daemon=True).start()
    log(f"IST now: {datetime.now(IST)} | UTC now: {datetime.now(UTC)}")
    log(f"Serving Flask on port {port}. Health: /health  |  Manual: /send-now")
    app.run(host="0.0.0.0", port=port)

def run_phase1_now():
    log("⚙️ Phase 1: starting real-work batch now…")
    try:
        results = phase1.run_all()
        # Build a short HTML summary to include in emails
        lines = [f"- {r.get('task')}: {r.get('status')} — {r.get('details')} ({r.get('at')})" for r in results]
        summary_html = "<br>".join(lines)
        log("✅ Phase 1 batch completed.")
        return True, results, summary_html
    except Exception as e:
        log(f"❌ Phase 1 batch failed: {e}")
        return False, [], f"Phase 1 failed: {e}"

@app.get("/phase1/start-now")
def phase1_start_now():
    ok, results, html = run_phase1_now()
    from flask import jsonify
    return (jsonify({"ok": ok, "results": results}), 200 if ok else 500)
