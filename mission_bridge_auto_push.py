# mission_bridge_auto_push.py
# Phase-1.3 : JRAVIS ↔ VA Bot ↔ Dashboard live bridge
# Run:  python mission_bridge_auto_push.py
# Deps: pip install requests schedule

import os, sqlite3, time, json, requests, schedule
from datetime import datetime

LIVE_FEED_URL = os.getenv("LIVE_FEED_URL", "http://localhost:3001/push")
LIVE_FEED_TOKEN = os.getenv("LIVE_FEED_TOKEN", "put_a_strong_token_here")
DB_PATH = os.getenv("DB_PATH", "./jravis_core.db")


def read_income_summary(conn):
    """Aggregate recent income totals by stream."""
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT stream, SUM(amount) 
            FROM income
            WHERE ts >= datetime('now', '-1 day')
            GROUP BY stream
        """)
        return [{"stream": s, "amount": a or 0} for s, a in cur.fetchall()]
    except Exception as e:
        print("[Bridge] income read error:", e)
        return []


def read_task_summary(conn):
    """Count VA Bot tasks by status."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
        rows = dict(cur.fetchall())
        return {
            "completed": rows.get("completed", 0),
            "pending": rows.get("pending", 0),
            "error": rows.get("error", 0)
        }
    except Exception as e:
        print("[Bridge] task read error:", e)
        return {}


def read_recent_logs(conn, limit=5):
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT ts, level, message FROM logs ORDER BY ts DESC LIMIT ?",
            (limit, ))
        return [{
            "ts": ts,
            "level": lvl,
            "message": msg
        } for ts, lvl, msg in cur.fetchall()]
    except Exception as e:
        print("[Bridge] log read error:", e)
        return []


def push_snapshot():
    try:
        conn = sqlite3.connect(DB_PATH)
        payload = {
            "type": "jravis_snapshot",
            "payload": {
                "income": read_income_summary(conn),
                "tasks": read_task_summary(conn),
                "logs": read_recent_logs(conn),
                "ts": datetime.utcnow().isoformat()
            }
        }
        conn.close()

        headers = {
            "x-live-token": LIVE_FEED_TOKEN,
            "Content-Type": "application/json"
        }
        r = requests.post(LIVE_FEED_URL,
                          data=json.dumps(payload),
                          headers=headers,
                          timeout=10)
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] snapshot pushed — status {r.status_code}"
        )
    except Exception as e:
        print("[Bridge] push error:", e)


# Run every 3 minutes
schedule.every(3).minutes.do(push_snapshot)

print("[Bridge] Auto-push bridge active 🚀")
print("Pushing JRAVIS + VA Bot snapshots every 3 minutes…")

push_snapshot()  # first immediate push
while True:
    schedule.run_pending()
    time.sleep(10)
