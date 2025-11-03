import os
import time
from datetime import datetime
import requests

VA_BOT_URL = os.getenv("VA_BOT_URL", "https://va-bot-connector.onrender.com")

def generate_daily_report():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[DailyReport] 🕘 {timestamp} - Starting daily summary generation...")
    try:
        response = requests.post(f"{VA_BOT_URL}/generate/daily-report", timeout=20)
        if response.status_code == 200:
            print(f"[DailyReport] ✅ {timestamp} - Daily report generated successfully.")
        else:
            print(f"[DailyReport] ⚠️ {timestamp} - VA Bot response: {response.text}")
    except Exception as e:
        print(f"[DailyReport] ❌ {timestamp} - Error generating daily report: {e}")

def run_worker():
    print("[DailyReport] 🚀 JRAVIS Daily Report Worker started...")
    while True:
        now = datetime.now()
        if now.hour == 10 and now.minute == 0:
            generate_daily_report()
            time.sleep(60)
        time.sleep(20)

if __name__ == "__main__":
    run_worker()
