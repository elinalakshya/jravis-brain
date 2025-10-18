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
    return jsonify({"status": "JRAVIS Brain is alive 🚀"})


@app.route("/health")
def health():
    return jsonify({
        "status": "alive",
        "time": datetime.datetime.now().isoformat()
    })


# --------------------------
# Heartbeat Logger
# --------------------------
def heartbeat():
    logging.info(f"💓 JRAVIS alive at {datetime.datetime.now().isoformat()}")


scheduler.add_job(heartbeat, 'interval', seconds=60)

# --------------------------
# OpenAI + Planner
# --------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
VA_BOT_WEBHOOK = os.getenv("VA_BOT_WEBHOOK")

PLANNER_SYSTEM = """You are JRAVIS Brain. Convert the user_command into a strict JSON Plan using the Plan Schema.
Schema keys: request_id, user_command, intent, priority, plan[], post_actions, mission_check.
Each plan[] item must include: step_id, action, target, params, expected_result, retry_policy."""


def generate_plan(user_command):
    if not OPENAI_API_KEY:
        return {"error": "Missing OPENAI_API_KEY"}
    prompt = f"User command: \"{user_command}\""
    resp = openai.ChatCompletion.create(model="gpt-5",
                                        messages=[{
                                            "role": "system",
                                            "content": PLANNER_SYSTEM
                                        }, {
                                            "role": "user",
                                            "content": prompt
                                        }],
                                        max_tokens=800,
                                        temperature=0.0)
    text = resp['choices'][0]['message']['content'].strip()
    try:
        return json.loads(text)
    except Exception:
        return {"error": "Failed to parse", "raw": text}


@app.route("/command", methods=["POST"])
def command():
    data = request.json or {}
    cmd = data.get("command")
    if not cmd:
        return jsonify({"error": "no command"}), 400
    plan = generate_plan(cmd)
    return jsonify({"plan": plan})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
