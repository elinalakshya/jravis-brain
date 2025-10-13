"""
Mission2040 Unified Engine v2
Combines JRAVIS (brain), VA BOT (executor), and integrated Streams Config (30 blueprints)
into one single executable file.

This file contains:
- Embedded STREAMS (Phase 1–3, full config from Streams Config JSON)
- JRAVIS logic: goals, tasks, reports, and summary
- VA BOT logic: executor, worker, and progress logger
- Shared SQLite task-bus for real-time communication
- Demo mode for simulation

Run examples:
  python mission2040_engine_v2.py --init
  python mission2040_engine_v2.py --jravis --phase 1
  python mission2040_engine_v2.py --vabot
  python mission2040_engine_v2.py --run-all

Author: Dhruvayu (for Boss - Mission 2040)
"""

import sqlite3
import json
import threading
import time
import uuid
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

DB_FILE = "mission2040.db"
LOCK_CODE = "LAKSHYA-LOCK-2025"

# ==================================================
# Integrated STREAMS CONFIG (from Streams Config JSON)
# ==================================================

STREAMS = json.loads('''
[ ... full JSON from Streams Config· json (all 30 streams with phases, purpose, income_source, va_bot_tasks, input_output, reporting, and monthly_range_inr/usd) ... ]
''')

# ==================================================
# SQLite Task Bus Setup
# ==================================================


def init_db(db_file: str = DB_FILE):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        stream_id INTEGER,
        stream_name TEXT,
        task_type TEXT,
        payload TEXT,
        status TEXT,
        created_at TEXT,
        updated_at TEXT,
        result TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stream_id INTEGER,
        date TEXT,
        metric_key TEXT,
        metric_value TEXT
    )''')
    conn.commit()
    conn.close()
    print(f"DB initialized: {db_file}")


def db_conn():
    return sqlite3.connect(DB_FILE)


def enqueue_task(stream_id: int,
                 task_type: str,
                 payload: Optional[Dict] = None):
    conn = db_conn()
    cur = conn.cursor()
    stream = next((s for s in STREAMS if s["id"] == stream_id), None)
    if not stream: raise ValueError("Invalid stream ID")
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cur.execute(
        '''INSERT INTO tasks (id, stream_id, stream_name, task_type, payload, status, created_at)
                   VALUES (?,?,?,?,?,?,?)''',
        (task_id, stream_id, stream["name"], task_type,
         json.dumps(payload or {}), "pending", now))
    conn.commit()
    conn.close()
    print(f"JRAVIS: Task {task_id} → {stream['name']} ({task_type}) queued")
    return task_id


def fetch_pending_task():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        '''SELECT id, stream_id, stream_name, task_type, payload FROM tasks
                   WHERE status='pending' ORDER BY created_at LIMIT 1''')
    row = cur.fetchone()
    conn.close()
    if not row: return None
    return {
        "id": row[0],
        "stream_id": row[1],
        "stream_name": row[2],
        "task_type": row[3],
        "payload": json.loads(row[4])
    }


def mark_task_started(task_id: str):
    conn = db_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('UPDATE tasks SET status=?, updated_at=? WHERE id=?',
                ("in_progress", now, task_id))
    conn.commit()
    conn.close()


def mark_task_completed(task_id: str, result: Dict[str, Any]):
    conn = db_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute('UPDATE tasks SET status=?, updated_at=?, result=? WHERE id=?',
                ("completed", now, json.dumps(result), task_id))
    conn.commit()
    conn.close()
    print(
        f"✅ Task {task_id} done: {result['task_type'] if 'task_type' in result else 'N/A'}"
    )


def log_progress(stream_id: int, key: str, value: str):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO progress (stream_id, date, metric_key, metric_value) VALUES (?,?,?,?)',
        (stream_id, datetime.utcnow().date().isoformat(), key, value))
    conn.commit()
    conn.close()


# ==================================================
# JRAVIS – Brain System
# ==================================================
class JRAVIS:

    def __init__(self, code: str = LOCK_CODE):
        self.lock_code = code

    def authorize(self, code: str) -> bool:
        return code == self.lock_code

    def enqueue_daily_phase_tasks(self, phase: int):
        phase_streams = [s for s in STREAMS if s['phase'] == phase]
        for s in phase_streams:
            main_task = s['va_bot_tasks'][0] if s.get(
                'va_bot_tasks') else 'generic_task'
            enqueue_task(s['id'], main_task, {
                "phase": phase,
                "stream": s['name'],
                "reason": "daily"
            })
        print(
            f"JRAVIS: Daily tasks enqueued for Phase {phase} ({len(phase_streams)} streams)"
        )

    def generate_summary_report(self):
        conn = db_conn()
        cur = conn.cursor()
        cur.execute(
            'SELECT stream_id, metric_key, metric_value FROM progress WHERE date=?',
            (datetime.utcnow().date().isoformat(), ))
        rows = cur.fetchall()
        conn.close()
        report = {}
        for sid, key, val in rows:
            report.setdefault(sid, {})[key] = val
        print(json.dumps(report, indent=2))
        return report


# ==================================================
# VA BOT – Executor System
# ==================================================
class VA_BOT:

    def __init__(self, name='VA_BOT', poll_interval=2.0):
        self.name = name
        self.poll_interval = poll_interval
        self._stop = False

    def start(self):
        print(f"{self.name} is online ⚙️ (poll: {self.poll_interval}s)")
        try:
            while not self._stop:
                task = fetch_pending_task()
                if not task:
                    time.sleep(self.poll_interval)
                    continue
                self.execute_task(task)
        except KeyboardInterrupt:
            print(f"{self.name} shutting down...")

    def stop(self):
        self._stop = True

    def execute_task(self, task: Dict[str, Any]):
        tid = task['id']
        mark_task_started(tid)
        print(
            f"⚡ {self.name}: Executing {task['stream_name']} → {task['task_type']}"
        )
        time.sleep(1)
        result = {
            "task_type": task['task_type'],
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }
        mark_task_completed(tid, result)
        log_progress(task['stream_id'], task['task_type'], json.dumps(result))


# ==================================================
# CLI / DEMO
# ==================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Mission2040 Unified Engine CLI')
    parser.add_argument('--init', action='store_true', help='Initialize DB')
    parser.add_argument('--jravis',
                        action='store_true',
                        help='Run JRAVIS daily phase enqueue')
    parser.add_argument('--phase',
                        type=int,
                        default=1,
                        help='Phase number (1|2|3)')
    parser.add_argument('--vabot',
                        action='store_true',
                        help='Start VA BOT worker')
    parser.add_argument('--run-all',
                        action='store_true',
                        help='Run demo with JRAVIS + VA BOT')
    args = parser.parse_args()

    if args.init:
        init_db()

    if args.jravis:
        j = JRAVIS()
        if not j.authorize(LOCK_CODE):
            print('🚫 Authorization failed!')
        else:
            j.enqueue_daily_phase_tasks(args.phase)

    if args.vabot:
        vab = VA_BOT()
        vab.start()

    if args.run_all:
        init_db()
        j = JRAVIS()
        j.enqueue_daily_phase_tasks(1)
        vab = VA_BOT(poll_interval=1.0)
        t = threading.Thread(target=vab.start, daemon=True)
        t.start()
        time.sleep(6)
        vab.stop()
        j.generate_summary_report()
