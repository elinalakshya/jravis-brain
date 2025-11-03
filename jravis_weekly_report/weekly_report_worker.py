import os
import time
from datetime import datetime
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "https://jravis-backend.onrender.com")


def trigger_weekly_report():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[WeeklyReport] 🕛 {timestamp} - Triggering weekly report...")

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/send_weekly_report?code=2040", timeout=30)
        if response.status_code == 200:
            print(
                f"[WeeklyReport] ✅ {timestamp} - Weekly report generated successfully."
            )
        else:
            print(
                f"[WeeklyReport] ⚠️ {timestamp} - Backend responded: {response.text}"
            )
    except Exception as e:
        print(f"[WeeklyReport] ❌ {timestamp} - Error: {e}")


def run_worker():
    print("[WeeklyReport] 🚀 JRAVIS Weekly Report Worker started...")
    while True:
        now = datetime.now()
        # Sunday at 00:00 (midnight)
        if now.weekday() == 6 and now.hour == 0 and now.minute == 0:
            trigger_weekly_report()
            time.sleep(60)
        time.sleep(20)


if __name__ == "__main__":
    run_worker()
