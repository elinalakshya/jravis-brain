#!/usr/bin/env python3
"""
va_bot_connector.py
VA Bot receiver and callback bridge for JRAVIS Dashboard v3.1
--------------------------------------------------------------

Environment variables:
  SECRET_KEY   - Flask session secret
  SHARED_KEY   - same as JRAVIS.SHARED_KEY
  JRAVIS_URL   - https://jravis-dashboard.onrender.com
  PORT          (optional, default 5000)
"""

from flask import Flask, request, jsonify
import logging, os, time, traceback, requests
from datetime import datetime

# Load environment
SHARED_KEY = os.getenv("SHARED_KEY", "LakshyaSecure2040")
JRAVIS_URL = os.getenv("JRAVIS_URL", "https://jravis-dashboard.onrender.com")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route('/execute', methods=['POST'])
def execute_task():
    """Receive automation plans from JRAVIS or Auto-Key Worker"""
    try:
        data = request.get_json(force=True)
        plan_id = data.get("plan_id", "N/A")
        stream = data.get("stream", "unknown")
        logging.info(
            f"[VA BOT] Received task for stream: {stream}, plan_id: {plan_id}")

        # Simulate VA Bot accepting the task
        response = {
            "status": "accepted",
            "plan_id": plan_id,
            "stream": stream,
            "message": f"VA Bot accepted plan for {stream}"
        }
        return jsonify(response), 200

    except Exception as e:
        logging.error(f"Error executing task: {e}")
        return jsonify({"error": str(e)}), 500


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
    logging.info(f"[VA BOT] Received task from JRAVIS: {payload}")

    try:
        action = payload.get("action")
        stream = payload.get("stream")
        phase = payload.get("phase")

        # simulate / trigger work
        logging.info(
            f"[VA BOT] Executing → action={action} stream={stream} phase={phase}"
        )
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
        logging.info(
            f"[VA BOT] Callback sent to JRAVIS: {r.status_code} {r.text}")
    except Exception as e:
        logging.error(f"[VA BOT] Callback error: {e}")


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
    logging.info("[VA BOT] VA Bot Connector ready")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
