#!/usr/bin/env python3
"""
auto_backup_cloud.py
JRAVIS Cloud Backup System (Sub-Phase 1B – Safety Layer)

Features:
- Creates time-stamped backups every 6 hours
- Keeps last 7 days (auto deletes older)
- Compresses folders into .zip archives
- Sends optional backup confirmation email
"""

import os
import shutil
import time
import zipfile
import schedule
import pytz
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

# ------------------------------------------
# CONFIGURATION
# ------------------------------------------
SMTP_USER = os.getenv("SMTP_USER", "elinalakshya@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")
RECEIVER_EMAIL = os.getenv("REPORT_RECIPIENT", "nrveeresh327@gmail.com")
SENDER_NAME = os.getenv("FROM_NAME", "JRAVIS BOT")

BACKUP_ROOT = os.path.join(os.getcwd(), "cloud_backups")
SOURCE_DIRS = [
    os.path.join(os.getcwd(), "PDFs"),
    os.path.join(os.getcwd(), "backups"),
    os.path.join(os.getcwd(), "logs"),
]
KEEP_DAYS = 7
SEND_EMAIL_REPORT = True
IST = pytz.timezone("Asia/Kolkata")


# ------------------------------------------
# UTILITIES
# ------------------------------------------
def log(msg: str):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{now}] {msg}")


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def cleanup_old_backups():
    """Delete backup folders older than KEEP_DAYS."""
    now = datetime.now()
    removed = 0
    for item in os.listdir(BACKUP_ROOT):
        full_path = os.path.join(BACKUP_ROOT, item)
        if os.path.isdir(full_path):
            try:
                dt = datetime.strptime(item, "%Y-%m-%d_%H-%M")
            except ValueError:
                continue
            if now - dt > timedelta(days=KEEP_DAYS):
                shutil.rmtree(full_path, ignore_errors=True)
                removed += 1
    if removed:
        log(f"🧹 Cleaned up {removed} old backup folders.")


def zip_folder(folder_path, zip_path):
    """Compress folder to zip file."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, folder_path)
                zipf.write(abs_path, rel_path)


def send_backup_email(summary_text, zip_file_path=None):
    """Optional: send email with summary and attached .zip file."""
    if not SMTP_USER or not SMTP_PASS or not SEND_EMAIL_REPORT:
        log("📧 Email report skipped (config disabled or missing creds).")
        return

    msg = EmailMessage()
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "JRAVIS Auto Backup Report"
    msg.set_content(summary_text)

    if zip_file_path and os.path.exists(zip_file_path):
        with open(zip_file_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="zip",
                filename=os.path.basename(zip_file_path),
            )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

    log("✅ Backup report email sent.")


# ------------------------------------------
# CORE BACKUP ROUTINE
# ------------------------------------------
def perform_backup():
    """Run full backup cycle."""
    log("🚀 Starting JRAVIS auto backup...")

    now = datetime.now(IST)
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    backup_dir = os.path.join(BACKUP_ROOT, timestamp)
    ensure_dir(backup_dir)

    copied = []
    for src in SOURCE_DIRS:
        if os.path.exists(src):
            dest = os.path.join(backup_dir, os.path.basename(src))
            try:
                shutil.copytree(src, dest)
                copied.append(dest)
                log(f"📦 Backed up: {src} → {dest}")
            except Exception as e:
                log(f"⚠️  Failed to backup {src}: {e}")
        else:
            log(f"⚠️  Source not found: {src}")

    # Zip the backup for compact storage
    zip_path = os.path.join(BACKUP_ROOT, f"{timestamp}.zip")
    zip_folder(backup_dir, zip_path)
    log(f"🗜  Compressed backup → {zip_path}")

    cleanup_old_backups()

    summary = (f"JRAVIS Auto Backup Completed ✅\n"
               f"Time: {timestamp}\n"
               f"Backed up {len(copied)} folders.\n\n"
               f"Files saved in: {zip_path}\n"
               f"Old backups older than {KEEP_DAYS} days cleaned.")

    send_backup_email(summary, zip_file_path=zip_path)
    log("🌇 Backup process completed.\n")


# ------------------------------------------
# SCHEDULER
# ------------------------------------------
def schedule_backup():
    """Schedule backup every 6 hours."""
    schedule.every(6).hours.do(perform_backup)
    log("⏰ Scheduled JRAVIS Auto Backup every 6 hours.")
    perform_backup()  # immediate first run
    while True:
        schedule.run_pending()
        time.sleep(60)


# ------------------------------------------
# MAIN ENTRY
# ------------------------------------------
if __name__ == "__main__":
    ensure_dir(BACKUP_ROOT)
    log("JRAVIS Auto Backup Cloud System Active ☁️")
    schedule_backup()
