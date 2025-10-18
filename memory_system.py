# memory_system.py
"""
JRAVIS Memory System — Mission 2040
-----------------------------------
Persistent lightweight memory for income tracking, system logs, and reports.
Stores daily summaries, earnings, and activity using TinyDB.
"""

from tinydb import TinyDB, Query
from datetime import datetime
import os, json

DB_PATH = os.getenv("JRAVIS_MEMORY_DB", "memory_data.json")
db = TinyDB(DB_PATH)
memory_table = db.table("memory")
activity_table = db.table("activity")


def log_event(event: str, category="general"):
    """Record an event or activity"""
    entry = {
        "time": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "category": category
    }
    activity_table.insert(entry)
    print(f"[Memory] {event}")


def save_income_summary(data: dict):
    """Save or update daily income snapshot"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    record = {
        "date": today,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": data
    }
    # Remove existing record for today
    memory_table.remove(Query().date == today)
    memory_table.insert(record)
    log_event(f"Income summary updated: {data}")


def get_income_history(limit=7):
    """Return last N days of stored income"""
    all_data = sorted(memory_table.all(),
                      key=lambda x: x["date"],
                      reverse=True)
    return [r["data"] for r in all_data[:limit]]


def get_activity_log(limit=10):
    """Return last N activity entries"""
    all_logs = sorted(activity_table.all(),
                      key=lambda x: x["time"],
                      reverse=True)
    return all_logs[:limit]


def export_full_memory():
    """Return full memory snapshot"""
    return {
        "income_history": get_income_history(30),
        "recent_activity": get_activity_log(50)
    }
