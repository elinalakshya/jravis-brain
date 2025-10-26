#!/usr/bin/env python3
"""
weekly_summary_cloud.py

Purpose:
- Gather last 7 days of PDFs (reports & invoices)
- Merge into a single Weekly Summary PDF
- Encrypt summary (if LOCK_CODE provided)
- Email the summary + invoices to RECEIVER_EMAIL
- Backup all involved files into /backups/week_<YYYY-MM-DD>/

Usage:
- Run once for test:
    python weekly_summary_cloud.py --run-now

- Run continuously (cloud worker):
    python weekly_summary_cloud.py
"""

import os
import sys
import argparse
import smtplib
import shutil
import schedule
import time
import pytz
from datetime import datetime, timedelta
from email.message import EmailMessage
from PyPDF2 import PdfReader, PdfWriter

# -------------------------
# Configuration (env / defaults)
# -------------------------
SMTP_USER = os.getenv("SMTP_USER", "elinalakshya@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")  # Must be set as secret (app password)
RECEIVER_EMAIL = os.getenv("REPORT_RECIPIENT", "nrveeresh327@gmail.com")
SENDER_NAME = os.getenv("FROM_NAME", "JRAVIS Bot")
LOCK_CODE = os.getenv("LOCK_CODE",
                      None)  # Optional password to encrypt weekly summary
WORK_DIR = os.getenv("WORK_DIR", os.getcwd())
BACKUP_ROOT = os.path.join(WORK_DIR, "backups")
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "7"))
IST = pytz.timezone("Asia/Kolkata")

# Filenames pattern expectations (adjust if you use different names)
# This script relies on file mtimes rather than strict filename date parsing.
VALID_EXTS = (".pdf", )

# Output weekly summary name
WEEKLY_SUMMARY_NAME = "weekly_summary.pdf"
WEEKLY_SUMMARY_LOCKED = "weekly_summary_locked.pdf"


# -------------------------
# Helpers
# -------------------------
def log(*args, **kwargs):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{now}]", *args, **kwargs)


def find_files_modified_within(days=7, root=WORK_DIR):
    """
    Return list of file paths with PDF extension modified within last `days`.
    """
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    found = []
    for dirpath, _, filenames in os.walk(root):
        # skip backup folder to avoid recursion
        if os.path.abspath(dirpath).startswith(os.path.abspath(BACKUP_ROOT)):
            continue
        for fn in filenames:
            if not fn.lower().endswith(VALID_EXTS):
                continue
            path = os.path.join(dirpath, fn)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
            except Exception:
                continue
            if mtime >= cutoff:
                found.append(path)
    return sorted(found)


def merge_pdfs(pdf_paths, out_path):
    """Merge PDFs in given order into out_path"""
    writer = PdfWriter()
    for p in pdf_paths:
        try:
            reader = PdfReader(p)
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            log("Warning: failed to read PDF", p, ":", e)
    with open(out_path, "wb") as f:
        writer.write(f)
    log("Merged", len(pdf_paths), "PDF(s) ->", out_path)
    return out_path


def encrypt_pdf(input_path, output_path, password):
    """Encrypt input_path -> output_path with password using PyPDF2"""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with open(output_path, "wb") as f:
        writer.write(f)
    log("Encrypted PDF written to", output_path)
    return output_path


def send_email(subject, body, attachments):
    """Send email with attachments via Gmail SMTP (SSL)."""
    if not SMTP_USER or not SMTP_PASS:
        raise ValueError(
            "SMTP_USER or SMTP_PASS not set. Add them to environment/secrets.")
    msg = EmailMessage()
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    for path in attachments:
        if not os.path.exists(path):
            log("Attachment not found, skipping:", path)
            continue
        with open(path, "rb") as f:
            data = f.read()
        maintype = "application"
        subtype = "pdf"
        filename = os.path.basename(path)
        msg.add_attachment(data,
                           maintype=maintype,
                           subtype=subtype,
                           filename=filename)

    # Send via Gmail SSL
    log("Connecting to SMTP and sending email to", RECEIVER_EMAIL)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
    log("Email sent.")


def ensure_backup_folder(target_root):
    os.makedirs(target_root, exist_ok=True)


def backup_files(file_paths, target_dir):
    ensure_backup_folder(target_dir)
    copied = []
    for p in file_paths:
        try:
            dest = os.path.join(target_dir, os.path.basename(p))
            shutil.copy2(p, dest)
            copied.append(dest)
        except Exception as e:
            log("Backup failed for", p, ":", e)
    return copied


