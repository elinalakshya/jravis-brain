# db.py
import sqlite3
from datetime import datetime
import os

DB = os.path.join(os.getcwd(), "phase2.db")


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS streams (
        id TEXT PRIMARY KEY,
        name TEXT,
        amount REAL,
        currency TEXT,
        last_updated TEXT
    )""")
    conn.commit()
    conn.close()


def upsert_stream_earnings(id, name, amount, currency="USD"):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO streams (id,name,amount,currency,last_updated) VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, amount=excluded.amount, currency=excluded.currency, last_updated=excluded.last_updated",
        (id, name, amount, currency, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_streams():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT id,name,amount,currency,last_updated FROM streams ORDER BY name"
    )
    rows = cur.fetchall()
    conn.close()
    streams = [{
        "id": r[0],
        "name": r[1],
        "amount": r[2],
        "currency": r[3],
        "last_updated": r[4]
    } for r in rows]
    return streams


# convenience wrapper
def get_streams_wrapper():
    return get_streams()
