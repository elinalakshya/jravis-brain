# mission_bridge_auto_push_secure.py
# pip install cryptography requests
import os, json, time, sqlite3, requests, hmac, hashlib, base64
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

LIVE_FEED_URL = os.getenv('LIVE_FEED_URL', 'http://localhost:3001/push')
MASTER_KEY = os.getenv('MASTER_KEY', '')  # must match server MASTER_KEY
DB_PATH = os.getenv('DB_PATH', './jravis_core.db')

if not MASTER_KEY:
    raise SystemExit('Set MASTER_KEY in env')


def rotating_token_for_date(dt):
    # dt is a datetime.date or date-like formatted as YYYY-MM-DD
    hm = hmac.new(MASTER_KEY.encode(), dt.encode(), hashlib.sha256).digest()
    # base64 urlsafe without padding
    return base64.urlsafe_b64encode(hm).decode().rstrip('=')


def current_rotating_token():
    utc_today = datetime.utcnow().strftime('%Y-%m-%d')
    return rotating_token_for_date(utc_today)


def derive_aes_key():
    # derive 32-byte key deterministically
    return hashlib.sha256(MASTER_KEY.encode()).digest()


def encrypt_payload_json(obj):
    key = derive_aes_key()
    aesgcm = AESGCM(key)
    iv = os.urandom(12)  # 96-bit nonce recommended for GCM
    plaintext = json.dumps(obj).encode('utf-8')
    ct = aesgcm.encrypt(iv, plaintext,
                        None)  # returns ciphertext+tag concatenated
    # cryptography returns ciphertext||tag (tag is 16 bytes at end)
    tag = ct[-16:]
    cipher = ct[:-16]
    return {
        'cipher': base64.urlsafe_b64encode(cipher).decode().rstrip('='),
        'iv': base64.urlsafe_b64encode(iv).decode().rstrip('='),
        'tag': base64.urlsafe_b64encode(tag).decode().rstrip('=')
    }


def read_income_summary(conn):
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT stream, SUM(amount) FROM income WHERE ts >= datetime('now', '-1 day') GROUP BY stream"
        )
        return [{'stream': r[0], 'amount': r[1] or 0} for r in cur.fetchall()]
    except Exception:
        return []


def read_task_summary(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
        rows = dict(cur.fetchall())
        return {
            'completed': rows.get('completed', 0),
            'pending': rows.get('pending', 0),
            'error': rows.get('error', 0)
        }
    except Exception:
        return {}


def read_recent_logs(conn, limit=5):
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ts, level, message FROM logs ORDER BY ts DESC LIMIT ?",
            (limit, ))
        return [{
            'ts': r[0],
            'level': r[1],
            'message': r[2]
        } for r in cur.fetchall()]
    except Exception:
        return []


def push_snapshot():
    conn = sqlite3.connect(DB_PATH)
    payload = {
        'type': 'jravis_snapshot',
        'payload': {
            'income': read_income_summary(conn),
            'tasks': read_task_summary(conn),
            'logs': read_recent_logs(conn),
            'ts': datetime.utcnow().isoformat()
        }
    }
    conn.close()

    enc = encrypt_payload_json(payload)
    headers = {
        'x-live-token': current_rotating_token(),
        'x-live-encrypted': '1',
        'Content-Type': 'application/json'
    }
    body = json.dumps(enc)
    r = requests.post(LIVE_FEED_URL, data=body, headers=headers, timeout=10)
    print(
        f"[{datetime.utcnow().strftime('%H:%M:%S')}] push status {r.status_code}"
    )


if __name__ == '__main__':
    # initial immediate push
    push_snapshot()
    # then loop every 180 seconds
    while True:
        time.sleep(180)
        push_snapshot()
