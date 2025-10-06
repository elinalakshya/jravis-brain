#!/usr/bin/env python3
"""
JRAVIS Brain — Render-ready full brain (Mission 2040)
Features:
- 30 streams across 3 phases (min/max income)
- Auto-generation of simple stream connectors (streams/*.py) if missing
- Stream runner (simulated earnings) with self-heal/regen
- Scheduler: auto-phase activation, daily @10:00 IST, weekly Sun 00:00 IST
- PDF report generation (optional if fpdf & PyPDF2 installed)
- Email sending (optional, via env VA_EMAIL & VA_EMAIL_PASS)
- Chat endpoint: OpenAI-driven if OPENAI_API_KEY set; rule-based fallback otherwise
- Gmail auto-reply (optional, via VA_EMAIL creds)
- Dashboard HTML (simple, live)
- Heartbeat logging every minute
- Watchdog thread to check /health
- If psutil available, try to kill prior same-process instances on startup
- Auto-restart loop around Flask.run to attempt self-restart (Render will also restart)
"""

import os
import sys
import time
import json
import glob
import shutil
import logging
import threading
import schedule
import smtplib
import importlib.util
from datetime import datetime, timedelta, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string, abort

# Optional libs (import if installed)
try:
    import psutil
except Exception:
    psutil = None

try:
    import openai
except Exception:
    openai = None

# PDF libs (optional)
try:
    from fpdf import FPDF
    from PyPDF2 import PdfReader, PdfWriter
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

# -----------------------
# CONFIG (via ENV)
# -----------------------
PORT = int(os.environ.get("PORT", 8080))
SECRET_KEY = os.environ.get("JARVIS_SECRET", "MY OG")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")  # optional
VA_EMAIL = os.environ.get("VA_EMAIL", "")
VA_EMAIL_PASS = os.environ.get("VA_EMAIL_PASS", "")
INVOICE_EMAIL = os.environ.get("INVOICE_EMAIL", VA_EMAIL)
PDF_PASS = os.environ.get("PDF_PASS", "MY OG")  # passcode for PDF if used
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "60"))  # seconds
GMAIL_POLL_MIN = int(os.environ.get("GMAIL_POLL_MIN", "10"))  # minutes

if openai and OPENAI_KEY:
    openai.api_key = OPENAI_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)

# -----------------------
# PHASES & STREAMS (30 streams)
# -----------------------
PHASES = {
    "Phase 1": {
        "year": 2025,
        "description": "Fast Kickstart — immediate execution, fastest scaling, early cash inflow",
        "target_by": "Dec 2025",
        "start_date": date(2025, 1, 1),
        "streams": [
            ("Elina Instagram Reels", 15000, 50000),
            ("Printify POD Store", 20000, 200000),
            ("Meshy AI Store", 10000, 75000),
            ("Cad Crowd Auto Work", 30000, 120000),
            ("Fiverr AI Gig Automation", 25000, 150000),
            ("YouTube Automation", 50000, 200000),
            ("Stock Image/Video Sales", 20000, 80000),
            ("AI Book Publishing (KDP)", 30000, 150000),
            ("Shopify Digital Products", 50000, 250000),
            ("Stationery Export (Lakshya Passive Stationery)", 50000, 200000),
        ],
    },
    "Phase 2": {
        "year": 2026,
        "description": "Scaling & Medium Systems",
        "target_by": "Dec 2026",
        "start_date": date(2026, 1, 1),
        "streams": [
            ("Template/Theme Marketplace", 40000, 200000),
            ("Course Resell Automation", 50000, 200000),
            ("Printables Store (Etsy/Creative Market)", 25000, 80000),
            ("Affiliate Marketing Automation", 50000, 250000),
            ("AI SaaS Micro-Tools", 50000, 300000),
            ("Newsletter + Ads Automation", 30000, 100000),
            ("Subscription Box (Stationery/Digital)", 40000, 150000),
            ("Gaming Assets Store", 30000, 120000),
            ("Webflow Template Sales", 25000, 75000),
            ("Skillshare Course Automation", 25000, 80000),
        ],
    },
    "Phase 3": {
        "year": 2027,
        "description": "Advanced Passive Engines",
        "target_by": "2027",
        "start_date": date(2027, 1, 1),
        "streams": [
            ("SaaS Reseller Bots", 75000, 300000),
            ("Voiceover/AI Dubbing Automation", 30000, 100000),
            ("Music/Beats Licensing", 30000, 100000),
            ("Web Automation Scripts Marketplace", 40000, 150000),
            ("AI Plugin/Extension Sales", 50000, 250000),
            ("Educational Worksheets Store", 25000, 100000),
            ("Digital/Virtual Events Automation", 50000, 200000),
            ("AI Resume/CV Automation", 25000, 100000),
            ("Crypto Microtask Automation (Legal Only)", 20000, 80000),
            ("Global API Marketplace", 75000, 300000),
        ],
    },
}

