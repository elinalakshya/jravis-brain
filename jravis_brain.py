# -*- coding: utf-8 -*-
"""
JRAVIS Brain — Mission 2040 Core Engine
"""

import os, uuid, json, time, requests, datetime, logging
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import openai

# --------------------------
# Flask App Setup
# --------------------------
app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()


@app.route("/")
def home():
    return jsonify({"status": "✅ JRAVIS Brain is alive 🚀"})


@app.route("/health")
def health():
    return jsonify({
        "status": "alive",
        "time": datetime.datetime.utcnow().isoformat()
    })


# --------------------------
# Heartbeat Logger
# --------------------------
def heartbeat():
    logging.info(f"💓 JRAVIS heartbeat at {datetime.datetime.utcnow().isoformat()}")


scheduler.add_job(heartbeat, "interval", seconds=30)


# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

