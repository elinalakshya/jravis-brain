import os
import time
import requests
from datetime import datetime

BRAIN_URL = os.getenv("BRAIN_URL", "http://jravis-brain:8000")


def sync_memory():
    """Simulates periodic memory sync with JRAVIS Brain."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        response = requests.get(f"{BRAIN_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print(f"[MemorySync] ✅ {timestamp} - Synced memory with Brain:",
                  response.json())
        else:
            print(f"[MemorySync] ⚠️ {timestamp} - Brain returned:",
                  response.text)
    except Exception as e:
        print(f"[MemorySync] ❌ {timestamp} - Error syncing memory:", e)


def run_worker():
    print("[MemorySync] 💾 Starting Mission2040 Memory Sync Worker...")
    while True:
        sync_memory()
        # Runs every 90 seconds for stable sync interval
        time.sleep(90)


if __name__ == "__main__":
    run_worker()
