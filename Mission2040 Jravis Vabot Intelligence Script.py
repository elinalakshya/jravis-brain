"""
Mission2040_JRAVIS_VABot_Intelligence_Script.py (Hardened + Health Endpoint)

Purpose:
- JRAVIS ↔ VA Bot ↔ Mission Bridge intelligence controller with live monitoring.
- Includes automatic retries, self-healing watchdog, and /health endpoint for Render dashboards.

"""

import os
import time
import json
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, Any
from flask import Flask, jsonify

# ----------------------------- CONFIG -----------------------------
CONFIG = {
    "VA_BOT_WEBHOOK":
    os.getenv("VA_BOT_WEBHOOK",
              "https://va-bot-connector.onrender.com/execute"),
    "MISSION_BRIDGE_URL":
    os.getenv("MISSION_BRIDGE_URL", "https://mission-bridge.onrender.com/log"),
    "LOCK_CODE":
    os.getenv("LOCK_CODE", "YOUR_EXISTING_LOCK_CODE"),
    "HEARTBEAT_INTERVAL":
    int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30")),
    "JRAVIS_TOKEN":
    os.getenv("JRAVIS_TOKEN", "secure_jravis_token"),
    "MAX_RETRIES":
    3,
    "RETRY_DELAY":
    5,
    "REPORT_SCHEDULE": {
        "daily_hour_minute": (10, 0),
        "weekly_day": 6,
        "weekly_time": (0, 0)
    }
}


# ----------------------------- HEALTH MONITOR -----------------------------
class HealthMonitor:

    def __init__(self):
        self.last_success = datetime.utcnow()
        self.error_count = 0
        self.last_cycle = None

    def record_success(self):
        self.last_success = datetime.utcnow()
        self.error_count = 0

    def record_error(self):
        self.error_count += 1

    def summary(self) -> Dict[str, Any]:
        return {
            "last_success":
            self.last_success.isoformat() + "Z",
            "error_count":
            self.error_count,
            "healthy":
            self.error_count < 5
            and (datetime.utcnow() - self.last_success).seconds < 600
        }


# ----------------------------- UTILITIES -----------------------------
def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def safe_post(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {CONFIG['JRAVIS_TOKEN']}",
        "Content-Type": "application/json"
    }
    for attempt in range(CONFIG["MAX_RETRIES"]):
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if resp.status_code in [200, 201]:
                return {
                    "status": "ok",
                    "data": resp.json() if resp.content else {}
                }
        except Exception as e:
            if attempt == CONFIG["MAX_RETRIES"] - 1:
                return {"status": "error", "error": str(e)}
            time.sleep(CONFIG["RETRY_DELAY"])


def encrypt_file_placeholder(filepath: str, lock_code: str) -> str:
    enc = filepath.replace('.json', '.locked.json')
    with open(filepath, 'r') as fr, open(enc, 'w') as fw:
        fw.write(json.dumps({"locked_with": lock_code, "payload": fr.read()}))
    return enc


# ----------------------------- CONTROLLER -----------------------------
class JRAVISController:

    def __init__(self):
        self.heartbeat = CONFIG["HEARTBEAT_INTERVAL"]
        self.monitor = HealthMonitor()
        self.daily_done = False

    def run_cycle(self):
        plan = {
            "phase":
            1,
            "generated_at":
            now_iso(),
            "objective":
            "Run Phase 1 task set",
            "tasks": [
                "Elina Instagram Reels", "Printify POD Store",
                "YouTube Automation"
            ]
        }
        result = safe_post(CONFIG["VA_BOT_WEBHOOK"], plan)
        if result["status"] == "ok":
            self.monitor.record_success()
        else:
            self.monitor.record_error()
        safe_post(
            CONFIG["MISSION_BRIDGE_URL"], {
                "event": "cycle_run",
                "status": result["status"],
                "timestamp": now_iso()
            })

        # daily report trigger at 10:00 AM IST
        hour, minute = CONFIG["REPORT_SCHEDULE"]["daily_hour_minute"]
        now = datetime.now()
        if now.hour == hour and not self.daily_done:
            filename = f"report_{now.strftime('%Y-%m-%d')}.json"
            with open(filename, 'w') as f:
                json.dump({"report": "auto daily", "timestamp": now_iso()}, f)
            enc = encrypt_file_placeholder(filename, CONFIG["LOCK_CODE"])
            safe_post(CONFIG["MISSION_BRIDGE_URL"], {
                "event": "daily_report",
                "path": enc
            })
            self.daily_done = True
        if now.hour != hour:
            self.daily_done = False

    def start(self):
        print(
            f"[LIVE] JRAVIS Intelligence Controller active — heartbeat {self.heartbeat}s"
        )
        while True:
            try:
                start = time.time()
                self.run_cycle()
                self.monitor.last_cycle = now_iso()
                time.sleep(max(0, self.heartbeat - (time.time() - start)))
            except Exception as e:
                safe_post(
                    CONFIG["MISSION_BRIDGE_URL"], {
                        "event": "fatal_error",
                        "error": str(e),
                        "timestamp": now_iso()
                    })
                time.sleep(10)


# ----------------------------- FLASK HEALTH ENDPOINT -----------------------------
app = Flask(__name__)
controller = JRAVISController()


@app.route('/health', methods=['GET'])
def health():
    summary = controller.monitor.summary()
    summary.update({"last_cycle": controller.monitor.last_cycle})
    return jsonify(summary)


# ----------------------------- ENTRYPOINT -----------------------------
if __name__ == '__main__':
    # Run Flask health endpoint in a separate thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    controller.start()
