# daily_trigger.py
import threading, time, requests, schedule, os

URL = "https://jravis-backend.onrender.com/api/send_daily_report?code=2040"


def call_report():
    try:
        r = requests.get(URL, timeout=30)
        print(f"[Scheduler] Triggered daily report: {r.status_code}")
    except Exception as e:
        print(f"[Scheduler] ERROR: {e}")


def scheduler_loop():
    schedule.every().day.at("10:00").do(call_report)  # 10 AM IST
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_daily_scheduler():
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()


from daily_trigger import start_daily_scheduler

start_daily_scheduler()

# near top of server.py (imports)
from connectors.income_bridge import run_daily as run_income_bridge

# inside orchestrate_report(), before creating summary lines:
try:
    LOG.info("Running income bridge before building report...")
    matched = run_income_bridge()
    LOG.info("Income bridge matched %d payments", matched)
except Exception as e:
    LOG.error("Income bridge failed: %s", e)
