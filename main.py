
from login_manager import get_login
import os, json, threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

import pdfkit
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path

# ==============================
# CONFIG — Secrets & constants
# ==============================

TZ = ZoneInfo("Asia/Kolkata")  # Always IST
STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)

# Sender accounts (READ FROM REPLIT SECRETS)
SENDER_DEFAULT_EMAIL = os.getenv("ELINA_EMAIL")  # Primary bot sender (Elina)
SENDER_DEFAULT_PASS = os.getenv("APP_PASSWORD")  # 16-char Gmail app password
BOSS_EMAIL = os.getenv("MY_EMAIL")  # You

# PDF toolkit
WKHTMLTOPDF_PATH = "/nix/store/hxiay4lkq4389vxnhnb3d0pbaw6siwkw-wkhtmltopdf/bin/wkhtmltopdf"
PDF_LOCK_CODE = "MY OG"

# Storage
OUT_DIR = Path("out")
OUT_DIR.mkdir(exist_ok=True)

# ==============================
# Flask App
# ==============================
app = Flask(__name__)

# ==============================
# Routes
# ==============================
@app.route("/")
def home():
    return "✅ VA Bot is running!"

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(TZ).isoformat()
    })

@app.route("/test")
def test():
    return "📧 Test endpoint - VA Bot is alive!"

# ==============================
# Scheduler
# ==============================
scheduler = BackgroundScheduler(timezone=TZ)

def daily_report_job():
    """Daily report job at 10:00 AM IST"""
    try:
        print("⏰ Running daily report job...")
        # This would connect to the actual report generation
        # For now, just log that it's running
        print("✅ Daily report job completed")
    except Exception as e:
        print(f"❌ Daily report job failed: {e}")

# Schedule daily job
scheduler.add_job(daily_report_job, CronTrigger(hour=10, minute=0))

def run():
    """Main application runner"""
    scheduler.start()
    print("✅ Scheduler started - daily reports at 10:00 AM IST")
    
    # Run Flask app
    port = int(os.getenv("PORT", 5000))  # Use port 5000 for Replit
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    run()


import os
def print_public_url():
    slug = os.getenv("REPL_SLUG", "project")
    owner = os.getenv("REPL_OWNER", "user")
    url = f"https://{slug}.{owner}.repl.co/"
    print(f"\n🚀 Jarvis Dashboard is live at: {url}dashboard\n")

print_public_url()


if __name__ == "__main__":
    print("✅ Scheduler started - daily reports at 10:00 AM IST")
    print_public_url()
    app.run(port=8080, host="0.0.0.0")

