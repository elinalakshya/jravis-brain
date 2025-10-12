# va_bot_api_additions.py
import os, threading, time, sqlite3, json, requests, traceback
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
DB = os.environ.get('VADB_PATH', './vabot_tasks.db')
SHARED_KEY = os.environ.get('SHARED_KEY', 'change-this-securely')
JRAVIS_URL = os.environ.get('JRAVIS_URL',
                            'https://your-jravis-url.com').rstrip('/')
MAX_WORKER_THREADS = int(os.environ.get('VABOT_WORKERS', 3))

ALLOWED_TASKS = {"start_stream", "stop_stream", "collect_report", "run_phase"}
DB_CONN = None
DB_LOCK = threading.Lock()


def now():
    return datetime.utcnow().isoformat() + 'Z'


def init_db():
    global DB_CONN
    DB_CONN = sqlite3.connect(DB, check_same_thread=False)
    c = DB_CONN.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, inbound_json TEXT, status TEXT, tries INTEGER, created_at TEXT, updated_at TEXT, last_error TEXT)'''
              )
    DB_CONN.commit()


init_db()


def authenticate_request(flask_req):
    auth = flask_req.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        return token == SHARED_KEY
    return False


@app.route('/api/receive_task', methods=['POST'])
def receive_task():
    if not authenticate_request(request):
        return jsonify({'error': 'unauthorized'}), 401
    task = request.json or {}
    action = task.get('action')
    if action not in ALLOWED_TASKS:
        return jsonify({'error': 'invalid action'}), 400
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "INSERT INTO tasks (inbound_json, status, tries, created_at, updated_at) VALUES (?,?,?,?,?)",
            (json.dumps(task), 'queued', 0, now(), now()))
        DB_CONN.commit()
        tid = c.lastrowid
    return jsonify({'status': 'accepted', 'task_id': tid}), 200


def get_next_task():
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "SELECT id, inbound_json, status, tries FROM tasks WHERE status='queued' ORDER BY id LIMIT 1"
        )
        return c.fetchone()


def update_task(id, status, tries=None, last_error=None):
    with DB_LOCK:
        c = DB_CONN.cursor()
        if tries is None:
            c.execute(
                "UPDATE tasks SET status=?, updated_at=?, last_error=? WHERE id=?",
                (status, now(), last_error, id))
        else:
            c.execute(
                "UPDATE tasks SET status=?, tries=?, updated_at=?, last_error=? WHERE id=?",
                (status, tries, now(), last_error, id))
        DB_CONN.commit()


def send_status_to_jravis(payload):
    url = JRAVIS_URL.rstrip(
        '/'
    ) + '/api/vabot_status'  # create this endpoint in JRAVIS to receive callbacks
    headers = {
        'Authorization': f'Bearer {SHARED_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)


# Worker that executes tasks (implement platform-specific logic where indicated)
def worker_loop():
    while True:
        try:
            row = get_next_task()
            if not row:
                time.sleep(1)
                continue
            tid, inbound_json, status, tries = row
            task = json.loads(inbound_json)
            action = task.get('action')
            # mark running
            update_task(tid, 'running', tries + 1, None)
            # Execute action (placeholder - replace with real platform calls using existing API keys)
            try:
                # Example execution flow:
                if action == 'start_stream':
                    # call platform APIs using stored keys, e.g., Printify / Instagram posting
                    # simulate work:
                    time.sleep(2)
                    result = {
                        'ok': True,
                        'details': f"Started stream {task.get('stream')}"
                    }
                elif action == 'collect_report':
                    # gather report, compute earnings
                    time.sleep(1)
                    result = {'ok': True, 'earnings': 1234.0}
                else:
                    time.sleep(1)
                    result = {'ok': True, 'info': 'performed ' + action}

                update_task(tid, 'done', tries + 1, None)
                payload = {
                    'task_id': tid,
                    'status': 'done',
                    'result': result,
                    'task': task,
                    'timestamp': now()
                }
                send_status_to_jravis(payload)
            except Exception as ex:
                tries += 1
                if tries >= 5:
                    update_task(tid, 'failed', tries, str(ex))
                    payload = {
                        'task_id': tid,
                        'status': 'failed',
                        'error': str(ex),
                        'task': task,
                        'timestamp': now()
                    }
                else:
                    update_task(tid, 'queued', tries, str(ex))
                    payload = {
                        'task_id': tid,
                        'status': 'retry',
                        'error': str(ex),
                        'task': task,
                        'timestamp': now()
                    }
                send_status_to_jravis(payload)
        except Exception as e:
            print("VA Bot worker exception:", e)
            traceback.print_exc()
            time.sleep(3)


def start_workers(n=1):
    for _ in range(n):
        t = threading.Thread(target=worker_loop, daemon=True)
        t.start()


# Minimal endpoints for health and control
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'time': now()}), 200


# Example control endpoint to list tasks (for debugging)
@app.route('/api/list_tasks', methods=['GET'])
def list_tasks():
    with DB_LOCK:
        c = DB_CONN.cursor()
        c.execute(
            "SELECT id, inbound_json, status, tries, created_at, updated_at FROM tasks ORDER BY id DESC LIMIT 200"
        )
        rows = c.fetchall()
        out = []
        for r in rows:
            out.append({
                'id': r[0],
                'task': json.loads(r[1]),
                'status': r[2],
                'tries': r[3],
                'created_at': r[4],
                'updated_at': r[5]
            })
    return jsonify(out), 200


if __name__ == '__main__':
    # set up workers
    start_workers(MAX_WORKER_THREADS)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
