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

# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
