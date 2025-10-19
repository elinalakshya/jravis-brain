# ============================================================
# JRAVIS Phase-1 Auto-Scheduler
# Schedules daily and weekly automation for Mission 2040
# ============================================================

import schedule
import time
from datetime import datetime
import subprocess

# --- CONFIG ---
DAILY_TIME = "10:00"  # 10 AM IST
WEEKLY_TIME = "00:00"  # Sunday 12 AM IST


def run_daily():
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🧠 Running Daily Tasks..."
    )
    subprocess.run(["python", "jravis_core_debian.py"])


def run_weekly():
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📊 Running Weekly Report..."
    )
    subprocess.run(["python", "jravis_core_debian.py", "--weekly"])


# --- SCHEDULE ---
schedule.every().day.at(DAILY_TIME).do(run_daily)
schedule.every().sunday.at(WEEKLY_TIME).do(run_weekly)

print("🚀 Phase-1 Auto-Scheduler started")
print(f"  ⏰ Daily at {DAILY_TIME} IST")
print(f"  📆 Weekly (Sunday) at {WEEKLY_TIME} IST")

# --- LOOP ---
while True:
    schedule.run_pending()
    time.sleep(30)
