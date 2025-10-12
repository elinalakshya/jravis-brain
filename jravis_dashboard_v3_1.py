#!/usr/bin/env python3
"""
jravis_dashboard_v3_1.py
Single-file JRAVIS dashboard + connector (deploy-ready)

Environment variables expected:
  SECRET_KEY          - Flask session secret
  LOCK_CODE           - numeric/string lock code (default 2040)
  SHARED_KEY          - shared secret used between JRAVIS <-> VA Bot
  VABOT_URL           - VA Bot public URL (default https://vabot-dashboard.onrender.com)
  JDB_PATH            - optional SQLite DB path (default ./jravis_tasks.db)
  JRV_POLL_SECONDS    - optional polling interval (default 10)
"""
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import os, threading, time, sqlite3, json, requests, traceback
from datetime import datetime

# -------------------------
# Basic config & Flask app
# -------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "jravis_secret_key_fallback")

LOCK_CODE = os.environ.get("LOCK_CODE", "2040")
SHARED_KEY = os.environ.get(
    "SHARED_KEY", os.environ.get("VABOT_API_KEY", "change-this-securely"))
VABOT_URL = os.environ.get("VABOT_URL",
                           "https://vabot-dashboard.onrender.com").rstrip('/')
DB_PATH = os.environ.get("JDB_PATH", "./jravis_tasks.db")
POLL_INTERVAL = int(os.environ.get("JRV_POLL_SECONDS", 10))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 5))

ALLOWED_ACTIONS = {
    "start_stream", "stop_stream", "collect_report", "run_phase"
}


# -------------------------
# Utilities
# -------------------------
def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def log(*args, **kwargs):
    print("[JRAVIS]", *args, **kwargs)