# runtime state
PHASE_STATE = {
    name: {
        "state": "Pending" if date.today() < meta["start_date"] else "Active",
        "started_on": None if date.today() < meta["start_date"] else str(date.today()),
    }
    for name, meta in PHASES.items()
}

# where stream connectors live
STREAMS_DIR = Path("streams")
STREAMS_DIR.mkdir(exist_ok=True)

# persistent status files
GMAIL_STATUS_FILE = Path("gmail_status.json")
EARNINGS_HISTORY_FILE = Path("earnings_history.json")

# initialize history file if absent
if not EARNINGS_HISTORY_FILE.exists():
    EARNINGS_HISTORY_FILE.write_text(json.dumps({"history": []}, indent=2))

# -----------------------
# HELPERS: projections, connectors, stream runner
# -----------------------
def phase_income_projection(phase_name):
    if phase_name not in PHASES: return (0, 0, [])
    streams = PHASES[phase_name]["streams"]
    mn = sum(s[1] for s in streams)
    mx = sum(s[2] for s in streams)
    details = [{"name": s[0], "min": s[1], "max": s[2]} for s in streams]
    return mn, mx, details

def all_phases_projection():
    totals = {"min": 0, "max": 0, "per_phase": {}}
    for pname in PHASES:
        mn, mx, _ = phase_income_projection(pname)
        totals["per_phase"][pname] = {"min": mn, "max": mx}
        totals["min"] += mn
        totals["max"] += mx
    return totals

def sanitize_name(name):
    return "".join(c if c.isalnum() else "_" for c in name).lower()

def ensure_stream_connectors():
    """Auto-generate minimal connector file for each stream if missing"""
    for pname, pdata in PHASES.items():
        for s in pdata["streams"]:
            slug = sanitize_name(s[0])
            fpath = STREAMS_DIR / f"{slug}.py"
            if not fpath.exists():
                content = f'''"""
Auto-generated connector for stream: {s[0]}
This is a minimal template — replace with real API code and API keys.
"""
import random
def fetch_earnings():
    # simulate an earnings value between min and max
    return random.randint({s[1]}, {s[2]})
'''
                fpath.write_text(content)
                logging.info("Autogenerated connector: %s", fpath)

def run_streams_once():
    """Run all stream connectors, return aggregated earnings and per-stream values"""
    ensure_stream_connectors()
    total = 0
    details = []
    for pname, pdata in PHASES.items():
        for s in pdata["streams"]:
            slug = sanitize_name(s[0])
            fpath = STREAMS_DIR / f"{slug}.py"
            val = None
            try:
                spec = importlib.util.spec_from_file_location(slug, str(fpath))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "fetch_earnings"):
                    val = int(mod.fetch_earnings())
                else:
                    # fallback simulated
                    val = int((s[1] + s[2]) / 2)
                details.append({"stream": s[0], "earned": val})
                total += val
            except Exception as e:
                logging.warning("Stream %s failed: %s — attempting to regen connector", s[0], e)
                # regen simple connector and continue
                if fpath.exists():
                    try:
                        fpath.unlink()
                    except Exception:
                        pass
                ensure_stream_connectors()
                # after regen, try a simple simulated value
                val = int((s[1] + s[2]) / 2)
                details.append({"stream": s[0], "earned": val, "note": "regenerated"})
                total += val
    # persist to earnings history
    try:
        j = json.loads(EARNINGS_HISTORY_FILE.read_text())
    except Exception:
        j = {"history": []}
    j["history"].append({"time": datetime.utcnow().isoformat(), "total": total, "details": details})
    EARNINGS_HISTORY_FILE.write_text(json.dumps(j, indent=2))
    return total, details

