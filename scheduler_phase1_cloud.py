# ============================================================
# JRAVIS Phase-1 Cloud Scheduler
# Automates daily + weekly triggers for JRAVIS Core on Render
# ============================================================

import os
import time
import requests
import schedule
from datetime import datetime, timezone, timedelta

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

# Pull the deploy hook URL from environment variable
DEPLOY_HOOK_URL = os.environ.get("DEPLOY_HOOK_URL")

if not DEPLOY_HOOK_URL:
    raise EnvironmentError(
        "🚨 DEPLOY_HOOK_URL not found. Please add it in Render → Environment → Variables"
    )

# Timezone offset for IST (+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

# Daily & Weekly times (in IST)
DAILY_TIME = "10:00"
WEEKLY_TIME = "00:00"

# ------------------------------------------------------------
# TASK DEFINITIONS
# ------------------------------------------------------------


def trigger_deploy(task_name: str):
    """Ping Render deploy hook to trigger rebuild of JRAVIS Core"""
    try:
        print(
            f"[{datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Triggering {task_name} via Render Hook..."
        )
        response = requests.post(DEPLOY_HOOK_URL)
        if response.status_code == 200:
            print(
                f"✅ {task_name} Triggered Successfully — Status Code {response.status_code}"
            )
        else:
            print(
                f"⚠️ {task_name} Trigger Failed — HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error during {task_name}: {e}")


def daily_job():
    trigger_deploy("Daily Automation")


def weekly_job():
    trigger_deploy("Weekly Summary")


# ------------------------------------------------------------
# SCHEDULE SETUP
# ------------------------------------------------------------
schedule.every().day.at(DAILY_TIME).do(daily_job)
schedule.every().sunday.at(WEEKLY_TIME).do(weekly_job)

print("🌐 JRAVIS Cloud Scheduler started successfully!")
print(f"  ⏰ Daily run at {DAILY_TIME} IST")
print(f"  📆 Weekly summary every Sunday at {WEEKLY_TIME} IST")

# ------------------------------------------------------------
# LOOP
# ------------------------------------------------------------
while True:
    schedule.run_pending()
    time.sleep(30)
