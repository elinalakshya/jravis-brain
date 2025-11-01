import os
import time
import json
import logging
import requests
from datetime import datetime, timezone

VABOT_ENDPOINT = "https://vabot-receiver.onrender.com/api/printify/order"

# === VA BOT RECEIVER ENDPOINT ===
VABOT_ENDPOINT = "https://vabot-receiver.onrender.com/api/printify/order"

# === Logging Setup ===
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s bridge: %(message)s")


def send_payload(data):
    """Send order payload to VA Bot Receiver."""
    try:
        response = requests.post(VABOT_ENDPOINT, json=data, timeout=15)
        response.raise_for_status()
        logging.info("✅ Sent %d orders to VA Bot Receiver", len(data))
    except Exception as e:
        logging.warning("⚠️ Push failed: %s", e)


def main():
    logging.info("🚀 JRAVIS Bridge Core started at %s",
                 datetime.now(timezone.utc))

    while True:
        # 🔁 Simulate pulling order data (replace with Printify/PayPal sync later)
        sample_order = [{
            "id": "demo-order-1",
            "total": 25.0,
            "currency": "USD",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]

        # Send to VA Bot Receiver
        send_payload(sample_order)

        # Wait 5 minutes before next sync (300 seconds)
        time.sleep(300)


if __name__ == "__main__":
    main()
