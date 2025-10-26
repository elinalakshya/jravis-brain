#!/usr/bin/env python3
"""
phase1_execution_core.py

Reads config/phase1_config.json and dispatches scheduled tasks to VA Bot.
Tracks attempts and results in a small SQLite DB.
"""

import os
import json
import time
import sqlite3
import threading
import logging
import requests
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# -----------------------
# CONFIG & ENV
# -----------------------
PHASE_CONFIG_PATH = os.getenv("PHASE_CONFIG", "config/phase1_config.json")
VA_BOT_ENDPOINT = os.getenv("VA_BOT_ENDPOINT")  # required
JRAVIS_SECRET_KEY = os.getenv("JRAVIS_SECRET_KEY", "LakshyaSecureKey@2025")
DB_PATH = os.getenv("DB_PATH", "phase1_exec.db")
WORKER_ID = os.getenv("WORKER_ID", "phase1-exec-worker-1")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if VA_BOT_ENDPOINT is None:
    raise RuntimeError("VA_BOT_ENDPOINT environment variable is required")

# -----------------------
# LOGGING
# -----------------------
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("phase1_exec")

# -----------------------
# DB LAYER
# -----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        system_id INTEGER,
        action TEXT,
        scheduled_at TIMESTAMP,
        run_at TIMESTAMP,
        attempts INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        last_error TEXT,
        payload TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS exec_log (
        id TEXT PRIMARY KEY,
        task_id TEXT,
        timestamp TIMESTAMP,
        status TEXT,
        response_code INTEGER,
        response_text TEXT
    )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)


def save_task(task: Dict[str, Any]):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO tasks (id, system_id, action, scheduled_at, run_at, attempts, status, last_error, payload)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        task["id"],
        task["system_id"],
        task["action"],
        task.get("scheduled_at"),
        task.get("run_at"),
        task.get("attempts", 0),
        task.get("status", "pending"),
        task.get("last_error"),
        json.dumps(task.get("payload", {}))
    ))
    conn.commit()
    conn.close()


def fetch_pending(limit=50) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("""
        SELECT id, system_id, action, scheduled_at, run_at, attempts, status, last_error, payload
        FROM tasks
        WHERE status IN ('pending','retry') AND (run_at IS NULL OR run_at <= ?)
        ORDER BY run_at ASC
        LIMIT ?
    """, (now, limit))
    rows = c.fetchall()
    conn.close()
    tasks=[]
    for r in rows:
        tasks.append({
            "id": r[0],
            "system_id": r[1],
            "action": r[2],
            "scheduled_at": r[3],
            "run_at": r[4],
            "attempts": r[5],
            "status": r[6],
            "last_error": r[7],
            "payload": json.loads(r[8]) if r[8] else {}
        })
    return tasks


