import time, subprocess, datetime

TARGET_HOUR_IST = 10
OFFSET = 5.5  # IST offset from UTC


def wait_until_target():
    while True:
        now_utc = datetime.datetime.utcnow()
        ist = now_utc + datetime.timedelta(hours=OFFSET)
        if ist.hour == TARGET_HOUR_IST and ist.minute == 0:
            print("⏰ 10:00 AM IST reached — sending JRAVIS email...")
            subprocess.run(
                ["python", "jravis_email_sender.py", "--dir", "./archive"])
            time.sleep(60 * 60)  # sleep one hour to avoid duplicate runs
        time.sleep(60)


os.system("python auto_dashboard_trigger.py")
os.system("python email_automation_daemon.py --weekly")

if __name__ == "__main__":
    print("🕓 JRAVIS Auto-Scheduler running — waiting for 10:00 AM IST...")
    wait_until_target()
