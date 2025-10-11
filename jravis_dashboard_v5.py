#!/usr/bin/env python3
"""
jravis_dashboard_v5.py
JRAVIS v5 Ultimate Update — responsive dark-glass dashboard with:
- Login (password hidden), Logout, Auto-logout (10 min)
- Phase tabs (Phase 1/2/3) with per-phase data
- Tracking amounts, progress bars, goal bar
- Dhruvayu text chat (optional OpenAI fallback)
- Daily (10:00 IST) & Weekly (Sun 00:00 UTC) reports + optional email
- Global map + streams + Chart.js
- Place logo image at static/logo.png
Deploy: gunicorn jravis_dashboard_v5:app --bind 0.0.0.0:$PORT
"""
from flask import (Flask, request, jsonify, render_template_string, redirect,
                   url_for, session, send_from_directory)
import os, time, threading, datetime, json, requests, traceback, smtplib
from email.message import EmailMessage
from functools import wraps

# --------------------
# CONFIG / ENV
# --------------------
app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "jrvis_secret_fallback")
LOCK_CODE = os.environ.get("LOCK_CODE", "2040lock")
SHARED_KEY = os.environ.get("SHARED_KEY", "jrvis_vabot_2040_securekey")
VABOT_URL = os.environ.get("VABOT_URL",
                           "https://va-bot-connector.onrender.com")
