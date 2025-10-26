import os
import sqlite3
from flask import Flask, jsonify, render_template_string, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY",
                           "change_this_secret")  # Needed for sessions

DB_PATH = os.getenv("DB_PATH", "jravis_data.db")
LOCK_CODE = os.getenv("LOCK_CODE", "Lakshya@2040")


# ---------- DATABASE HELPERS ---------- #
def get_revenue_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            shop_id TEXT,
            amount NUMERIC,
            currency TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE VIEW IF NOT EXISTS revenue_summary AS
        SELECT DATE(created_at) AS day,
               SUM(amount) AS total_revenue,
               COUNT(*) AS total_orders
        FROM orders
        GROUP BY 1
        ORDER BY 1 DESC
    """)
    conn.commit()
    rows = c.execute(
        "SELECT day, total_orders, total_revenue FROM revenue_summary ORDER BY day DESC LIMIT 30"
    ).fetchall()
    conn.close()
    return rows


def get_live_totals():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- Always make sure the orders table exists ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            shop_id TEXT,
            amount NUMERIC,
            currency TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # --- Query safely ---
    try:
        c.execute("SELECT COUNT(*), IFNULL(SUM(amount),0) FROM orders")
        total_orders, total_revenue = c.fetchone()
    except sqlite3.OperationalError as e:
        print("[JRAVIS] Warning:", e)
        total_orders, total_revenue = 0, 0

    conn.close()
    return total_orders, total_revenue


# ---------- AUTH / LOCK ---------- #
@app.route("/unlock", methods=["GET", "POST"])
def unlock():
    if request.method == "POST":
        code = request.form.get("code", "")
        if code == LOCK_CODE:
            session["unlocked"] = True
            return redirect(url_for("dashboard"))
        return render_template_string(
            "<h3>Wrong code</h3><a href='/unlock'>Try again</a>")
    return render_template_string("""
        <html><head><title>JRAVIS Secure Access</title></head>
        <body style="font-family:Arial;background:#0b132b;color:#fff;text-align:center;margin-top:100px;">
            <h2>🔒 JRAVIS Dashboard Locked</h2>
            <form method="post">
              <input type="password" name="code" placeholder="Enter Lock Code" 
                     style="padding:8px;border-radius:5px;">
              <button type="submit" style="padding:8px 12px;">Unlock</button>
            </form>
        </body></html>
    """)


@app.before_request
def check_lock():
    if request.endpoint not in ("unlock",
                                "static") and not session.get("unlocked"):
        return redirect(url_for("unlock"))


# ---------- ROUTES ---------- #
@app.route("/")
def dashboard():
    total_orders, total_revenue = get_live_totals()
    data = get_revenue_summary()
    html = """
    <html>
    <head>
      <title>JRAVIS Live Dashboard</title>
      <style>
        body {font-family: Arial; margin: 40px; background: #0b132b; color: #f0f0f0;}
        h1 {color: #00f2ff;}
        table {border-collapse: collapse; width: 60%; margin-top: 30px;}
        th, td {border: 1px solid #222; padding: 8px; text-align: center;}
        th {background: #1c2541;}
        td {background: #3a506b;}
        a.logout {color:#00f2ff;text-decoration:none;float:right;}
      </style>
    </head>
    <body>
      <a href="/lockout" class="logout">Lock</a>
      <h1>JRAVIS — Live Income Dashboard</h1>
      <p><b>Total Orders:</b> {{orders}} &nbsp;&nbsp;
         <b>Total Revenue:</b> ₹{{revenue:,.2f}}</p>
      <h3>Daily Revenue (Past 30 Days)</h3>
      <table>
        <tr><th>Date</th><th>Orders</th><th>Revenue (₹)</th></tr>
        {% for row in data %}
          <tr><td>{{row[0]}}</td><td>{{row[1]}}</td><td>{{"{:,.2f}".format(row[2] or 0)}}</td></tr>
        {% endfor %}
      </table>
    </body>
    </html>
    """
    return render_template_string(html,
                                  orders=total_orders,
                                  revenue=total_revenue,
                                  data=data)


@app.route("/api/summary")
def api_summary():
    total_orders, total_revenue = get_live_totals()
    data = get_revenue_summary()
    return jsonify({
        "orders":
        total_orders,
        "revenue":
        total_revenue,
        "daily_summary": [{
            "day": d,
            "orders": o,
            "revenue": r
        } for (d, o, r) in data]
    })


@app.route("/lockout")
def lockout():
    session.clear()
    return redirect(url_for("unlock"))

def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            shop_id TEXT,
            amount NUMERIC,
            currency TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("[JRAVIS] Database initialized ✔️")

# ---------- MAIN ---------- #
if __name__ == "__main__":
    init_database()           # <-- ensure table exists on startup
    port = int(os.getenv("PORT", 10000))
    print(f"[JRAVIS] Live dashboard started on port {port}")
    app.run(host="0.0.0.0", port=port)