def mark_task_status(task_id: str, status: str, error: Optional[str]=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tasks SET status=?, last_error=? WHERE id=?", (status, error, task_id))
    conn.commit()
    conn.close()


def log_execution(task_id: str, status: str, code: int, text: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    lid = str(uuid.uuid4())
    c.execute("""
        INSERT INTO exec_log (id, task_id, timestamp, status, response_code, response_text)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (lid, task_id, datetime.utcnow().isoformat(), status, code, text[:2000]))
    conn.commit()
    conn.close()

# -----------------------
# UTIL
# -----------------------
def hmac_signature(payload_bytes: bytes) -> str:
    mac = hmac.new(JRAVIS_SECRET_KEY.encode('utf-8'), payload_bytes, hashlib.sha256)
    return mac.hexdigest()

def iso_now():
    return datetime.utcnow().isoformat()

def next_run_from_frequency(freq: str) -> datetime:
    """
    Interpret simple frequency strings and return the next run datetime (UTC).
    Supported: "3_per_day", "daily", "weekly", "biweekly", "hourly", "hourly_sync"
    """
    now = datetime.utcnow()
    if freq.endswith("_per_day") or "_per_day" in freq:
        parts = freq.split("_")
        try:
            n = int(parts[0])
        except Exception:
            n = 1
        # schedule next in 24/n hours:
        delta = timedelta(hours=24.0 / max(1, n))
        return now + delta
    if freq == "daily":
        return now + timedelta(days=1)
    if freq == "weekly":
        return now + timedelta(weeks=1)
    if freq == "biweekly":
        return now + timedelta(weeks=2)
    if freq in ("hourly", "hourly_sync"):
        return now + timedelta(hours=1)
    # fallback: default daily
    return now + timedelta(days=1)

# -----------------------
# CORE: dispatch to VA Bot
# -----------------------
def send_to_vabot(system: Dict[str,Any], action: str, payload: Dict[str,Any]) -> Dict[str,Any]:
    """
    Send a signed task to VA Bot endpoint.
    Returns a dict with keys: success(bool), code(int), text(str)
    """
    task_id = str(uuid.uuid4())
    body = {
        "task_id": task_id,
        "worker_id": WORKER_ID,
        "system_id": system.get("id"),
        "system_name": system.get("name"),
        "action": action,
        "payload": payload,
        "timestamp": iso_now()
    }
    data = json.dumps(body).encode("utf-8")
    signature = hmac_signature(data)

    headers = {
        "Content-Type": "application/json",
        "X-JRAVIS-Sign": signature
    }

    try:
        r = requests.post(VA_BOT_ENDPOINT, headers=headers, data=data, timeout=20)
        logger.debug("VA Bot response (%s): %s", r.status_code, r.text[:300])
        success = r.status_code >= 200 and r.status_code < 300
        return {"success": success, "code": r.status_code, "text": r.text}
    except Exception as e:
        logger.exception("Error posting to VA Bot")
        return {"success": False, "code": 0, "text": str(e)}


# -----------------------
# ACTION HANDLER (sends instructions to VA bot)
# -----------------------
def build_payload_for_system(system: Dict[str,Any]) -> Dict[str,Any]:
    # Basic payload with data_source and system metadata. VA Bot will fetch the feed.
    return {
        "data_source": system.get("data_source"),
        "system": {
            "id": system.get("id"),
            "name": system.get("name"),
            "platform": system.get("platform")
        },
        "meta": {
            "scheduled_by": WORKER_ID,
            "phase": "1"
        }
    }

# Map action strings to handlers (currently all actions forward to VA Bot with a consistent structure).
ACTION_HANDLERS = {
    "auto_post_reels": lambda s: send_to_vabot(s, "auto_post_reels", build_payload_for_system(s)),
    "auto_pin_pinterest": lambda s: send_to_vabot(s, "auto_pin_pinterest", build_payload_for_system(s)),
    "reddit_discord_posts": lambda s: send_to_vabot(s, "reddit_discord_posts", build_payload_for_system(s)),
    "auto_apply_jobs": lambda s: send_to_vabot(s, "auto_apply_jobs", build_payload_for_system(s)),
    "auto_refresh_gigs": lambda s: send_to_vabot(s, "auto_refresh_gigs", build_payload_for_system(s)),
    "auto_upload_videos": lambda s: send_to_vabot(s, "auto_upload_videos", build_payload_for_system(s)),
    "auto_upload_assets": lambda s: send_to_vabot(s, "auto_upload_assets", build_payload_for_system(s)),
    "auto_publish_books": lambda s: send_to_vabot(s, "auto_publish_books", build_payload_for_system(s)),
    "email_drip_campaign": lambda s: send_to_vabot(s, "email_drip_campaign", build_payload_for_system(s)),
    "b2b_catalog_emails": lambda s: send_to_vabot(s, "b2b_catalog_emails", build_payload_for_system(s)),
    # fallback: direct forward
}

# -----------------------
# SCHEDULER
# -----------------------
class Scheduler(threading.Thread):
    def __init__(self, config: Dict[str,Any], poll_interval=30):
        super().__init__(daemon=True)
        self.config = config
        self.poll_interval = poll_interval
        self.systems = {s["id"]: s for s in config.get("systems", [])}
        self._stop = threading.Event()

    def schedule_initial_tasks(self):
        # create an initial scheduled task for each system based on frequency
        for s in self.config.get("systems", []):
            freq = s.get("frequency", "daily")
            run_at = next_run_from_frequency(freq)
            task = {
                "id": str(uuid.uuid4()),
                "system_id": s["id"],
                "action": s.get("marketing_action"),
                "scheduled_at": iso_now(),
                "run_at": run_at.isoformat(),
                "attempts": 0,
                "status": "pending",
                "payload": build_payload_for_system(s)
            }
            save_task(task)
            logger.info("Scheduled initial task for %s at %s", s["name"], task["run_at"])

    def run(self):
        logger.info("Scheduler started (poll_interval=%s)", self.poll_interval)
        # ensure there is at least one entry
        self.schedule_initial_tasks()
        while not self._stop.is_set():
            try:
                pending = fetch_pending(limit=20)
                if not pending:
                    time.sleep(self.poll_interval)
                    continue
                for t in pending:
                    # pick system
                    sys_def = self.systems.get(t["system_id"])
                    if not sys_def:
                        logger.warning("Unknown system_id %s for task %s", t["system_id"], t["id"])
                        mark_task_status(t["id"], "failed", "unknown system")
                        continue
                    # execute task
                    self.execute_task(sys_def, t)
                # small pause between batches
                time.sleep(1)
            except Exception as e:
                logger.exception("Scheduler loop error: %s", e)
                time.sleep(5)

    def execute_task(self, system: Dict[str,Any], task: Dict[str,Any]):
        logger.info("Executing task %s -> %s (%s)", task["id"], system["name"], task["action"])
        handler = ACTION_HANDLERS.get(task["action"])
        if not handler:
            logger.warning("No handler for action %s; marking failed", task["action"])
            mark_task_status(task["id"], "failed", f"no handler for action {task['action']}")
            return

        # attempt
        attempts = (task.get("attempts") or 0) + 1
        # call handler (which will call VA Bot)
        result = handler(system)
        code = result.get("code", 0)
        success = result.get("success", False)
        text = result.get("text", "")

        # log execution
        log_execution(task["id"], "success" if success else "failure", code, text)
        # update task in db
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now_iso = datetime.utcnow().isoformat()
        if success:
            c.execute("""
                UPDATE tasks SET status=?, attempts=?, last_error=?, run_at=?, run_at=?
                WHERE id=?
            """, ("done", attempts, None, now_iso, now_iso, task["id"]))
            conn.commit()
            conn.close()
            # schedule next run according to frequency
            next_run = next_run_from_frequency(system.get("frequency", "daily"))
            next_task = {
                "id": str(uuid.uuid4()),
                "system_id": system["id"],
                "action": system.get("marketing_action"),
                "scheduled_at": iso_now(),
                "run_at": next_run.isoformat(),
                "attempts": 0,
                "status": "pending",
                "payload": build_payload_for_system(system)
            }
            save_task(next_task)
            logger.info("Task %s succeeded; scheduled next run at %s", task["id"], next_task["run_at"])
        else:
            # failure -> decide retry policy
            backoff = min(60 * (2 ** (attempts - 1)), 3600)  # exponential backoff up to 1 hour
            retry_at = datetime.utcnow() + timedelta(seconds=backoff)
            c.execute("""
                UPDATE tasks SET attempts=?, status=?, last_error=?, run_at=? WHERE id=?
            """, (attempts, "retry", text[:1000], retry_at.isoformat(), task["id"]))
            conn.commit()
            conn.close()
            logger.warning("Task %s failed (code=%s). Will retry at %s", task["id"], code, retry_at.isoformat())

    def stop(self):
        self._stop.set()


# -----------------------
# HEALTH / METRICS (optional small HTTP server)
# -----------------------
def start_health_server(port=12000):
    # lightweight health check that returns JSON - uses Flask if available, otherwise simple socket server
    try:
        from flask import Flask, jsonify
        app = Flask("phase1_health")

        @app.route("/health", methods=["GET"])
        def health():
            return jsonify({
                "status": "ok",
                "worker_id": WORKER_ID,
                "time": iso_now()
            })

        def run_app():
            app.run(host="0.0.0.0", port=port)

        t = threading.Thread(target=run_app, daemon=True)
        t.start()
        logger.info("Health server started at /health on port %s", port)
    except Exception:
        logger.warning("Flask not available for health server; skipping")


# -----------------------
# BOOT
# -----------------------
def load_config(path=PHASE_CONFIG_PATH) -> Dict[str,Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Phase config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg


def main():
    logger.info("Phase1 Execution Core starting - worker id: %s", WORKER_ID)
    init_db()
    cfg = load_config()
    # optional: sanity check for systems
    systems = cfg.get("systems", [])
    if not systems:
        logger.error("No systems found in config - exiting")
        return

    # start health server (optional) on port 12000
    start_health_server(port=12000)

    # start scheduler
    sched = Scheduler(cfg, poll_interval=20)
    sched.start()

    # keep main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        sched.stop()
        sched.join()


if __name__ == "__main__":
    main()