# -----------------------
# EMAIL helpers
# -----------------------
def send_internal_email(subject, body, attachments=None):
    if not VA_EMAIL or not VA_EMAIL_PASS:
        logging.warning("Email not sent (missing VA_EMAIL / VA_EMAIL_PASS)")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = VA_EMAIL
        msg["To"] = INVOICE_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        if attachments:
            for p in attachments:
                try:
                    with open(p, "rb") as fh:
                        part = MIMEApplication(fh.read(), Name=os.path.basename(p))
                    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(p)}"'
                    msg.attach(part)
                except Exception as e:
                    logging.warning("attach error %s: %s", p, e)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
            s.login(VA_EMAIL, VA_EMAIL_PASS)
            s.sendmail(VA_EMAIL, [INVOICE_EMAIL], msg.as_string())
        logging.info("✉️ Email sent: %s", subject)
        return True
    except Exception as e:
        logging.error("Email send failed: %s", e)
        return False

# -----------------------
# PDF report helpers (optional)
# -----------------------
def generate_pdf_summary(total, details, outpath="DailySummary.pdf", passcode=PDF_PASS):
    if not PDF_AVAILABLE:
        logging.warning("PDF libs not available")
        return None
    # Simple PDF using fpdf
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "JRAVIS Daily Summary", ln=True)
        pdf.cell(0, 8, f"Generated: {datetime.utcnow().isoformat()}", ln=True)
        pdf.cell(0, 8, f"Total earnings (simulated): ₹{total}", ln=True)
        pdf.ln(4)
        for d in details[:100]:
            pdf.multi_cell(0, 6, f"{d['stream']}: ₹{d['earned']}")
        pdf.output(outpath)
        # Optionally encrypt with PyPDF2
        try:
            reader = PdfReader(outpath)
            writer = PdfWriter()
            for p in reader.pages:
                writer.add_page(p)
            writer.encrypt(passcode)
            with open(outpath, "wb") as fh:
                writer.write(fh)
        except Exception:
            # if encryption not available, fine
            pass
        return outpath
    except Exception as e:
        logging.error("PDF generation failed: %s", e)
        return None

# -----------------------
# GMAIL auto-reply (optional)
# -----------------------
def gmail_autoreply_once():
    """Check inbox (UNSEEN) and reply with a canned message. Requires VA_EMAIL & VA_EMAIL_PASS."""
    try:
        import imaplib, email
    except Exception:
        logging.warning("imaplib/email libs missing")
        return {"status": "imap_missing"}

    if not VA_EMAIL or not VA_EMAIL_PASS:
        logging.warning("Gmail creds not set")
        return {"status": "no_creds"}

    replied = []
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(VA_EMAIL, VA_EMAIL_PASS)
        imap.select("inbox")
        typ, data = imap.search(None, '(UNSEEN)')
        if typ != "OK":
            imap.logout()
            return {"status": "search_failed"}
        mail_ids = data[0].split()
        for mid in mail_ids:
            typ, msg_data = imap.fetch(mid, "(RFC822)")
            if typ != "OK":
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            sender = email.utils.parseaddr(msg["From"])[1]
            subject = msg.get("Subject", "")
            # send reply
            reply_text = ("Hello — this is an automated JRAVIS reply. "
                          "Your message has been received. Boss will review and respond.")
            m = MIMEText(reply_text)
            m["From"] = VA_EMAIL
            m["To"] = sender
            m["Subject"] = "Re: " + subject if subject else "Re: your message"
            try:
                srv = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
                srv.login(VA_EMAIL, VA_EMAIL_PASS)
                srv.sendmail(VA_EMAIL, [sender], m.as_string())
                srv.quit()
                replied.append(sender)
            except Exception as e:
                logging.warning("Failed to send reply to %s: %s", sender, e)
        imap.logout()
    except Exception as e:
        logging.error("Gmail check failed: %s", e)
        return {"status": "error", "error": str(e)}
    # store status
    st = {"last_check": datetime.utcnow().isoformat(), "last_replied": replied}
    try:
        GMAIL_STATUS_FILE.write_text(json.dumps(st))
    except Exception:
        pass
    return st

