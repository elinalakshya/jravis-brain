import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz


# -----------------------------
# Email Sending Logic
# -----------------------------
def send_daily_report():
    EMAIL = os.getenv("EMAIL")  # Sender Gmail
    APP_PASS = os.getenv("APP_PASS")  # Gmail App Password
    TO_EMAIL = "nrveeresh327@gmail.com"  # Boss' email

    if not EMAIL or not APP_PASS:
        print("❌ Missing EMAIL or APP_PASS in environment variables!")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "✅ VA Bot Daily Report"
    msg["From"] = EMAIL
    msg["To"] = TO_EMAIL

    now = datetime.now(
        pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M %p IST")

    text = f"Boss, this is your VA Bot Daily Report for {now}."
    html = f"""
    <html>
      <body>
        <h2>✅ VA Bot Daily Report</h2>
        <p>Boss,</p>
        <p>VA Bot ran successfully at {now} and is keeping Mission 2040 alive 🚀</p>
        <p>- Dhruvayu</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465,
                              context=context) as server:
            server.login(EMAIL, APP_PASS)
            server.sendmail(EMAIL, TO_EMAIL, msg.as_string())
        print(f"✅ Daily report email sent successfully to {TO_EMAIL} at {now}")
    except Exception as e:
        print("❌ Error sending daily report:", e)


# -----------------------------
# APScheduler Job
# -----------------------------
scheduler = BlockingScheduler(timezone="Asia/Kolkata")


# Run every day at 10:00 AM IST
@scheduler.scheduled_job("cron", hour=10, minute=0)
def scheduled_task():
    send_daily_report()


if __name__ == "__main__":
    print("🚀 VA Bot Daily Scheduler started (IST)")
    scheduler.start()
