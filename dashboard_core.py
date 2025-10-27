import os
import sqlite3
from flask import Flask, request, redirect, render_template_string, session

# -----------------------------
# ✅ CONFIG
# -----------------------------
LOCK_CODE = os.getenv("LOCK_CODE", "LakshyaSecureCode@2040")
DB_PATH = "dashboard.db"

app = Flask(__name__)
app.secret_key = os.getenv("DASHBOARD_SECRET", "JRAVIS@Mission2040")


# -----------------------------
# ✅ DATABASE INITIALIZATION
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream TEXT,
            amount REAL,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()

# -----------------------------
# ✅ HTML TEMPLATE
# -----------------------------
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>JRAVIS Command Console — Mission 2040</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0d1117; color: #eee; text-align: center; }
        h1 { color: #00c3ff; }
        table { margin: 20px auto; border-collapse: collapse; width: 80%; }
        th, td { padding: 10px; border: 1px solid #444; }
        tr:nth-child(even) { background: #1c1f26; }
        .stat { margin-top: 20px; }
    </style>
</head>
<body>
    <h1>JRAVIS Command Console — Mission 2040</h1>
    <p>Phase 1 Active • Automated Passive Systems</p>
    <div class="stat">
        <h2>Total Income: ₹{{ total_income }}</h2>
        <h3>Total Orders: {{ total_orders }}</h3>
    </div>
    <table>
        <tr><th>Stream</th><th>Amount (₹)</th><th>Date</th></tr>
        {% for o in orders %}
        <tr><td>{{ o[1] }}</td><td>{{ o[2] }}</td><td>{{ o[3] }}</td></tr>
        {% endfor %}
    </table>
    <p>Last update: {{ last_update }}</p>
</body>
</html>
"""


# -----------------------------
# ✅ ROUTES
# -----------------------------
@app.route("/", methods=["GET"])
def root():
    if not session.get("unlocked"):
        return redirect("/unlock")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), IFNULL(SUM(amount), 0) FROM orders")
    total_orders, total_income = c.fetchone()
    c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 50")
    orders = c.fetchall()
    conn.close()
    return render_template_string(HTML_DASHBOARD,
                                  orders=orders,
                                  total_orders=total_orders,
                                  total_income=round(total_income, 2),
                                  last_update="Live")


@app.route("/unlock", methods=["GET", "POST"])
def unlock():
    if request.method == "POST":
        code = request.form.get("code", "")
        if code == LOCK_CODE:
            session["unlocked"] = True
            return redirect("/")
        else:
            return "<h3>❌ Invalid Code</h3><a href='/unlock'>Try again</a>"
    return """
    <form method='POST'>
        <h2>Enter Lock Code</h2>
        <input type='password' name='code' placeholder='Enter Lock Code' required>
        <button type='submit'>Unlock</button>
    </form>
    """


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "JRAVIS Dashboard", "time": "live"}


# -----------------------------
# ✅ RUN
# -----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"[JRAVIS] Live dashboard started on port {port}")
    app.run(host="0.0.0.0", port=port)
