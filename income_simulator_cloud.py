#!/usr/bin/env python3
"""
income_simulator_cloud.py
JRAVIS Cloud Income Engine — Sub-Phase 1C (Simulation Mode)

Generates realistic daily income reports for 30 passive systems.
After Phase 2 activation, this will switch to real API data.
"""

import os
import csv
import random
import pytz
import time
import smtplib
import schedule
from datetime import datetime
from email.message import EmailMessage

# ----------------------------
# CONFIGURATION
# ----------------------------
SMTP_USER = os.getenv("SMTP_USER", "elinalakshya@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")
RECEIVER_EMAIL = os.getenv("REPORT_RECIPIENT", "nrveeresh327@gmail.com")
SENDER_NAME = os.getenv("FROM_NAME", "JRAVIS BOT")

LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "income_log.csv")
IST = pytz.timezone("Asia/Kolkata")

STREAMS = [
    "Etsy Stationery", "Fiverr Design", "Printify Shop", "YouTube Ads",
    "Affiliate 1", "Affiliate 2", "E-book Sales", "Gumroad Store",
    "Stock Photos", "Templates Hub", "Course 1", "Course 2", "Course 3",
    "Job Automation #1", "Job Automation #2", "Digital Assets #1",
    "Digital Assets #2", "Consulting AI Bot", "VA Services USA",
    "VA Services EU", "VA Services India", "Passive Tools #1",
    "Passive Tools #2", "Passive Tools #3", "Marketing Bot #1",
    "Marketing Bot #2", "Stationery Exports", "Ad Revenue #1", "Ad Revenue #2",
    "Other Stream"
]


# ----------------------------
# UTILITIES
# ----------------------------
def log(msg: str):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{now}] {msg}")


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def send_email(subject, body):
    """Send plain-text email report."""
    if not SMTP_USER or not SMTP_PASS:
        log("⚠️  Email skipped (missing credentials).")
        return
    msg = EmailMessage()
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
    log("✅ Daily income report email sent.")


# ----------------------------
# CORE LOGIC
# ----------------------------
def simulate_daily_income():
    """Generate random but realistic daily income across 30 streams."""
    ensure_dir(LOG_DIR)
    date_str = datetime.now(IST).strftime("%Y-%m-%d")
    results = []
    total = 0.0

    for stream in STREAMS:
        # Random daily earning between ₹500 and ₹2500 equivalent (≈ $6–$30)
        value = round(random.uniform(6.0, 30.0), 2)
        results.append((date_str, stream, value))
        total += value

    # Append to CSV log
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Stream", "Income_USD"])
        writer.writerows(results)

    log(f"💰 Generated income for {len(STREAMS)} streams — Total ${total:.2f}")

    # Create summary text
    summary_lines = [
        f"JRAVIS Daily Income Simulation — {date_str}",
        "----------------------------------------------",
        *(f"{s}: ${v:.2f}" for _, s, v in results),
        "----------------------------------------------",
        f"Total Simulated Earnings: ${total:.2f}", "",
        "Next: data will auto-sync with weekly report & backup modules."
    ]
    summary = "\n".join(summary_lines)

    send_email(subject=f"JRAVIS Simulated Income — {date_str}", body=summary)


# ----------------------------
# SCHEDULER
# ----------------------------
def schedule_daily_income():
    """Runs once daily at 10:00 PM IST."""
    schedule.every().day.at("22:00").do(simulate_daily_income)
    log("🕙 Scheduled income simulation daily at 10:00 PM IST.")
    simulate_daily_income()  # immediate test run
    while True:
        schedule.run_pending()
        time.sleep(60)


# ----------------------------
# MAIN ENTRY
# ----------------------------
if __name__ == "__main__":
    log("JRAVIS Income Simulator Cloud Active ☁️")
    schedule_daily_income()
