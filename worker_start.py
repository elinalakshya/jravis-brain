import time
import schedule
import subprocess


def run_bot():
    print("▶️ Running VA Bot…")
    subprocess.run(["python3", "send_daily_report.py"])


# schedule the bot daily at 10:00 AM IST
schedule.every().day.at("10:00").do(run_bot)

print("✅ Worker started, waiting for schedule…")

while True:
    schedule.run_pending()
    time.sleep(60)
