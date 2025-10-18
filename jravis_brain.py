# -*- coding: utf-8 -*-
"""
JRAVIS Brain — Mission 2040 Core Engine
"""
import os, uuid, json, time, requests, datetime, logging
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import openai

from memory_system import save_income_summary, export_full_memory

# --------------------------
# Flask App Setup
# --------------------------
app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()


@app.route('/')
def home():
    return "🧠 JRAVIS Brain active — Mission 2040 core online.", 200


@app.route("/health")
def health():
    return jsonify({
        "status": "alive",
        "time": datetime.datetime.utcnow().isoformat()
    })


@app.route("/api/update_income", methods=["POST"])
def update_income():
    data = request.get_json(force=True)
    save_income_summary(data)
    return jsonify({"status": "saved"}), 200


@app.route("/api/memory_snapshot", methods=["GET"])
def memory_snapshot():
    return jsonify(export_full_memory()), 200


# --------------------------
# Heartbeat Logger
# --------------------------
def heartbeat():
    logging.info(
        f"💓 JRAVIS heartbeat at {datetime.datetime.utcnow().isoformat()}")


scheduler.add_job(heartbeat, "interval", seconds=30)

# ===============================
# 🔁 Mission 2040 Daily Scheduler
# ===============================
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import time
from datetime import datetime


def run_income_sync():
    print(
        f"🚀 [JRAVIS] Running daily income sync @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    try:
        subprocess.run(["python3", "mission2040_income_sync.py"], check=True)
        print("✅ [JRAVIS] Income sync finished.")
    except Exception as e:
        print(f"❌ [JRAVIS] Scheduler error: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(run_income_sync, "interval", hours=24)
scheduler.start()

print("📅 JRAVIS Daily Scheduler is live and running...")

# Optional immediate trigger on startup
time.sleep(10)
run_income_sync()


@app.route("/api/report_status", methods=["POST"])
def report_status():
    data = request.get_json(force=True)
    with open("latest_report.json", "w") as f:
        json.dump(data, f, indent=2)
    print("✅ Report data received from worker:", data.get("summary"))
    return jsonify({"status": "ok"}), 200


# ==============================================================
# 📩 API ENDPOINT — Receive Mission 2040 Report Status
# ==============================================================
from flask import Flask, request, jsonify
import logging, datetime, json, os

REPORT_LOG_FILE = "report_log.json"


@app.route("/api/report_status", methods=["POST"])
def receive_report_status():
    """Receive status updates from Mission 2040 Report Worker"""
    try:
        data = request.get_json(force=True)
        timestamp = data.get("timestamp",
                             datetime.datetime.utcnow().isoformat())
        summary = data.get("summary", "No summary text received.")

        logging.info(f"📥 Received report confirmation from Worker → {summary}")

        # Store into local JSON log
        entry = {"timestamp": timestamp, "summary": summary}
        if os.path.exists(REPORT_LOG_FILE):
            with open(REPORT_LOG_FILE, "r") as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(entry)
        with open(REPORT_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)

        return jsonify({"status": "logged", "timestamp": timestamp}), 200

    except Exception as e:
        logging.error(f"❌ Failed to record report status: {e}")
        return jsonify({"error": str(e)}), 500


# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
