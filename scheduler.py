from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz, subprocess, sys, os

IST = pytz.timezone("Asia/Kolkata")

def run_py(args):
    print(f"→ [{datetime.now(IST)}] {' '.join(args)}", flush=True)
    subprocess.check_call([sys.executable, "-u"] + args)

def job_daily():
    run_py(["vabot/runner_now.py"])

def job_weekly():
    # Reuse the same runner for now; customize if you add a weekly script
    run_py(["vabot/runner_now.py"])

if __name__ == "__main__":
    print(f"Scheduler starting in IST… now: {datetime.now(IST)}", flush=True)
    sched = BlockingScheduler(timezone=IST)
    # 10:00 IST every day
    sched.add_job(job_daily, CronTrigger(hour=10, minute=0))
    # 00:00 IST every Sunday
    sched.add_job(job_weekly, CronTrigger(day_of_week="sun", hour=0, minute=0))
    sched.start()
