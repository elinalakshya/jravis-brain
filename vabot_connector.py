#!/usr/bin/env python3
"""
vabot_connector.py
------------------
VA Bot ↔ JRAVIS connector.
• Receives tasks from JRAVIS (/api/receive_task)
• Executes or simulates the work
• Sends completion status back to JRAVIS (/api/vabot_status)
• Stores a local SQLite queue for reliability
"""

import os, threading, time, sqlite3, json, requests, traceback
from datetime import datetime

# --- CONFIG ---
DB = os.environ.get("VADB_PATH", "./vabot_tasks.db")
JRAVIS_URL = os.environ.get(
    "JRAVIS_URL", "https://jravis-dashboard.onrender.com").rstrip("/")
SHARED_KEY = os.environ.get(
    "SHARED_KEY", os.environ.get("VABOT_API_KEY", "change-this-securely"))
POLL_INTERVAL = int(os.environ.get("VABOT_POLL_SECONDS", 10))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 5))

ALLOWED_ACTIONS = {
    "start_stream", "stop_stream", "collect_report", "run_phase"
}


def now():
    return datetime.utcnow().isoformat() + "Z"


# --- DATABASE ---
def init_db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vabot_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_json TEXT,
            status TEXT,
            tries INTEGER,
            created_at TEXT,
            updated_at TEXT,
            last_error TEXT
        )
    """)
    conn.commit()
    return conn


DB_CONN = init_db()
DB_LOCK = threading.Lock()


def enqueue_task(task_dict):
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "INSERT INTO vabot_queue (task_json,status,tries,created_at,updated_at) VALUES (?,?,?,?,?)",
            (json.dumps(task_dict), 'queued', 0, now(), now()))
        DB_CONN.commit()
        return c.lastrowid


def get_next_task():
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "SELECT id, task_json, status, tries FROM vabot_queue WHERE status IN ('queued','retry') ORDER BY id LIMIT 1"
        )
        return c.fetchone()


def mark_task(id, status, tries=None, last_error=None):
    with DB_LOCK:
        c = DB_CONN.cursor()
        if tries is None:
            c.execute(
                "UPDATE vabot_queue SET status=?, updated_at=?, last_error=? WHERE id=?",
                (status, now(), last_error, id))
        else:
            c.execute(
                "UPDATE vabot_queue SET status=?, tries=?, updated_at=?, last_error=? WHERE id=?",
                (status, tries, now(), last_error, id))
        DB_CONN.commit()


# --- SEND STATUS BACK TO JRAVIS ---
def notify_jravis(status_payload):
    headers = {
        "Authorization": f"Bearer {SHARED_KEY}",
        "Content-Type": "application/json"
    }
    url = JRAVIS_URL + "/api/vabot_status"
    try:
        r = requests.post(url,
                          headers=headers,
                          json=status_payload,
                          timeout=20)
        print(f"[VA Bot] Callback → {r.status_code}: {r.text}")
    except Exception as e:
        print("[VA Bot] callback error:", e)


# --- TASK EXECUTION (simulation) ---
def execute_task(task):
    action = task.get("action")
    stream = task.get("stream", "")
    phase = task.get("phase", "")
    print(f"[VA Bot] Executing: {action} on {stream} (phase {phase})")

    # Simulated delay / work
    time.sleep(3)
    # Example: pretend success
    return {
        "result": "success",
        "stream": stream,
        "action": action,
        "phase": phase
    }


# --- WORKER LOOP ---
def worker_loop():
    while True:
        try:
            row = get_next_task()
            if not row:
                time.sleep(POLL_INTERVAL)
                continue

            tid, task_json, status, tries = row
            task = json.loads(task_json)
            print(f"[VA Bot] Processing task #{tid}: {task}")

            try:
                result = execute_task(task)
                mark_task(tid, "done", (tries or 0) + 1, None)
                notify_jravis({
                    "task_id": tid,
                    "status": "done",
                    "details": result
                })
            except Exception as e:
                tries = (tries or 0) + 1
                if tries >= MAX_RETRIES:
                    mark_task(tid, "failed", tries, str(e))
                else:
                    mark_task(tid, "retry", tries, str(e))
            time.sleep(1)

        except Exception as e:
            print("[VA Bot] worker exception:", e)
            traceback.print_exc()
            time.sleep(3)


def start_background_worker():
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    print("✅ VA Bot background worker started")
    return t


# --- FLASK ENDPOINTS ---
def register_endpoints(app):
    from flask import request, jsonify

    @app.route("/api/receive_task", methods=["POST"])
    def receive_task():
        auth = request.headers.get("Authorization", "")
        token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
        if token != SHARED_KEY:
            return jsonify({"error": "unauthorized"}), 401

        data = request.get_json(force=True)
        if data.get("action") not in ALLOWED_ACTIONS:
            return jsonify({"error": "invalid action"}), 400

        tid = enqueue_task(data)
        print(f"[VA Bot] Task queued #{tid}: {data}")
        return jsonify({"status": "queued", "id": tid}), 200

    @app.route("/api/vabot_list_tasks", methods=["GET"])
    def list_tasks():
        with DB_LOCK:
            c = DB_CONN.cursor()
            c.execute(
                "SELECT id, task_json, status, tries, created_at, updated_at FROM vabot_queue ORDER BY id DESC LIMIT 100"
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


# --- STANDALONE TEST MODE ---
if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    register_endpoints(app)
    start_background_worker()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