# -------------------------
# Core weekly run
# -------------------------
def weekly_run(dry_run=False):
    log("Starting weekly summary run (lookback days =", LOOKBACK_DAYS, ")")
    files = find_files_modified_within(days=LOOKBACK_DAYS)
    if not files:
        log("No PDFs found in last", LOOKBACK_DAYS, "days. Exiting.")
        return {"status": "no_files", "files": []}

    # Separate invoice-like and report-like if desired, but we will include all found PDFs
    log("Found PDFs:", *files, sep="\n  - ")
    # Create a temp folder for weekly build
    timestamp = datetime.now(IST).strftime("%Y-%m-%d")
    weekly_folder_name = f"week_{timestamp}"
    weekly_backup_dir = os.path.join(BACKUP_ROOT, weekly_folder_name)
    os.makedirs(weekly_backup_dir, exist_ok=True)

    # Build merged weekly summary
    merged_path = os.path.join(WORK_DIR, WEEKLY_SUMMARY_NAME)
    # If exists, remove old
    if os.path.exists(merged_path):
        try:
            os.remove(merged_path)
        except Exception:
            pass

    merge_pdfs(files, merged_path)

    final_summary_path = merged_path

    # Encrypt if LOCK_CODE provided
    encrypted_path = None
    if LOCK_CODE:
        encrypted_path = os.path.join(WORK_DIR, WEEKLY_SUMMARY_LOCKED)
        try:
            encrypt_pdf(merged_path, encrypted_path, LOCK_CODE)
            final_summary_path = encrypted_path
        except Exception as e:
            log("Error encrypting PDF:", e)
            # fallback to non-encrypted summary

    # Backup original files and the final summary
    files_to_backup = list(files)
    files_to_backup.append(final_summary_path)
    backed = backup_files(files_to_backup, weekly_backup_dir)
    log("Backed up", len(backed), "files to", weekly_backup_dir)

    # Send email
    subject = f"JRAVIS Weekly Summary — {timestamp}"
    body = (
        f"JRAVIS Weekly Summary for week ending {timestamp}.\n\n"
        "- Attached: Weekly summary PDF + source PDFs from the last {days} days.\n\n"
        "This message was auto-generated by JRAVIS.")
    # NOTE: fix mistake: use LOOKBACK_DAYS not days variable
    body = (
        f"JRAVIS Weekly Summary for week ending {timestamp}.\n\n"
        f"- Attached: Weekly summary PDF + source PDFs from the last {LOOKBACK_DAYS} days.\n\n"
        "This message was auto-generated by JRAVIS.")

    attachments = [final_summary_path] + files
    if dry_run:
        log("Dry-run mode ON. Would send email with attachments:", attachments)
        return {
            "status": "dry_run",
            "attachments": attachments,
            "backed_up": backed
        }

    try:
        send_email(subject, body, attachments)
    except Exception as e:
        log("Failed to send email:", e)
        return {"status": "email_failed", "error": str(e), "backed_up": backed}

    log("Weekly summary run completed successfully.")
    return {"status": "ok", "attachments": attachments, "backed_up": backed}


# -------------------------
# Scheduler
# -------------------------
def schedule_weekly():
    # schedule for Sunday 00:00 IST
    # schedule library runs in local time; we'll compute the next time offset
    # To run weekly at Sunday 00:00 IST, we set up a job that checks every minute and
    # triggers when local time (UTC environment) matches target IST time.
    TARGET_HOUR = 0
    TARGET_MINUTE = 0

    def trigger_if_ist_sunday_midnight():
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        now_ist = now_utc.astimezone(IST)
        if now_ist.weekday(
        ) == 6 and now_ist.hour == TARGET_HOUR and now_ist.minute == TARGET_MINUTE:
            log("IST Sunday 00:00 detected; running weekly job.")
            try:
                weekly_run()
            except Exception as e:
                log("Error during scheduled weekly_run:", e)

    # check every 60 seconds
    schedule.every(60).seconds.do(trigger_if_ist_sunday_midnight)
    log("Scheduled weekly check (every 60 seconds) for Sunday 00:00 IST.")


# -------------------------
# CLI
# -------------------------
def parse_args():
    p = argparse.ArgumentParser(description="JRAVIS Weekly Summary Cloud")
    p.add_argument("--run-now",
                   action="store_true",
                   help="Run the weekly job immediately (for testing).")
    p.add_argument("--dry-run",
                   action="store_true",
                   help="Do everything except send email.")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    log("JRAVIS Weekly Summary Cloud starting...")

    # quick sanity checks for SMTP credentials (email sending)
    if not SMTP_USER or not SMTP_PASS:
        log("Warning: SMTP_USER or SMTP_PASS missing. Email sending will fail. Set secrets and restart."
            )

    if args.run_now:
        log("Running immediate weekly job (run-now).")
        res = weekly_run(dry_run=args.dry_run)
        log("Immediate run result:", res)
        sys.exit(0)

    # otherwise run scheduler continuously
    schedule_weekly()
    log("Entering scheduler loop. Press Ctrl+C to exit.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log("Shutting down weekly_summary_cloud.py by user.")
