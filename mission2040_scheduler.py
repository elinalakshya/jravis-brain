#!/usr/bin/env python3
"""
mission2040_scheduler.py
--------------------------------------------------------
Schedules JRAVIS income sync every 24h automatically.
--------------------------------------------------------
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
import subprocess

print("🕒 Mission 2040 Scheduler Started...")


def run_income_sync():
    print(
        f"🚀 Triggering income sync at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    try:
        # Run the income sync module
        subprocess.run(["python3", "mission2040_income_sync.py"], check=True)
        print("✅ Income sync completed.")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")


# Create scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_income_sync, 'interval', hours=24)
scheduler.start()

print("📅 JRAVIS Daily Income Scheduler Running...")

# Keep the process alive
try:
    while True:
        time.sleep(60)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    print("🛑 Scheduler stopped.")
