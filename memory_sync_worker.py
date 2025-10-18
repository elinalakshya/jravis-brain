#!/usr/bin/env python3
import os, time, json, logging, requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)

MEMORY_FILE = "memory_data.json"
INCOME_API = os.getenv(
    "INCOME_BUNDLE_URL",
    "https://income-system-bundle.onrender.com/api/summary")


def sync_memory():
    logging.info("🚀 JRAVIS Memory Sync Worker running...")
    try:
        r = requests.get(INCOME_API, timeout=30)
        if r.status_code == 200:
            data = r.json()
            logging.info(f"✅ Synced income summary: {data}")
            memory = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data
            }
            with open(MEMORY_FILE, "w") as f:
                json.dump(memory, f, indent=2)
            logging.info("💾 Memory updated successfully.")
        else:
            logging.error(f"❌ Failed: {r.status_code} - {r.text}")
    except Exception as e:
        logging.error(f"⚠️ Error syncing memory: {e}")


if __name__ == "__main__":
    while True:
        sync_memory()
        logging.info("🕒 Sleeping for 24 hours...")
        time.sleep(86400)
