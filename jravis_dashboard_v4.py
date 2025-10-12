#!/usr/bin/env python3
"""
JRAVIS Dashboard v4.1
🧠 Mission 2040 – Global Passive Income System
- Dark glass UI + hidden lock code
- Real-time phase progress
- Integrated with Income System API
- VA BOT compatible
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import os, requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "jrvis_secret_fallback")

LOCK_CODE = os.environ.get("LOCK_CODE", "2040lock")
SHARED_KEY = os.environ.get("SHARED_KEY", "jrvis_vabot_2040_securekey")
INCOME_API = os.environ.get(
    "INCOME_API",
    "https://income-system-bundle.onrender.com/api/earnings_summary")


# ==============================
# 🔐 SECURE ACCESS PAGE
# ==============================
@app.route("/", methods=["GET", "POST"])
def home():
  if "logged_in" in session:
    return redirect(url_for("dashboard"))

  if request.method == "POST":
    code = request.form.get("code", "")
    if code == LOCK_CODE:
      session["logged_in"] = True
      return redirect(url_for("dashboard"))
    else:
      return render_template_string("""
            <html><body style="background:#0b0c10; color:#fff; text-align:center; font-family:Segoe UI;">
            <h2>🔐 JRAVIS Secure Access</h2>
            <p style="color:red;">Invalid Lock Code</p>
            <form method="POST">
              <input name="code" type="password" placeholder="Enter Lock Code" 
                     style="padding:10px;border:none;border-radius:8px;width:200px;text-align:center;">
              <br><br><button style="padding:8px 16px;border:none;border-radius:8px;
              background:linear-gradient(90deg,#00ffff,#00ff7f);color:black;font-weight:bold;">Unlock</button>
            </form></body></html>
            """)

  return render_template_string("""
    <html><body style="background:#0b0c10; color:#fff; text-align:center; font-family:Segoe UI;">
    <h2>🔐 JRAVIS Secure Access</h2>
    <form method="POST">
      <input name="code" type="password" placeholder="Enter Lock Code"
             style="padding:10px;border:none;border-radius:8px;width:200px;text-align:center;">
      <br><br><button style="padding:8px 16px;border:none;border-radius:8px;
      background:linear-gradient(90deg,#00ffff,#00ff7f);color:black;font-weight:bold;">Unlock</button>
    </form></body></html>
    """)


# ==============================
# 🌍 DASHBOARD MAIN PAGE
# ==============================
@app.route("/dashboard")
def dashboard():
  if "logged_in" not in session:
    return redirect(url_for("home"))

  html = f"""
    <html>
    <head>
    <title>JRAVIS – Mission 2040</title>
    <style>
      body {{
        background: #0b0c10;
        color: #fff;
        font-family: 'Segoe UI', sans-serif;
        padding: 40px;
      }}
      h1 {{
        text-align:center;
        color:#00ffff;
        margin-bottom:30px;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
        gap: 20px;
      }}
      .card {{
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(8px);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      }}
      .progress {{
        background:#222;
        border-radius:10px;
        height:14px;
        margin-top:6px;
        overflow:hidden;
      }}
      .progress div {{
        height:100%;
        background:linear-gradient(90deg,#00ffff,#00ff7f);
        transition:width 0.5s ease;
      }}
      table {{
        width:100%;
        color:#fff;
        border-spacing:0 6px;
      }}
      th, td {{
        text-align:left;
        padding:6px;
      }}
      th {{ color:#00ffff; }}
    </style>
    </head>
    <body>
      <h1>Jarvis Brain – Mission 2040 Dashboard</h1>

      <div class="card">
        <h3>Mission 2040 Progress</h3>
        <div class="progress"><div id="mainProgress" style="width:0%;"></div></div>
        <p id="earningsText">Syncing earnings...</p>
      </div>

      <div class="grid">
        <div class="card">
          <h3>Phase Status</h3>
          <table>
            <tr><th>Phase</th><th>Status</th><th>Target</th></tr>
            <tr><td>Phase 1</td><td id="p1_status">🟢 Active</td><td>₹4 Cr loan clearance</td></tr>
            <tr><td>Phase 2</td><td id="p2_status">🟡 Scaling</td><td>Grow global systems</td></tr>
            <tr><td>Phase 3</td><td id="p3_status">🌐 Preparing</td><td>Robo Mode Expansion</td></tr>
          </table>
          <div class="progress"><div id="phase1" style="width:0%;"></div></div>
          <div class="progress"><div id="phase2" style="width:0%;margin-top:5px;"></div></div>
          <div class="progress"><div id="phase3" style="width:0%;margin-top:5px;"></div></div>
        </div>

        <div class="card">
          <h3>Property & Debt Tracker</h3>
          <p>Debt Clearance ₹2 Cr</p>
          <div class="progress"><div id="debtBar" style="width:40%;"></div></div>
          <p>Savings for Property ₹62L</p>
          <div class="progress"><div id="saveBar" style="width:62%;"></div></div>
          <p>Timeline to June 2027</p>
          <div class="progress"><div id="timeBar" style="width:25%;"></div></div>
        </div>

        <div class="card">
          <h3>Task Timeline</h3>
          <p>✅ Completed</p>
          <p>🟢 Today</p>
          <p>🔵 Tomorrow</p>
        </div>

        <div class="card">
          <h3>Earnings Tracker</h3>
          <canvas id="earnChart" height="100"></canvas>
        </div>
      </div>

      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <script>
      async function loadEarnings() {{
        try {{
          const res = await fetch("{INCOME_API}");
          const data = await res.json();
          document.getElementById("earningsText").innerText = 
            "₹" + data.total_income.toLocaleString() + " / ₹" + data.target.toLocaleString();
          document.getElementById("mainProgress").style.width = data.progress_percent + "%";
          document.getElementById("phase1").style.width = Math.min(100, data.progress_percent) + "%";
          document.getElementById("phase2").style.width = Math.min(60, data.progress_percent * 0.6) + "%";
          document.getElementById("phase3").style.width = Math.min(30, data.progress_percent * 0.3) + "%";
          const ctx = document.getElementById("earnChart").getContext("2d");
          new Chart(ctx, {{
            type:'line',
            data:{{labels:data.dates, datasets:[{{label:'Earnings',data:data.daily_income,borderColor:'#00ffff',fill:true,backgroundColor:'rgba(0,255,255,0.1)'}}]}},
            options:{{scales:{{y:{{ticks:{{color:'#fff'}}}},x:{{ticks:{{color:'#fff'}}}}}}}}
          }});
        }} catch (e) {{
          document.getElementById("earningsText").innerText = "Error syncing";
        }}
      }}
      loadEarnings();
      </script>
    </body>
    </html>
    """
  return render_template_string(html)


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  print(f"[JRAVIS] Dark Glass Dashboard v4.1 running on port {port}")
  app.run(host="0.0.0.0", port=port)
