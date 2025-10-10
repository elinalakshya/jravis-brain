#!/usr/bin/env python3
"""
vabot_connector.py
VA Bot receiver and callback bridge for JRAVIS Dashboard v3.1
--------------------------------------------------------------

Environment variables:
  SECRET_KEY   - Flask session secret
  SHARED_KEY   - same as JRAVIS.SHARED_KEY
  JRAVIS_URL   - https://jravis-dashboard.onrender.com
  PORT          (optional, default 5000)
"""

from flask import Flask, request, jsonify
import os, json, requests, traceback, time
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "vabot_secret_key")

SHARED_KEY = os.environ.get("SHARED_KEY", "change-this-securely")
JRAVIS_URL = os.environ.get(
    "JRAVIS_URL", "https://jravis-dashboard.onrender.com").rstrip("/")


# simple log
def log(*a):
    print("[VA BOT]", *a)


# ------------------------------
# Receive tasks from JRAVIS
# ------------------------------
@app.route("/api/receive_task", methods=["POST"])
def receive_task():
    auth = request.headers.get("Authorization", "")
    token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
    if token != SHARED_KEY:
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(force=True)
    log("Received task from JRAVIS:", payload)

    try:
        action = payload.get("action")
        stream = payload.get("stream")
        phase = payload.get("phase")

        # simulate / trigger work
        log(f"Executing → action={action} stream={stream} phase={phase}")
        time.sleep(2)

        status = {
            "action": action,
            "stream": stream,
            "phase": phase,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # callback to JRAVIS
        send_status_to_jravis(status)
        return jsonify({"status": "received"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ------------------------------
# Send callback to JRAVIS
# ------------------------------
def send_status_to_jravis(status):
    try:
        url = JRAVIS_URL + "/api/vabot_status"
        headers = {
            "Authorization": f"Bearer {SHARED_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.post(url, json=status, headers=headers, timeout=15)
        log("Callback sent to JRAVIS:", r.status_code, r.text)
    except Exception as e:
        log("Callback error:", e)


# ------------------------------
# Health check
# ------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat() + "Z"
    }), 200


if __name__ == "__main__":
    log("VA Bot Connector ready")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
