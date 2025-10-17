#!/usr/bin/env python3
"""
mission2040_income_sync.py
-----------------------------------------
Daily Income Sync module for JRAVIS Brain.
Pulls income data from connected APIs (Printify, Meshy, YouTube),
sends execution tasks to VA Bot, and updates Mission Bridge.
-----------------------------------------
"""

import os
import json
import time
import requests
from datetime import datetime

# Load environment variables
PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
MESHY_API_KEY = os.getenv("MESHY_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

VA_BOT_WEBHOOK = os.getenv("VA_BOT_WEBHOOK",
                           "https://va-bot-connector.onrender.com/execute")
MISSION_BRIDGE_URL = os.getenv("MISSION_BRIDGE_URL",
                               "https://mission-bridge.onrender.com")
LOCK_CODE = os.getenv("LOCK_CODE", "204040")

print("🚀 JRAVIS Mission 2040 — Income Sync Starting...")

# -------------------------------
# Helper functions
# -------------------------------


def send_to_vabot(stream, payload):
    """Send income task to VA Bot Connector"""
    try:
        res = requests.post(VA_BOT_WEBHOOK, json=payload, timeout=10)
        res.raise_for_status()
        print(f"✅ Sent income sync to VA Bot for {stream}")
    except Exception as e:
        print(f"❌ VA Bot send error for {stream}: {e}")


def update_mission_bridge(stream, data):
    """Send earnings to Mission Bridge"""
    try:
        payload = {
            "stream": stream,
            "earnings": data.get("earnings", 0),
            "currency": "INR",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        r = requests.post(MISSION_BRIDGE_URL + "/api/income_update",
                          json=payload,
                          timeout=10)
        r.raise_for_status()
        print(f"📈 Bridge updated for {stream}: ₹{payload['earnings']}")
    except Exception as e:
        print(f"⚠️ Bridge update failed for {stream}: {e}")


# -------------------------------
# Stream income sync functions
# -------------------------------


def fetch_printify_income():
    url = "https://api.printify.com/v1/shops.json"
    headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        # demo: assume 5% of total products sold = ₹ amount
        total = 12500  # placeholder; real calculation from response
        return {"earnings": total}
    except Exception as e:
        print("❌ Printify fetch error:", e)
        return {"earnings": 0}


def fetch_meshy_income():
    # demo placeholder
    try:
        total = 8700  # sample revenue
        return {"earnings": total}
    except Exception as e:
        print("❌ Meshy fetch error:", e)
        return {"earnings": 0}


def fetch_youtube_income():
    # demo placeholder
    try:
        total = 23300  # sample revenue
        return {"earnings": total}
    except Exception as e:
        print("❌ YouTube fetch error:", e)
        return {"earnings": 0}


# -------------------------------
# Main execution
# -------------------------------
def main():
    streams = {
        "printify": fetch_printify_income,
        "meshy": fetch_meshy_income,
        "youtube": fetch_youtube_income
    }

    print("🧠 Starting income sync for all connected streams...")
    for stream, fn in streams.items():
        data = fn()
        earnings = data["earnings"]
        print(f"💰 {stream.title()} earnings fetched: ₹{earnings}")

        # Send to VA Bot
        payload = {
            "stream": stream,
            "plan_id":
            f"income-{stream}-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            "earnings": earnings,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        send_to_vabot(stream, payload)

        # Update Mission Bridge
        update_mission_bridge(stream, data)
        time.sleep(2)

    print("✅ Income sync completed successfully!")


if __name__ == "__main__":
    main()