# -----------------------
# ROUTES: Dashboard + API + Chat + Streams + Reports
# -----------------------
HOME_HTML = """\
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>JRAVIS Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body{background:#020d1f;color:#e6f0ff;font-family:Inter,system-ui;padding:18px;}
    .progress>span{display:block;height:100%%;background:linear-gradient(90deg,#32d583,#2ab7ff)}
    button{background:#206db0;color:#fff;border:none;padding:8px 12px;border-radius:8px;cursor:pointer;}
  </style>
</head>
<body>
  <h1>🧠 JRAVIS — Dhruvayu (Mission 2040)</h1>
  <div id="messages"></div>
  <input id="chatInput" placeholder="Ask JRAVIS..." />
  <button onclick="sendChat()">Send</button>
  <script>
    async function sendChat(){
      const msg=document.getElementById('chatInput').value;
      const r=await fetch('/chat?msg='+encodeURIComponent(msg));
      const j=await r.json();
      const m=document.getElementById('messages');
      m.innerHTML+='<div>'+msg+'</div><div>'+j.reply+'</div>';
    }
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "phases": PHASE_STATE
    })

@app.route("/projections")
def projections_route():
    key = request.args.get("key", "")
    if key != SECRET_KEY:
        abort(403)
    return jsonify(all_phases_projection())

@app.route("/phases")
def phases_route():
    key = request.args.get("key", "")
    if key != SECRET_KEY:
        abort(403)
    out = {}
    for pname, pdata in PHASES.items():
        mn, mx, details = phase_income_projection(pname)
        out[pname] = {"state": PHASE_STATE[pname]["state"], "start_date": str(pdata["start_date"]), "monthly_min": mn, "monthly_max": mx, "streams": details}
    return jsonify(out)

@app.route("/streams-run", methods=["POST"])
def streams_run():
    key = request.args.get("key", "")
    if key != SECRET_KEY:
        abort(403)
    total, details = run_streams_once()
    return jsonify({"total": total, "details": details})

@app.route("/latest-earnings")
def latest_earnings():
    try:
        j = json.loads(EARNINGS_HISTORY_FILE.read_text())
        return jsonify(j["history"][-6:])
    except Exception:
        return jsonify([])

@app.route("/generate-report", methods=["POST"])
def generate_report():
    key = request.args.get("key", "")
    if key != SECRET_KEY:
        abort(403)
    total, details = run_streams_once()
    pdf = generate_pdf_summary(total, details, outpath="DailySummary.pdf")
    if pdf:
        send_internal_email("JRAVIS Daily Summary", f"Attached summary (total ₹{total})", attachments=[pdf])
        return jsonify({"ok": True, "file": pdf})
    else:
        return jsonify({"ok": False, "msg": "pdf not available, but report data generated", "total": total, "details": details})

@app.route("/chat")
def chat_route():
    msg = request.args.get("msg", "").strip()
    if not msg:
        return jsonify({"reply": "Say something, Boss."})
    low = msg.lower()
    # OpenAI-driven if available
    if openai and OPENAI_KEY:
        try:
            res = openai.ChatCompletion.create(
                model="gpt-4o-mini" if hasattr(openai, "ChatCompletion") else "gpt-3.5-turbo",
                messages=[{"role":"system","content":"You are JRAVIS, an assistant for the Boss."},{"role":"user","content": msg}],
                max_tokens=500,
            )
            # support different library responses
            if isinstance(res, dict) and "choices" in res and len(res["choices"])>0:
                txt = res["choices"][0]["message"]["content"]
            else:
                txt = getattr(res.choices[0].message, "content", str(res))
            return jsonify({"reply": txt})
        except Exception as e:
            logging.warning("OpenAI call failed: %s", e)
    # rule-based fallback
    if "when" in low and "phase" in low:
        for pname in PHASES:
            if pname.lower() in low:
                return jsonify({"reply": f"{pname} starts on {PHASES[pname]['start_date']} (state: {PHASE_STATE[pname]['state']})."})
        lines = [f"{p}: {PHASES[p]['start_date']} ({PHASE_STATE[p]['state']})" for p in PHASES]
        return jsonify({"reply": "Phase schedule:\n" + "\n".join(lines)})
    if "income" in low or "projection" in low or "potential" in low:
        proj = all_phases_projection()
        lines = []
        for p, vals in proj["per_phase"].items():
            lines.append(f"{p}: ₹{vals['min']:,} — ₹{vals['max']:,} /month")
        lines.append(f"TOTAL: ₹{proj['min']:,} — ₹{proj['max']:,} /month")
        return jsonify({"reply": "\n".join(lines)})
    # run streams intent
    if "run streams" in low or "capture" in low:
        total, details = run_streams_once()
        return jsonify({"reply": f"Ran streams. Total (simulated): ₹{total}"})
    return jsonify({"reply": "JRAVIS online and waiting, Boss."})

@app.route("/gmail-status")
def gmail_status():
    if GMAIL_STATUS_FILE.exists():
        try:
            return jsonify(json.loads(GMAIL_STATUS_FILE.read_text()))
        except Exception:
            pass
    return jsonify({"last_check": None, "last_replied": []})

@app.route("/gmail-check", methods=["POST"])
def gmail_check_endpoint():
    key = request.args.get("key", "")
    if key != SECRET_KEY:
        abort(403)
    return jsonify(gmail_autoreply_once())

# -----------------------
# SCHEDULER: phase auto-start + daily/weekly jobs + gmail polling
# -----------------------
def check_and_start_phases():
    today = date.today()
    for pname, pdata in PHASES.items():
        if PHASE_STATE[pname]["state"] == "Pending" and today >= pdata["start_date"]:
            PHASE_STATE[pname]["state"] = "Active"
            PHASE_STATE[pname]["started_on"] = str(today)
            msg = f"Auto-started {pname} on {today} — starting streams: {len(pdata['streams'])}"
            logging.info(msg)
            try:
                send_internal_email(f"JRAVIS: {pname} auto-started", msg)
            except Exception:
                pass

# schedule: heartbeat (every HEARTBEAT_INTERVAL sec is handled separately), phase check, daily & weekly emails, gmail poll
schedule.every(30).minutes.do(check_and_start_phases)
# Daily at 04:30 UTC ~ 10:00 IST (adjust as needed)
schedule.every().day.at("04:30").do(lambda: run_daily_job())
# Weekly (Sunday at 18:30 UTC ~ Sunday 00:00 IST)
schedule.every().saturday.at("18:30").do(lambda: run_weekly_job())
# Gmail polling
schedule.every(GMAIL_POLL_MIN).minutes.do(gmail_autoreply_once)

# helper jobs (defined after scheduler)
def run_daily_job():
    logging.info("Running daily job: generating report and sending email")
    total, details = run_streams_once()
    pdf = generate_pdf_summary(total, details, outpath=f"daily_{datetime.utcnow().strftime('%Y%m%d')}.pdf")
    body = f"JRAVIS Daily Snapshot — total (simulated): ₹{total}"
    try:
        if pdf:
            send_internal_email("JRAVIS Daily Snapshot", body, attachments=[pdf])
        else:
            send_internal_email("JRAVIS Daily Snapshot", body)
    except Exception as e:
        logging.warning("Daily email failed: %s", e)

def gather_week_files():
    files = []
    # include last 7 daily pdfs if present
    for i in range(1, 8):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y%m%d")
        fn = f"daily_{d}.pdf"
        if Path(fn).exists():
            files.append(fn)
    return files

def run_weekly_job():
    logging.info("Running weekly job: bundle and send")
    files = gather_week_files()
    body = f"JRAVIS Weekly bundle — {datetime.utcnow().strftime('%d %b %Y')}\nAttached {len(files)} files."
    try:
        send_internal_email("JRAVIS Weekly", body, attachments=files)
    except Exception as e:
        logging.warning("Weekly email error: %s", e)

# scheduler loop thread
def scheduler_loop():
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logging.error("Scheduler error: %s", e)
        time.sleep(10)

threading.Thread(target=scheduler_loop, daemon=True).start()

# -----------------------
# Heartbeat & Watchdog
# -----------------------
def heartbeat():
    logging.info("💓 JRAVIS alive at %s", datetime.utcnow().isoformat())

def heartbeat_loop():
    while True:
        heartbeat()
        time.sleep(HEARTBEAT_INTERVAL)

threading.Thread(target=heartbeat_loop, daemon=True).start()

def watchdog_loop():
    # periodically check /health and log; if repeatedly failing, rely on platform to restart
    fail_count = 0
    while True:
        try:
            import requests
            r = requests.get(f"http://127.0.0.1:{PORT}/health", timeout=5)
            if r.status_code != 200:
                fail_count += 1
                logging.warning("Watchdog: /health returned %s", r.status_code)
            else:
                fail_count = 0
        except Exception as e:
            fail_count += 1
            logging.warning("Watchdog: request failed: %s", e)
        # If many consecutive failures, log and continue; platforms like Render will restart container
        if fail_count >= 12:
            logging.error("Watchdog: persistent failures detected; waiting for platform to restart")
            fail_count = 0
        time.sleep(60)

threading.Thread(target=watchdog_loop, daemon=True).start()

import schedule, smtplib, threading, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_daily_email():
    sender = os.getenv("VA_EMAIL")
    password = os.getenv("VA_EMAIL_PASS")
    receiver = "nrveeresh327@gmail.com"
    subject = "✅ VA BOT Daily Report"
    body = "Boss, VA BOT has completed today’s scheduled tasks successfully."
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        logging.info("📧 Daily report email sent successfully.")
    except Exception as e:
        logging.error(f"❌ Failed to send email: {e}")

# Run every day at 10:00 AM IST
schedule.every().day.at("10:00").do(send_daily_email)

def scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(60)
threading.Thread(target=scheduler_loop, daemon=True).start()

# -----------------------
# Auto-kill old same-name processes (if psutil available)
# -----------------------
def free_port_kill(port):
    if not psutil:
        logging.info("psutil not available; skipping free_port_kill")
        return
    logging.info("Attempting to kill any old processes using port %s", port)
    for conn in psutil.net_connections():
        if conn.laddr and getattr(conn.laddr, "port", None) == port:
            pid = conn.pid
            if pid and pid != os.getpid():
                try:
                    p = psutil.Process(pid)
                    logging.info("Killing PID %s (owner %s)", pid, p.username())
                    p.kill()
                except Exception as e:
                    logging.warning("Failed to kill %s: %s", pid, e)

# Try to free port on startup
try:
    free_port_kill(PORT)
except Exception:
    pass

# -----------------------
# STARTUP: run Flask with auto-restart loop (platform restarts too)
# -----------------------
def run_app_forever():
    while True:
        try:
            logging.info("Starting Flask on port %s", PORT)
            # Flask built-in server is OK for Render small apps; replace with gunicorn for heavy load.
            app.run(host="0.0.0.0", port=PORT)
        except Exception as e:
            logging.error("Flask crashed: %s", e)
        logging.info("Restarting app in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    logging.info("✅ JRAVIS initializing — scheduler & dashboard (Phases automation enabled).")
    logging.info("Dashboard (Render) will bind to port %s", PORT)
    run_app_forever()
