# mission_bridge.py

```python
"""
mission_bridge.py

Shared bridge module used by JRAVIS and VA_BOT.
Implements a simple SQLite-backed task-bus and progress logging API.

Usage (import from other modules):
    from mission_bridge import Bridge
    bridge = Bridge(db_path='mission2040.db')
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List


class Bridge:
    def __init__(self, db_path: str = 'mission2040.db'):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def _init_db(self):
        conn = self._conn(); cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                stream_id INTEGER,
                stream_name TEXT,
                task_type TEXT,
                payload TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT,
                result TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_id INTEGER,
                date TEXT,
                metric_key TEXT,
                metric_value TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                level TEXT,
                message TEXT
            )
        ''')
        conn.commit(); conn.close()

    # -------- Task bus APIs --------
    def enqueue_task(self, task_id: str, stream_id: int, stream_name: str, task_type: str, payload: Optional[Dict]=None) -> None:
        conn = self._conn(); cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute('INSERT INTO tasks (id, stream_id, stream_name, task_type, payload, status, created_at) VALUES (?,?,?,?,?,?,?)',
                    (task_id, stream_id, stream_name, task_type, json.dumps(payload or {}), 'pending', now))
        conn.commit(); conn.close()

    def fetch_pending_task(self) -> Optional[Dict[str,Any]]:
        conn = self._conn(); cur = conn.cursor()
        cur.execute("SELECT id, stream_id, stream_name, task_type, payload FROM tasks WHERE status='pending' ORDER BY created_at LIMIT 1")
        row = cur.fetchone(); conn.close()
        if not row:
            return None
        return {"id": row[0], "stream_id": row[1], "stream_name": row[2], "task_type": row[3], "payload": json.loads(row[4] or '{}')}

    def mark_task_started(self, task_id: str) -> None:
        conn = self._conn(); cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute('UPDATE tasks SET status=?, updated_at=? WHERE id=?', ('in_progress', now, task_id))
        conn.commit(); conn.close()

    def mark_task_completed(self, task_id: str, result: Dict[str,Any]) -> None:
        conn = self._conn(); cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute('UPDATE tasks SET status=?, updated_at=?, result=? WHERE id=?', ('completed', now, json.dumps(result), task_id))
        conn.commit(); conn.close()

    def list_tasks(self, status: Optional[str]=None, limit: int=100) -> List[Dict[str,Any]]:
        conn = self._conn(); cur = conn.cursor()
        if status:
            cur.execute('SELECT id, stream_id, stream_name, task_type, status, created_at, updated_at FROM tasks WHERE status=? ORDER BY created_at DESC LIMIT ?', (status, limit))
        else:
            cur.execute('SELECT id, stream_id, stream_name, task_type, status, created_at, updated_at FROM tasks ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cur.fetchall(); conn.close()
        out = []
        for r in rows:
            out.append({"id": r[0], "stream_id": r[1], "stream_name": r[2], "task_type": r[3], "status": r[4], "created_at": r[5], "updated_at": r[6]})
        return out

    # -------- Progress / reporting API --------
    def log_progress(self, stream_id: int, key: str, value: str, date: Optional[str]=None) -> None:
        conn = self._conn(); cur = conn.cursor()
        date = date or datetime.utcnow().date().isoformat()
        cur.execute('INSERT INTO progress (stream_id, date, metric_key, metric_value) VALUES (?,?,?,?)', (stream_id, date, key, value))
        conn.commit(); conn.close()

    def get_progress(self, date: Optional[str]=None) -> List[Dict[str,Any]]:
        conn = self._conn(); cur = conn.cursor()
        date = date or datetime.utcnow().date().isoformat()
        cur.execute('SELECT stream_id, metric_key, metric_value FROM progress WHERE date=?', (date,))
        rows = cur.fetchall(); conn.close()
        return [{"stream_id": r[0], "metric_key": r[1], "metric_value": r[2]} for r in rows]

    # -------- Logging --------
    def write_log(self, level: str, message: str) -> None:
        conn = self._conn(); cur = conn.cursor()
        cur.execute('INSERT INTO logs (ts, level, message) VALUES (?,?,?)', (datetime.utcnow().isoformat(), level, message))
        conn.commit(); conn.close()

    def read_logs(self, limit: int=100) -> List[Dict[str,Any]]:
        conn = self._conn(); cur = conn.cursor()
        cur.execute('SELECT ts, level, message FROM logs ORDER BY id DESC LIMIT ?', (limit,))
        rows = cur.fetchall(); conn.close()
        return [{"ts": r[0], "level": r[1], "message": r[2]} for r in rows]
```

---