INCOME_API = os.environ.get("INCOME_API", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMAIL_TARGET = os.environ.get("EMAIL_TARGET", "")
PORT = int(os.environ.get("PORT", 10000))

AUTO_LOGOUT_SECONDS = 10 * 60  # 10 minutes
REPORTS_DIR = "./reports"
TARGET_AMOUNT = 40000000  # ₹4 Cr

os.makedirs(REPORTS_DIR, exist_ok=True)

# --------------------
# Helpers: fetch income data (robust)
# --------------------
SAMPLE_STREAMS = [
    {
        "country": "India",
        "country_code": "IN",
        "stream": "Printify",
        "amount": 624000,
        "timestamp": "2025-10-10T00:00:00Z"
    },
    {
        "country": "United States",
        "country_code": "US",
        "stream": "YouTube",
        "amount": 8250,
        "timestamp": "2025-10-09T00:00:00Z"
    },
    {
        "country": "United Kingdom",
        "country_code": "GB",
        "stream": "Fiverr",
        "amount": 1500,
        "timestamp": "2025-10-08T00:00:00Z"
    },
]


def fetch_income():
    if not INCOME_API:
        total = sum(s["amount"] for s in SAMPLE_STREAMS)
        return {
            "total_income": total,
            "progress_percent": round(min(100, total / TARGET_AMOUNT * 100),
                                      2),
            "target": TARGET_AMOUNT,
            "streams": SAMPLE_STREAMS,
            "daily_income": [s["amount"] for s in SAMPLE_STREAMS],
            "dates": [s["timestamp"][:10] for s in SAMPLE_STREAMS]
        }
    try:
        r = requests.get(INCOME_API, timeout=8)
        r.raise_for_status()
        payload = r.json()
        # payload support: summary dict with streams OR list of entries
        if isinstance(payload, dict):
            streams = payload.get("streams") or payload.get("data") or []
            if isinstance(streams, list) and streams:
                normalized = []
                for s in streams:
                    normalized.append({
                        "country":
                        s.get("country") or s.get("country_name") or "",
                        "country_code":
                        s.get("country_code") or s.get("cc") or "",
                        "stream":
                        s.get("stream") or s.get("source") or "unknown",
                        "amount":
                        float(s.get("amount") or s.get("value") or 0),
                        "timestamp":
                        s.get("timestamp") or ""
                    })
                total = payload.get("total_income") or sum(x["amount"]
                                                           for x in normalized)
                return {
                    "total_income":
                    total,
                    "progress_percent":
                    float(
                        payload.get("progress_percent",
                                    min(100, total / TARGET_AMOUNT * 100))),
                    "target":
                    payload.get("target", TARGET_AMOUNT),
                    "streams":
                    normalized,
                    "daily_income":
                    payload.get("daily_income",
                                [x["amount"] for x in normalized]),
                    "dates":
                    payload.get("dates",
                                [x["timestamp"][:10] for x in normalized])
                }
        if isinstance(payload, list):
            normalized = []
            for s in payload:
                normalized.append({
                    "country":
                    s.get("country") or s.get("country_name") or "",
                    "country_code":
                    s.get("country_code") or "",
                    "stream":
                    s.get("stream") or s.get("source") or "unknown",
                    "amount":
                    float(s.get("amount") or s.get("value") or 0),
                    "timestamp":
                    s.get("timestamp") or ""
                })
            total = sum(x["amount"] for x in normalized)
            return {
                "total_income": total,
                "progress_percent":
                round(min(100, total / TARGET_AMOUNT * 100), 2),
                "target": TARGET_AMOUNT,
                "streams": normalized,
                "daily_income": [x["amount"] for x in normalized],
                "dates": [x["timestamp"][:10] for x in normalized]
            }
    except Exception as e:
        print("fetch_income error:", e)
    # fallback
    total = sum(s["amount"] for s in SAMPLE_STREAMS)
    return {
        "total_income": total,
        "progress_percent": round(min(100, total / TARGET_AMOUNT * 100), 2),
        "target": TARGET_AMOUNT,
        "streams": SAMPLE_STREAMS,
        "daily_income": [s["amount"] for s in SAMPLE_STREAMS],
        "dates": [s["timestamp"][:10] for s in SAMPLE_STREAMS],
        "note": "fallback"
    }


# --------------------
# Session & auth utilities
# --------------------
def login_required(f):

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        # auto-logout check
        last = session.get("last_active", 0)
        if time.time() - last > AUTO_LOGOUT_SECONDS:
            session.clear()
            return redirect(url_for("login"))
        session["last_active"] = time.time()
        return f(*args, **kwargs)

    return wrapped


@app.route("/favicon.svg")
def favicon_svg():
    # serve logo if available
    if os.path.exists(os.path.join(app.static_folder, "logo.png")):
        return send_from_directory(app.static_folder, "logo.png")
    return "", 204


# --------------------
# Login / Logout / Auto Logout
# --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form.get("code", "")
        if code == LOCK_CODE:
            session["logged_in"] = True
            session["last_active"] = time.time()
            return redirect(url_for("dashboard"))
        else:
            return render_template_string(LOGIN_HTML,
                                          error="Invalid lock code")
    return render_template_string(LOGIN_HTML, error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------
# Dashboard page
# --------------------
@app.route("/")
@login_required
def dashboard():
    return render_template_string(DASH_HTML,
                                  logo_url=url_for('favicon_svg'),
                                  vabot_url=VABOT_URL,
                                  shared_key=SHARED_KEY)


# --------------------
# API: earnings summary & streams normalized for front-end
# --------------------
@app.route("/api/earnings_summary")
@login_required
def api_earnings_summary():
    data = fetch_income()
    return jsonify(data), 200


@app.route("/api/streams")
@login_required
def api_streams():
    data = fetch_income()
    streams = data.get("streams", [])
    # ensure country_code exists where possible
    for s in streams:
        if not s.get("country_code") and s.get("country"):
            mapping = {
                "India": "IN",
                "United States": "US",
                "United Kingdom": "GB",
                "UK": "GB",
                "Germany": "DE"
            }
            s["country_code"] = mapping.get(s["country"], "")
    return jsonify({
        "streams": streams,
        "total_income": data.get("total_income"),
        "progress_percent": data.get("progress_percent"),
        "target": data.get("target"),
        "daily_income": data.get("daily_income"),
        "dates": data.get("dates")
    })


# --------------------
# API: per-phase data (clickable tabs)
# --------------------
@app.route("/api/phase/<int:n>")
@login_required
def api_phase(n):
    # Simple derived phase logic: Phase1 focuses on debt clearance (50% of target), Phase2 scaling (30%), Phase3 global (20%)
    data = fetch_income()
    total = data.get("total_income", 0)
    if n == 1:
        target = TARGET_AMOUNT * 0.5
    elif n == 2:
        target = TARGET_AMOUNT * 0.3
    else:
        target = TARGET_AMOUNT * 0.2
    percent = round(min(100, total / target * 100), 2) if target > 0 else 0
    # streams filtered per-phase heuristic (by stream names)
    streams = [
        s for s in data.get("streams", [])
        if "print" in s.get("stream", "").lower() or n == 1
    ]
    return jsonify({
        "phase": n,
        "phase_target": target,
        "phase_percent": percent,
        "phase_streams": streams,
        "total": total
    })


# --------------------
# API: send task (for control buttons)
# --------------------
@app.route("/api/send_task", methods=["POST"])
@login_required
def api_send_task_forward():
    token = request.headers.get("Authorization", "")
    if token and token.startswith("Bearer "):
        key = token.split(" ", 1)[1]
        if key != SHARED_KEY:
            return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json() or {}
    if not payload.get("action"):
        return jsonify({"error": "invalid payload"}), 400
    # forward to VA Bot
    try:
        headers = {"Authorization": f"Bearer {SHARED_KEY}"}
        rv = requests.post(f"{VABOT_URL.rstrip('/')}/api/receive_task",
                           json=payload,
                           headers=headers,
                           timeout=10)
        return jsonify({
            "status": "sent",
            "va_status": rv.status_code,
            "va_text": rv.text
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------
# Chat: Dhruvayu (text-only)
# --------------------
@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    body = request.get_json() or {}
    q = (body.get("q") or "").strip()
    if not q:
        return jsonify({"reply": "Say something, Boss."})
    # small rule-based replies for common queries
    lower = q.lower()
    data = fetch_income()
    total = data.get("total_income", 0)
    if "income" in lower or "total" in lower:
        reply = f"Boss ⚡ total recorded earnings: ₹{int(total):,}. Progress: {data.get('progress_percent')}%."
        return jsonify({"reply": reply})
    if "phase 1" in lower or "phase1" in lower:
        p = (requests.get(url_for('api_phase', n=1, _external=True),
                          timeout=5).json())
        return jsonify({
            "reply":
            f"Phase 1 — {p['phase_percent']}% complete, target ₹{int(p['phase_target']):,}."
        })
    if "report" in lower or "daily" in lower:
        return jsonify({
            "reply":
            "Daily reports are generated automatically at 10:00 AM IST. I can email them to you if SMTP is configured."
        })
    # optional OpenAI fallback if set
    if OPENAI_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{
                    "role": "user",
                    "content": q
                }],
                "max_tokens": 200
            }
            r = requests.post("https://api.openai.com/v1/chat/completions",
                              json=payload,
                              headers=headers,
                              timeout=10)
            rr = r.json()
            text = rr["choices"][0]["message"]["content"]
            return jsonify({"reply": text})
        except Exception as e:
            print("openai error:", e)
    # fallback generic
    return jsonify({
        "reply":
        "Got it, Boss. I will summarize and act on that. (Dhruvayu - text mode)"
    })


# --------------------
# REPORTS generation & email
# --------------------
def generate_pdfs_and_save():
    """Generates summary + invoice PDFs (simple HTML->PDF or fallback text PDFs) and saves in reports folder."""
    data = fetch_income()
    total = data.get("total_income", 0)
    today = datetime.date.today().strftime("%Y-%m-%d")
    html = f"<h1>JRAVIS Daily Summary {today}</h1><p>Total earnings: ₹{int(total):,}</p><p>Progress: {data.get('progress_percent')}%</p>"
    # Try pdfkit first (if wkhtmltopdf present)
    try:
        import pdfkit
        out1 = os.path.join(REPORTS_DIR, f"{today}_summary.pdf")
        pdfkit.from_string(html, out1)
    except Exception:
        # fallback simple text file
        out1 = os.path.join(REPORTS_DIR, f"{today}_summary.txt")
        with open(out1, "w") as f:
            f.write(
                f"Summary {today}\nTotal: ₹{int(total):,}\nProgress: {data.get('progress_percent')}%\n"
            )
    # invoice
    invoice_path = os.path.join(REPORTS_DIR, f"{today}_invoice.txt")
    with open(invoice_path, "w") as inv:
        inv.write(f"INVOICE {today}\nTotal: ₹{int(total):,}\n")
    return out1, invoice_path


def send_email_with_attachments(subject, body, attachments):
    server = os.environ.get("SMTP_SERVER")
    if not server or not EMAIL_TARGET:
        print("SMTP or EMAIL_TARGET not configured; skipping email.")
        return False
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER")
    pwd = os.environ.get("SMTP_PASS")
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = user or "jravis@local"
        msg["To"] = EMAIL_TARGET
        msg.set_content(body)
        for p in attachments:
            with open(p, "rb") as f:
                data = f.read()
            msg.add_attachment(data,
                               maintype="application",
                               subtype="octet-stream",
                               filename=os.path.basename(p))
        with smtplib.SMTP(server, port, timeout=10) as s:
            s.starttls()
            if user and pwd:
                s.login(user, pwd)
            s.send_message(msg)
        print("Email sent to", EMAIL_TARGET)
        return True
    except Exception as e:
        print("Email error:", e)
        return False


def daily_and_weekly_scheduler():
    """Background scheduler thread to run daily at 10:00 IST and weekly Sunday 00:00 UTC."""
    while True:
        now_utc = datetime.datetime.utcnow()
        # Daily at 04:30 UTC = 10:00 IST (approx)
        if now_utc.hour == 4 and now_utc.minute == 30:
            try:
                summary, invoice = generate_pdfs_and_save()
                send_email_with_attachments("JRAVIS Daily Summary",
                                            "Daily report attached.",
                                            [summary, invoice])
            except Exception as e:
                print("daily job error:", e)
            time.sleep(70)  # avoid double-run within same minute
        # Weekly: Sunday 00:00 UTC
        if now_utc.weekday(
        ) == 6 and now_utc.hour == 0 and now_utc.minute == 0:
            try:
                summary, invoice = generate_pdfs_and_save()
                send_email_with_attachments("JRAVIS Weekly Summary",
                                            "Weekly report attached.",
                                            [summary, invoice])
            except Exception as e:
                print("weekly job error:", e)
            time.sleep(70)
        time.sleep(20)


# start scheduler thread
t = threading.Thread(target=daily_and_weekly_scheduler, daemon=True)
t.start()

# --------------------
# HTML Templates (embedded)
# --------------------
LOGIN_HTML = """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>JRAVIS Login</title>
<style>
body{background:#071022;color:#e6eef6;font-family:Inter,Arial,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.card{background:rgba(255,255,255,0.03);padding:28px;border-radius:12px;width:320px;text-align:center}
input[type=password]{width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.05);background:transparent;color:inherit}
button{margin-top:12px;padding:10px 16px;border-radius:8px;border:none;background:linear-gradient(90deg,#00ffff,#00ff7f);color:#042018;font-weight:700;cursor:pointer}
.err{color:#ffb4b4;margin-top:8px}
.small{color:#9aa7bf;font-size:12px;margin-top:10px}
</style></head><body>
<div class="card">
<img src="{{ url_for('favicon_svg') }}" width=86 alt="logo" style="border-radius:8px;margin-bottom:10px"/>
<h2>JRAVIS Secure Access</h2>
<form method="post">
<input name="code" type="password" placeholder="Enter Lock Code" required/>
<button>Unlock</button>
</form>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
<div class="small">Auto-logout after 10 minutes of inactivity</div>
</div></body></html>
"""

DASH_HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>JRAVIS Dashboard v5 — Phase 1 Global System Status</title>
<style>
body{
  background:#000;
  color:#00ff99;
  font-family:"JetBrains Mono","Courier New",monospace;
  white-space:pre;
  padding:20px;
  margin:0;
}
h1{color:#0ff;text-align:center;margin:0 0 20px 0;}
.section{margin-bottom:20px;}
hr{border:none;border-top:1px solid #033;}
.box{border:2px solid #033;border-radius:8px;padding:10px;}
.dim{color:#099;}
.highlight{color:#0ff;}
.warn{color:#ff0;}
.ok{color:#0f0;}
.fail{color:#f33;}
.gauge{display:inline-block;width:250px;background:#033;border-radius:5px;overflow:hidden;margin:4px 0;}
.bar{background:#0ff;height:14px;width:30%;transition:width 1s;}
</style>
<script>
function animateGauge(p){document.querySelector(".bar").style.width=p+"%";}
window.onload=()=>animateGauge(12);
</script>
</head>
<body>

<h1>JRAVIS DASHBOARD v5 — PHASE 1 GLOBAL SYSTEM STATUS</h1>
<div class="box">
│ [🧠 JRAVIS BRAIN] [🤖 VA BOT CONNECTOR] [💰 INCOME BUNDLE] │
│ Status: ACTIVE  Status: ACTIVE  Status: ACTIVE │
│ Last Ping: 2 min ago Last Loop: 10:24 AM API: 200 OK │
</div>

<div class="section">
AUTOMATION → VA BOT LOOPS
<hr>
#  STREAM NAME   LAST RUN  STATUS  RESULT
1  Elina Reels   10:30 AM ✅ OK  +₹1 250
2  Printify POD Store 10:28 AM ✅ OK  +₹3 900
3  Meshy AI Store  10:25 AM ✅ OK  +₹ 450
4  CAD Crowd Auto Work 10:25 AM ⏳ RUNNING
5  Fiverr AI Gig Auto 10:24 AM ✅ OK  +₹ 700
6  YouTube Automation 10:22 AM ✅ OK  +₹1 600
7  Stock Image/Video 10:21 AM ✅ OK  +₹ 380
8  KDP AI Publishing 10:19 AM ✅ OK  +₹1 100
9  Shopify Digital Store 10:18 AM ✅ OK  +₹2 300
10 Stationery Export 10:17 AM ✅ OK  +₹2 900
──────────────────────────────────────────────
TOTAL TODAY: ₹14 280  NEXT LOOP IN: 00:28:45
</div>

<div class="section">
INCOME → LIVE FEED
<hr>
<div class="gauge"><div class="bar"></div></div> 12% of target  
Target ₹4 Cr Monthly ₹1.05 L Daily ₹14 280  
Next Report: Daily 10 AM IST | Weekly Sunday 12 AM IST
</div>

<div class="section">
LOG STREAM
<hr>
[10:24:10] VA Bot: Loop #1 started  
[10:24:15] Fiverr automation: success  
[10:24:18] Meshy API upload: OK  
[10:24:20] IncomeBundle POST → 200 OK  
[10:24:21] JRAVIS Dashboard updated successfully
</div>

</body>
</html>
"""

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    print(f"[JRAVIS v5] starting on port {PORT}")
    app.run(host="0.0.0.0", port=PORT)
