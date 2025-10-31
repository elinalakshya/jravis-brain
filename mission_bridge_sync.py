# mission_bridge_sync.py
# Run: python mission_bridge_sync.py
# pip install requests

import sqlite3
import time
import json
import os
import requests
from datetime import datetime, timedelta

LIVE_FEED_URL = os.getenv('LIVE_FEED_URL', 'http://localhost:3001/push')
LIVE_FEED_TOKEN = os.getenv('LIVE_FEED_TOKEN', 'supersecret_token_change_this')
DB_PATH = os.getenv('DB_PATH', './jravis_core.db')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '15'))  # seconds


def get_latest_income(conn, since_minutes=60):
    """
    Example: table 'income' with columns (id, ts, stream, amount)
    If your table name/columns differ, adjust the SQL.
    """
    since_ts = (datetime.utcnow() -
                timedelta(minutes=since_minutes)).isoformat()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT stream, sum(amount) as total_amount FROM income WHERE ts >= ? GROUP BY stream",
            (since_ts, ))
        rows = cur.fetchall()
        return [{'stream': r[0], 'amount': r[1]} for r in rows]
    except sqlite3.OperationalError:
        return []


def get_tasks_summary(conn):
    """
    Example: table 'tasks' with (id, ts, desc, status)
    returns counts by status.
    """
    cur = conn.cursor()
    try:
        cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
        rows = cur.fetchall()
        return {r[0]: r[1] for r in rows}
    except sqlite3.OperationalError:
        return {}


def get_recent_logs(conn, limit=20):
    """
    Example: table 'logs' with (id, ts, level, message)
    """
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT ts, level, message FROM logs ORDER BY ts DESC LIMIT ?",
            (limit, ))
        return [{
            'ts': r[0],
            'level': r[1],
            'message': r[2]
        } for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return []


def send_payload(payload):
    headers = {
        'Content-Type': 'application/json',
        'x-live-token': LIVE_FEED_TOKEN
    }
    try:
        resp = requests.post(LIVE_FEED_URL,
                             json=payload,
                             headers=headers,
                             timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print("Send error:", e)
        return False


def main_loop():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    print("Bridge started, reading DB:", DB_PATH)
    while True:
        try:
            income = get_latest_income(conn, since_minutes=60)
            tasks = get_tasks_summary(conn)
            logs = get_recent_logs(conn, limit=10)

            payload = {
                'type': 'jravis_snapshot',
                'payload': {
                    'income': income,
                    'tasks': tasks,
                    'logs': logs,
                    'ts': datetime.utcnow().isoformat()
                }
            }

            ok = send_payload(payload)
            print(
                f"[{datetime.utcnow().isoformat()}] pushed snapshot — ok={ok}")
        except Exception as e:
            print('Bridge loop error:', e)
        time.sleep(POLL_INTERVAL)


{
    "type": "jravis_snapshot",
    "payload": {
        "income": [{
            "stream": "Printify",
            "amount": 230.5
        }, {
            "stream": "Etsy",
            "amount": 129.9
        }],
        "tasks": {
            "completed": 18,
            "pending": 3,
            "error": 1
        }
    }
}

if __name__ == '__main__':
    main_loop()
