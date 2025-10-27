#!/usr/bin/env python3
import os, sqlite3, json
from datetime import datetime
from flask import Flask, request, redirect, session, render_template_string, jsonify

# ---------------- CONFIG ----------------
LOCK_CODE = os.getenv("LOCK_CODE", "LakshyaSecureCode@2040")
FLASK_SECRET = os.getenv("DASHBOARD_SECRET", "JRAVIS@Mission2040")
DB_PATH = os.getenv("DB_PATH", "dashboard.db")
PHASE1_DB = os.getenv("PHASE1_DB_PATH", "phase1_exec.db")

app = Flask(__name__)
app.secret_key = FLASK_SECRET


# ---------------- INIT DATABASE ----------------
def init_db():
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


init_db()

# ---------------- HTML TEMPLATE (Neon Theme) ----------------
HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>JRAVIS Dashboard v6 — Mission 2040</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#030712] text-gray-100 font-sans p-6">

  <div class="max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-cyan-400">JRAVIS DASHBOARD v6 — PHASE 1 GLOBAL STATUS</h1>
      <form action="/lockout"><button class="bg-gray-800 px-4 py-2 rounded text-cyan-300 hover:bg-gray-700">Lock</button></form>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="bg-[#0B1320] p-4 rounded-lg border border-cyan-900">
        <h2 class="text-xl font-semibold text-cyan-300 mb-2">JRAVIS BRAIN</h2>
        <p>Status: <span class="text-green-400 font-semibold">ACTIVE</span></p>
        <p>Last Sync: {{ last_sync or 'N/A' }}</p>
        <p>API Ping: <span class="text-cyan-400">200 OK</span></p>
      </div>

      <div class="bg-[#0B1320] p-4 rounded-lg border border-cyan-900 text-center">
        <h2 class="text-xl font-semibold text-cyan-300 mb-2">INCOME</h2>
        <div class="text-3xl font-bold text-green-400">₹{{ total_revenue }}</div>
        <p class="text-gray-400">Total Orders: {{ total_orders }}</p>
      </div>

      <div class="bg-[#0B1320] p-4 rounded-lg border border-cyan-900 text-center">
        <h2 class="text-xl font-semibold text-cyan-300 mb-2">TARGET PROGRESS</h2>
        <div class="w-full bg-gray-800 rounded-full h-3 mb-2">
          <div class="bg-cyan-500 h-3 rounded-full" style="width: {{ progress }}%;"></div>
        </div>
        <p class="text-gray-400">{{ progress }}% of target (₹{{ target }})</p>
      </div>
    </div>

    <div class="bg-[#0B1320] p-4 rounded-lg border border-cyan-900 mb-6">
      <h2 class="text-xl font-semibold text-cyan-300 mb-4">PHASE 1 — SYSTEM STATUS</h2>
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-cyan-900 text-cyan-400">
            <th class="py-2">#</th>
            <th>Stream Name</th>
            <th>Last Run</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {% for s in systems %}
          <tr class="border-b border-gray-800 hover:bg-gray-900">
            <td class="py-2">{{ loop.index }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.last_success or '—' }}</td>
            <td>
              {% if s.success > 0 %}
                <span class="text-green-400">✔ OK</span>
              {% else %}
                <span class="text-yellow-400">RUNNING</span>
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <div class="bg-[#0B1320] p-4 rounded-lg border border-cyan-900">
      <h2 class="text-xl font-semibold text-cyan-300 mb-4">RECENT ORDERS</h2>
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b border-cyan-900 text-cyan-400">
            <th>Stream</th><th>Amount (₹)</th><th>Currency</th><th>Date</th>
          </tr>
        </thead>
        <tbody>
          {% for o in orders %}
          <tr class="border-b border-gray-800 hover:bg-gray-900">
            <td class="py-1">{{ o[1] }}</td>
            <td>{{ o[2] }}</td>
            <td>{{ o[3] }}</td>
            <td>{{ o[4] }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <div class="text-gray-500 text-sm text-center mt-6">
      JRAVIS Assistant online • Updated {{ now }}
    </div>
  </div>

</body>
</html>
"""


# ---------------- HELPERS ----------------
def read_orders_summary():
  conn = sqlite3.connect(DB_PATH)
  c = conn.cursor()
  c.execute("SELECT COUNT(*), IFNULL(SUM(amount),0) FROM orders")
  total_orders, total_revenue = c.fetchone()
  c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 20")
  recent = c.fetchall()
  conn.close()
  return total_orders, round(total_revenue or 0, 2), recent


def read_phase1_metrics():
  if not os.path.exists(PHASE1_DB):
    return [], None
  conn = sqlite3.connect(PHASE1_DB)
  conn.row_factory = sqlite3.Row
  c = conn.cursor()
  try:
    q = """SELECT t.system_id, t.payload, el.status, el.timestamp
               FROM exec_log el
               LEFT JOIN tasks t ON el.task_id = t.id
               ORDER BY el.timestamp DESC"""
    c.execute(q)
    rows = c.fetchall()
  except Exception:
    conn.close()
    return [], None

  agg, last_sync = {}, None
  for r in rows:
    try:
      payload = json.loads(r["payload"] or "{}")
      sys_name = payload.get("system", {}).get("name",
                                               f"system-{r['system_id']}")
    except Exception:
      sys_name = f"system-{r['system_id']}"
    if sys_name not in agg:
      agg[sys_name] = {"success": 0, "failure": 0, "last_success": None}
    if r["status"] and "success" in r["status"].lower():
      agg[sys_name]["success"] += 1
      agg[sys_name][
          "last_success"] = agg[sys_name]["last_success"] or r["timestamp"]
      last_sync = last_sync or r["timestamp"]
    else:
      agg[sys_name]["failure"] += 1
      last_sync = last_sync or r["timestamp"]

  conn.close()
  systems = [{"name": k, **v} for k, v in agg.items()]
  return sorted(systems, key=lambda x: x["name"]), last_sync


# ---------------- ROUTES ----------------
@app.before_request
def require_unlock():
  if request.endpoint in ("unlock", "health"):
    return None
  if not session.get("unlocked"):
    return redirect("/unlock")


@app.route("/unlock", methods=["GET", "POST"])
def unlock():
  if request.method == "POST":
    if request.form.get("code") == LOCK_CODE:
      session["unlocked"] = True
      return redirect("/")
    return "<h3 class='text-red-400'>Invalid Code</h3><a href='/unlock'>Try again</a>"
  return """<html><body style='background:#0B1320;color:#9fdcff;text-align:center;padding-top:80px;'>
    <h2>🔒 JRAVIS Dashboard Locked</h2>
    <form method='POST'><input name='code' type='password' placeholder='Enter Lock Code' style='padding:8px;border-radius:4px;margin:8px;'/>
    <button type='submit' style='padding:8px 14px;background:#007bff;color:white;border-radius:4px;'>Unlock</button></form></body></html>"""


@app.route("/lockout")
def lockout():
  session.clear()
  return redirect("/unlock")


@app.route("/")
def home():
  total_orders, total_revenue, orders = read_orders_summary()
  systems, last_sync = read_phase1_metrics()
  target = 100000  # Example monthly goal
  progress = min(int((total_revenue / target) * 100) if target else 0, 100)
  return render_template_string(
      HTML,
      total_orders=total_orders,
      total_revenue=f"{total_revenue:,.2f}",
      orders=orders,
      systems=systems,
      last_sync=last_sync,
      progress=progress,
      target=f"{target:,}",
      now=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))


@app.route("/health")
def health():
  return {
      "status": "ok",
      "service": "JRAVIS Dashboard v6",
      "time": datetime.utcnow().isoformat()
  }


if __name__ == "__main__":
  port = int(os.getenv("PORT", 10000))
  print(f"[JRAVIS] Dashboard v6 running on port {port}")
  app.run(host="0.0.0.0", port=port)
