#!/usr/bin/env python3
import os
import sqlite3
import json
from flask import Flask, request, redirect, render_template_string, session, jsonify
from datetime import datetime

# ---------- CONFIG ----------
LOCK_CODE = os.getenv("LOCK_CODE", "LakshyaSecureCode@2040")
FLASK_SECRET = os.getenv("DASHBOARD_SECRET", "JRAVIS@Mission2040")
DB_PATH = os.getenv("DB_PATH", "dashboard.db")  # dashboard orders DB
PHASE1_DB = os.getenv("PHASE1_DB_PATH",
                      "phase1_exec.db")  # phase1 execution DB (worker)
app = Flask(__name__)
app.secret_key = FLASK_SECRET


# ---------- DB INIT (dashboard orders) ----------
def init_dashboard_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stream TEXT,
        amount REAL,
        currency TEXT DEFAULT 'INR',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)
    conn.commit()
    conn.close()


init_dashboard_db()

# ---------- TEMPLATES ----------
HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>JRAVIS — Live Dashboard</title>
  <style>
    body{font-family:Inter,Arial;margin:28px;background:#071027;color:#eaf6ff}
    h1{color:#5be7ff} .card{background:#081428;padding:16px;border-radius:8px;margin-bottom:12px}
    table{width:100%;border-collapse:collapse;margin-top:12px}
    th,td{padding:8px;border-bottom:1px solid #102135;text-align:left}
    th{color:#9fdcff}
    .small{font-size:0.9rem;color:#9fb6c9}
  </style>
</head>
<body>
  <h1>JRAVIS Command Console — Mission 2040</h1>
  <div class="card">
    <div><strong>Total Revenue (dashboard)</strong></div>
    <div style="font-size:1.6rem">₹ {{ total_revenue }}</div>
    <div class="small">Total Orders: {{ total_orders }}</div>
  </div>

  <div class="card">
    <div><strong>Phase-1 Worker Metrics (live)</strong></div>
    <div class="small">Last scheduler sync: {{ last_sync }}</div>
    <table>
      <thead><tr><th>System</th><th>Success</th><th>Failures</th><th>Last Success</th></tr></thead>
      <tbody>
        {% for s in systems %}
        <tr>
          <td>{{ s.name }}</td>
          <td>{{ s.success }}</td>
          <td>{{ s.failure }}</td>
          <td>{{ s.last_success or '-' }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <div><strong>Recent Orders (dashboard)</strong></div>
    <table>
      <thead><tr><th>Stream</th><th>Amount</th><th>Currency</th><th>Date</th></tr></thead>
      <tbody>
        {% for o in orders %}
        <tr><td>{{ o[1] }}</td><td>₹ {{ o[2] }}</td><td>{{ o[3] }}</td><td>{{ o[4] }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="small">Last updated: {{ now }}</div>
  <div style="margin-top:12px"><a href="/lockout" style="color:#9fdcff">Lock dashboard</a></div>
</body>
</html>
"""


# ---------- HELPERS: Phase1 DB read ----------
def read_phase1_metrics(db_path=PHASE1_DB):
    """
    Returns a list of system metrics:
      [{name, success, failure, last_success}, ...]
    Uses exec_log + tasks tables if available.
    """
    if not os.path.exists(db_path):
        return [], None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Try to join exec_log -> tasks to compute per-system stats.
    try:
        # We expect tasks.payload to be JSON (string) with system metadata OR system_id
        q = """
        SELECT t.system_id, t.payload, el.status, el.timestamp
        FROM exec_log el
        LEFT JOIN tasks t ON el.task_id = t.id
        ORDER BY el.timestamp DESC
        """
        c.execute(q)
        rows = c.fetchall()
    except Exception:
        conn.close()
        return [], None

    # aggregate
    agg = {}
    last_sync = None
    for r in rows:
        payload_raw = r["payload"] or "{}"
        try:
            payload = json.loads(payload_raw)
            sys_name = payload.get(
                "system",
                {}).get("name") or f"system-{r['system_id'] or 'unknown'}"
        except Exception:
            sys_name = f"system-{r['system_id'] or 'unknown'}"

        if sys_name not in agg:
            agg[sys_name] = {"success": 0, "failure": 0, "last_success": None}
        if r["status"] and r["status"].lower().startswith("success"):
            agg[sys_name]["success"] += 1
            agg[sys_name]["last_success"] = agg[sys_name]["last_success"] or r[
                "timestamp"]
            if not last_sync:
                last_sync = r["timestamp"]
        else:
            agg[sys_name]["failure"] += 1
            if not last_sync:
                last_sync = r["timestamp"]

    conn.close()
    systems = []
    for name, vals in agg.items():
        systems.append({
            "name": name,
            "success": vals["success"],
            "failure": vals["failure"],
            "last_success": vals["last_success"]
        })
    # ensure deterministic order
    systems = sorted(systems, key=lambda x: (-x["success"], x["name"]))
    return systems, last_sync


# ---------- HELPERS: Dashboard orders ----------
def read_orders_summary(db_path=DB_PATH, limit=50):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), IFNULL(SUM(amount),0) FROM orders")
    total_orders, total_revenue = c.fetchone()
    c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?",
              (limit, ))
    recent = c.fetchall()
    conn.close()
    return int(total_orders or 0), float(total_revenue or 0.0), recent


# ---------- AUTH (lock) ----------
@app.before_request
def require_unlock():
    if request.endpoint in ("unlock", "static", "health", "api_metrics"):
        return None
    if not session.get("unlocked"):
        return redirect("/unlock")


@app.route("/unlock", methods=["GET", "POST"])
def unlock():
    if request.method == "POST":
        code = request.form.get("code", "")
        if code == LOCK_CODE:
            session["unlocked"] = True
            return redirect("/")
        return "<h3>Invalid code</h3><a href='/unlock'>Try again</a>"
    return """
    <html><body style="font-family:Arial;background:#071027;color:#eaf6ff;text-align:center;padding-top:80px;">
      <h2>🔒 JRAVIS Dashboard Locked</h2>
      <form method="post">
        <input name="code" placeholder="Enter lock code" type="password" style="padding:8px;margin:8px" />
        <button type="submit" style="padding:8px 14px">Unlock</button>
      </form>
    </body></html>
    """


@app.route("/lockout")
def lockout():
    session.clear()
    return redirect("/unlock")


# ---------- HEALTH & METRICS ----------
@app.route("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.route("/api/metrics")
def api_metrics():
    total_orders, total_revenue, recent = read_orders_summary()
    systems, last_sync = read_phase1_metrics()
    return jsonify({
        "orders":
        total_orders,
        "revenue":
        total_revenue,
        "recent_orders": [{
            "id": r[0],
            "stream": r[1],
            "amount": r[2],
            "created_at": r[4]
        } for r in recent],
        "systems":
        systems,
        "last_sync":
        last_sync
    })


# ---------- ROOT DASHBOARD ----------
@app.route("/")
def root():
    total_orders, total_revenue, recent = read_orders_summary()
    systems, last_sync = read_phase1_metrics()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return render_template_string(HTML,
                                  total_revenue=f"{total_revenue:,.2f}",
                                  total_orders=total_orders,
                                  orders=recent,
                                  systems=systems,
                                  last_sync=last_sync or "N/A",
                                  now=now)


# ---------- BOOT ----------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"[JRAVIS] Dashboard starting on port {port}")
    app.run(host="0.0.0.0", port=port)