# -------------------------
# SQLite DB (tasks + status)
# -------------------------
def init_db(path=DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS task_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_json TEXT,
            status TEXT,
            tries INTEGER,
            created_at TEXT,
            updated_at TEXT,
            last_error TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS vabot_callbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload_json TEXT,
            received_at TEXT
        )
    ''')
    conn.commit()
    return conn


DB_CONN = init_db()
DB_LOCK = threading.Lock()


def enqueue_task(task):
    if task.get("action") not in ALLOWED_ACTIONS:
        raise ValueError(f"Action not allowed: {task.get('action')}")
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "INSERT INTO task_queue (task_json,status,tries,created_at,updated_at) VALUES (?,?,?,?,?)",
            (json.dumps(task), "queued", 0, now_iso(), now_iso()))
        DB_CONN.commit()
        return c.lastrowid


def get_next_task():
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "SELECT id, task_json, status, tries FROM task_queue WHERE status IN ('queued','retry') ORDER BY id LIMIT 1"
        )
        return c.fetchone()


def update_task(id, status, tries=None, last_error=None):
    with DB_LOCK:
        c = DB_CONN.cursor()
        if tries is None:
            c.execute(
                "UPDATE task_queue SET status=?, updated_at=?, last_error=? WHERE id=?",
                (status, now_iso(), last_error, id))
        else:
            c.execute(
                "UPDATE task_queue SET status=?, tries=?, updated_at=?, last_error=? WHERE id=?",
                (status, tries, now_iso(), last_error, id))
        DB_CONN.commit()


def save_vabot_callback(payload):
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "INSERT INTO vabot_callbacks (payload_json, received_at) VALUES (?,?)",
            (json.dumps(payload), now_iso()))
        DB_CONN.commit()
        return c.lastrowid


# -------------------------
# Networking to VA Bot
# -------------------------
def post_to_vabot(task):
    url = VABOT_URL.rstrip('/') + "/api/receive_task"
    headers = {
        "Authorization": f"Bearer {SHARED_KEY}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(url, json=task, headers=headers, timeout=20)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)


# -------------------------
# Background worker
# -------------------------
def worker_loop():
    log("Background worker started, polling every", POLL_INTERVAL, "s")
    while True:
        try:
            row = get_next_task()
            if not row:
                time.sleep(POLL_INTERVAL)
                continue
            tid, task_json, status, tries = row
            task = json.loads(task_json)
            log("Sending task", tid, task)
            code, text = post_to_vabot(task)
            if code == 200:
                update_task(tid, "sent", (tries or 0) + 1, None)
                log("Task sent:", tid)
            else:
                tries = (tries or 0) + 1
                if tries >= MAX_RETRIES:
                    update_task(tid, "failed", tries, f"final error: {text}")
                    log("Task failed permanently:", tid, text)
                else:
                    update_task(tid, "retry", tries, f"error: {text}")
                    log("Task retry scheduled:", tid,
                        f"attempts={tries} error={text}")
            time.sleep(0.5)
        except Exception as e:
            log("Worker exception:", e)
            traceback.print_exc()
            time.sleep(3)


_worker_thread = None


def start_worker():
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return _worker_thread
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    _worker_thread = t
    log("✅ JRAVIS connector background worker started")
    return t


# -------------------------
# Flask routes: UI + API
# -------------------------
UNLOCK_HTML = """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JRAVIS Dashboard</title>
<style>
body{margin:0;font-family:Inter, Arial, sans-serif;background:#071022;color:#e6eef6;display:flex;align-items:center;justify-content:center;height:100vh}
.card{background:rgba(255,255,255,0.03);padding:24px;border-radius:12px;width:320px;box-shadow:0 6px 24px rgba(0,0,0,0.6)}
input{width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:inherit}
button{margin-top:10px;padding:10px;border-radius:8px;border:0;background:#6ee7b7;color:#042018;font-weight:700}
.small{color:#9aa7bf;font-size:12px;margin-top:8px}
.err{color:#ffb4b4;margin-top:8px}
</style>
</head><body>
<div class="card">
  <h2>JRAVIS</h2>
  <form method="post">
    <input name="code" placeholder="Enter lock code" autocomplete="one-time-code" required>
    <button>Unlock</button>
  </form>
  {% if error %}<div class="err">{{error}}</div>{% endif %}
  <div class="small">VA Bot: {{vabot_url}}</div>
</div>
</body></html>
"""

DASH_HTML = """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JRAVIS v3.1</title>
<style>
body{margin:0;font-family:Inter, Arial, sans-serif;background:linear-gradient(180deg,#030408,#071022);color:#e6eef6}
.wrap{padding:18px;max-width:1100px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center}
.logo{font-weight:800;background:linear-gradient(135deg,#0ea5a0,#6366f1);padding:10px;border-radius:10px}
.grid{display:grid;grid-template-columns:1fr 360px;gap:18px;margin-top:18px}
.card{background:rgba(255,255,255,0.02);padding:12px;border-radius:12px}
.chat{max-height:360px;overflow:auto}
.msg{padding:8px;border-radius:8px;margin-bottom:8px}
.me{background:rgba(110,231,183,0.06);align-self:flex-end}
.bot{background:rgba(255,255,255,0.02)}
.small{color:#9aa7bf;font-size:13px}
@media(max-width:880px){.grid{grid-template-columns:1fr}}
</style>
</head><body>
<div class="wrap">
  <div class="header">
    <div style="display:flex;gap:12px;align-items:center">
      <div class="logo">JR</div>
      <div>
        <div style="font-weight:700">JRAVIS · VA Bot</div>
        <div class="small">Auto-run & monitor</div>
      </div>
    </div>
    <div class="small">VA Bot: {{vabot_url}}</div>
  </div>

  <div class="grid">
    <div>
      <div class="card">
        <h3>Today</h3>
        <div class="small">Queued tasks: {{queued_count}}</div>
        <div class="small">Callbacks: {{callback_count}}</div>
      </div>

      <div class="card" style="margin-top:12px">
        <h3>Actions</h3>
        <div style="display:flex;gap:8px">
          <form method="post" action="/api/send_task" style="display:flex;gap:8px">
            <input name="action" placeholder="action (start_stream)" required>
            <input name="stream" placeholder="stream (Printify)">
            <button type="submit">Enqueue</button>
          </form>
        </div>
      </div>
    </div>

    <div>
      <div class="card">
        <h3>Recent callbacks</h3>
        <div>
          {% for cb in callbacks %}
            <div class="small" style="margin-bottom:8px"><strong>{{cb.received_at}}</strong><div>{{cb.payload}}</div></div>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>
</div>
</body></html>
"""

<div class="card glass-card" style="padding:20px; border-radius:20px; text-align:center;">
  <h2>💰 Mission 2040 Progress</h2>
  <div id="income-total" style="font-size:1.4rem; margin:10px 0;">Loading...</div>
  <div class="bar-container" style="width:80%; margin:auto; background:#333; border-radius:10px; height:25px;">
    <div id="progress-bar" style="height:25px; border-radius:10px; background:linear-gradient(90deg,#00ffff,#00ff00); width:0%; transition:width 1s ease;"></div>
  </div>
  <p id="progress-text" style="margin-top:10px;">Syncing...</p>
</div>

<script>
async function updateEarnings() {
  try {
    const response = await fetch("https://income-system-bundle.onrender.com/api/earnings_summary");
    const data = await response.json();
    document.getElementById("income-total").innerHTML = 
      `₹${data.total_income.toLocaleString()} / ₹${data.target.toLocaleString()}`;
    document.getElementById("progress-bar").style.width = data.progress_percent + "%";
    document.getElementById("progress-text").innerText = 
      data.progress_percent + "% complete • Next report: " + data.next_report_time;
  } catch (err) {
    document.getElementById("income-total").innerText = "Error syncing data";
  }
}

// initial call + auto-refresh every 30s
updateEarnings();
setInterval(updateEarnings, 30000);
</script>

@app.route("/", methods=["GET", "POST"])
def index():
    if session.get("unlocked"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        code = request.form.get("code", "")
        if code == LOCK_CODE:
            session["unlocked"] = True
            return redirect(url_for("dashboard"))
        error = "Incorrect code"
    return render_template_string(UNLOCK_HTML,
                                  error=error,
                                  vabot_url=VABOT_URL)


@app.route("/dashboard")
def dashboard():
    if not session.get("unlocked"):
        return redirect(url_for("index"))
    # gather stats
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "SELECT COUNT(*) FROM task_queue WHERE status IN ('queued','retry')"
        )
        queued_count = c.fetchone()[0] or 0
        c.execute(
            "SELECT id, payload_json, received_at FROM vabot_callbacks ORDER BY id DESC LIMIT 10"
        )
        rows = c.fetchall()
    callbacks = [{
        "payload": json.loads(r[1]) if r[1] else r[1],
        "received_at": r[2]
    } for r in rows]
    return render_template_string(DASH_HTML,
                                  vabot_url=VABOT_URL,
                                  queued_count=queued_count,
                                  callback_count=len(callbacks),
                                  callbacks=callbacks)


# -------------------------
# API: enqueue task (from UI or curl)
# -------------------------
@app.route("/api/send_task", methods=["POST"])
def api_send_task():
    # optional auth via header
    auth = request.headers.get("Authorization", "")
    if auth:
        token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
        if token != SHARED_KEY:
            return jsonify({"error": "unauthorized"}), 401

    # accept form (from dashboard) or JSON
    if request.is_json:
        data = request.get_json()
    else:
        data = {k: request.form.get(k) for k in ("action", "stream", "phase")}
    if not data or "action" not in data:
        return jsonify({"error": "no action provided"}), 400
    try:
        tid = enqueue_task(data)
        return jsonify({"status": "ok", "task_id": tid}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# API: task status
# -------------------------
@app.route("/api/task_status/<int:task_id>", methods=["GET"])
def api_task_status(task_id):
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "SELECT id, task_json, status, tries, created_at, updated_at, last_error FROM task_queue WHERE id=?",
            (task_id, ))
        r = c.fetchone()
        if not r:
            return jsonify({"error": "not found"}), 404
        return jsonify({
            "id": r[0],
            "task": json.loads(r[1]),
            "status": r[2],
            "tries": r[3],
            "created_at": r[4],
            "updated_at": r[5],
            "last_error": r[6]
        }), 200


# -------------------------
# VA Bot callback endpoint
# -------------------------
@app.route("/api/vabot_status", methods=["POST"])
def vabot_status():
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
    if token != SHARED_KEY:
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json(force=True)
    log("VA Bot callback received:", payload)
    save_vabot_callback(payload)
    return jsonify({"status": "ok"}), 200


# -------------------------
# list tasks (admin)
# -------------------------
@app.route("/api/list_tasks", methods=["GET"])
def api_list_tasks():
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "SELECT id, task_json, status, tries, created_at, updated_at FROM task_queue ORDER BY id DESC LIMIT 100"
        )
        rows = c.fetchall()
    out = [{
        "id": r[0],
        "task": json.loads(r[1]),
        "status": r[2],
        "tries": r[3],
        "created_at": r[4],
        "updated_at": r[5]
    } for r in rows]
    return jsonify(out), 200


# -------------------------
# health
# -------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": now_iso()}), 200


# -------------------------
# Start worker & app
# -------------------------
if __name__ == "__main__":
    # Start the background worker before running the web server
    start_worker()
    log("Starting JRAVIS Dashboard v3.1")
    port = int(os.environ.get("PORT", 10000))
    # Run Flask for Render: it will listen on the provided port
    app.run(host="0.0.0.0", port=port)
