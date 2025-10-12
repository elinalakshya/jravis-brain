#!/usr/bin/env python3
"""
JRAVIS Dashboard v3.1
---------------------
• Dark glass UI (mobile friendly)
• Lock-protected (code 2040)
• Auto-refresh sections
• Fully linked with VA Bot through jravis_va_connector.py
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import os, json, time, requests

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "jravis_secret_key_fallback")

# --- Import JRAVIS-VA connector ---
from jravis_va_connector import register_endpoints, start_background_worker

# -------------------------------------------------------------
# 🔐 Basic lock page (uses your lock code)
LOCK_CODE = os.environ.get("LOCK_CODE", "2040")


@app.route("/", methods=["GET", "POST"])
def index():
    if "unlocked" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        code = request.form.get("code", "")
        if code == LOCK_CODE:
            session["unlocked"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template_string(PAGE_TEMPLATE, error="Wrong code")
    return render_template_string(PAGE_TEMPLATE)


PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>JRAVIS v3.1</title>
  <style>
    body {
      background: radial-gradient(circle at top, #0b0b0b, #111);
      color: #fff; font-family: sans-serif;
      display:flex; flex-direction:column; align-items:center; justify-content:center;
      height:100vh; margin:0;
    }
    input[type=password]{padding:10px;border:none;border-radius:8px;font-size:18px;}
    button{padding:10px 20px;margin-left:10px;border:none;border-radius:8px;background:#1e88e5;color:#fff;}
    .err{color:#ff5555;margin-top:10px;}
  </style>
</head>
<body>
  <h2>Enter Lock Code</h2>
  <form method="POST">
    <input type="password" name="code" placeholder="2040" autofocus>
    <button>Unlock</button>
  </form>
  {% if error %}<div class="err">{{error}}</div>{% endif %}
</body>
</html>
"""


# -------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if "unlocked" not in session:
        return redirect(url_for("index"))
    return "<h1 style='color:white;text-align:center;margin-top:30vh'>JRAVIS v3.1 Connected ✅</h1>"


# -------------------------------------------------------------
# ✅ VA Bot status callback endpoint
@app.route("/api/vabot_status", methods=["POST"])
def vabot_status():
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
    if token != os.environ.get("SHARED_KEY"):
        return jsonify({"error": "unauthorized"}), 401
    payload = request.json or {}
    print("✅ VA Bot status callback received:", payload)
    # Optional: update DB or UI
    return jsonify({"status": "ok"}), 200


# -------------------------------------------------------------
# ✅ Integrate connector and start worker
register_endpoints(app)
start_background_worker()

# -------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
