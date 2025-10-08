#!/usr/bin/env python3
from flask import Flask, jsonify, render_template_string
import os, datetime, subprocess, json

app = Flask(__name__)

# ------------------------------
# Mission Data
# ------------------------------
CURRENT_EARNINGS_INR = 125000
CURRENT_EARNINGS_USD = 1500
PROGRESS_PERCENT = 32

PHASES = {
    "Phase 1 — Fast Kickstart": {
        "streams": [{
            "name": "Elina Instagram Reels",
            "status": "✅ Active"
        }, {
            "name": "Printify POD Store",
            "status": "⚙️ Syncing"
        }, {
            "name": "MeshyAI Models",
            "status": "⚠️ Reconnect needed"
        }, {
            "name": "YouTube Automation",
            "status": "✅ Active"
        }, {
            "name": "Stationery Export",
            "status": "⚠️ Awaiting invoice"
        }]
    },
    "Phase 2 — Global Expansion": {
        "streams": [{
            "name": "Shopify Digital Products",
            "status": "🕒 Planned"
        }, {
            "name": "AI Book Publishing",
            "status": "🕒 Planned"
        }]
    },
    "Phase 3 — Robo Mode": {
        "streams": [{
            "name": "Auto Inspection Garuda",
            "status": "🧠 Development"
        }, {
            "name": "Dhruvayu VA Bot",
            "status": "⚙️ Operational"
        }]
    }
}

# ------------------------------
# HTML Template (No special characters in {{ }})
# ------------------------------
MAIN_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>JRAVIS Mission 2040</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #f6f8fa; margin: 30px; color: #222; }
    h1 { margin-bottom: 10px; }
    .earn-large { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
    .progress { height: 10px; background: #ddd; border-radius: 5px; margin-top: 6px; overflow: hidden; }
    .bar { height: 10px; background: linear-gradient(90deg, #4caf50, #81c784); border-radius: 5px; transition: width 0.6s ease; }
    .phase { margin-top: 20px; padding: 16px; background: #fff; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,.1); }
    ul { list-style: none; padding: 0; }
    li { padding: 4px 0; }
  </style>
</head>
<body>
  <h1>Mission 2040 Dashboard</h1>

  <div class="earn-large">
    ₹ {{ earn_inr }} | $ {{ earn_usd }}
  </div>

  <div>
    <b>Progress:</b> {{ progress_percent }}%
    <div class="progress"><div class="bar" style="width:{{ progress_percent }}%"></div></div>
  </div>

  {% for name, data in phases.items() %}
  <div class="phase">
    <h2>{{ name }}</h2>
    <ul>
      {% for stream in data.streams %}
      <li>{{ stream.name }} — {{ stream.status }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endfor %}
</body>
</html>
"""


# ------------------------------
# Routes
# ------------------------------
@app.route("/")
def dashboard():
    return render_template_string(MAIN_HTML,
                                  earn_inr=str(CURRENT_EARNINGS_INR),
                                  earn_usd=str(CURRENT_EARNINGS_USD),
                                  progress_percent=PROGRESS_PERCENT,
                                  phases=PHASES)


@app.route("/health")
def health():
    return jsonify({
        "status": "OK",
        "uptime": datetime.datetime.now().isoformat()
    })


@app.route("/run-capture", methods=["POST"])
def run_capture():
    try:
        result = subprocess.run(
            ["python3", "DailyReport/capture_meshytube.py"],
            capture_output=True,
            text=True,
            timeout=15)
        return f"Capture complete:\\n{result.stdout or result.stderr}"
    except Exception as e:
        return f"Error: {e}", 500


# ------------------------------
# Run
# ------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"⚙️ Starting JRAVIS Dashboard on port {port}")
    app.run(host="0.0.0.0", port=port)
