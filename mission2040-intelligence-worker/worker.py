import os
import time
import requests

BRAIN_URL = os.getenv("BRAIN_URL", "https://jravis-brain.onrender.com")


def ping_brain():
    try:
        response = requests.get(f"{BRAIN_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("[Intelligence Worker] ✅ Connected to JRAVIS Brain:",
                  response.json())
        else:
            print("[Intelligence Worker] ⚠️ Brain response error:",
                  response.text)
    except Exception as e:
        print("[Intelligence Worker] ❌ Could not reach JRAVIS Brain:", e)


def run_worker():
    print("[Intelligence Worker] 🚀 Starting Mission 2040 Intelligence Loop...")
    while True:
        ping_brain()
        # Placeholder for future intelligence logic (AI queue, data sync, etc.)
        time.sleep(60)  # Runs every 60 seconds


if __name__ == "__main__":
    run_worker()
