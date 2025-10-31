#!/usr/bin/env python3
"""
email_automation_daemon.py

Sends the latest locked JRAVIS reports via Gmail API using existing token.json credentials.
- Uses the same OAuth token.json you created earlier.
- Attaches the most recent *_locked.pdf files from ./archive.
- Sends to the configured recipient and includes an "Approve" button (mailto link).

Usage:
  # test run once
  python email_automation_daemon.py --once

  # run as daemon: checks every CHECK_INTERVAL seconds and sends once per day
  python email_automation_daemon.py

Config (edit at top) or override via env vars.
"""
import os
import glob
import base64
import time
import argparse
import mimetypes
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# -------- CONFIG --------
TOKEN_FILE = "token.json"  # oauth token you created
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
ARCHIVE_DIR = "./archive"
SENDER_NAME = "JRAVIS Auto Mailer"
SENDER_EMAIL = None  # None => 'me' (uses authenticated Gmail account)
RECIPIENT_EMAIL = "nrveeresh327@gamil.com"  # from model context
MISSION_LOCK_CODE = "2040LOCK"  # include in body (you confirmed same)
CHECK_INTERVAL = 60 * 60  # seconds between checks in daemon mode (1 hour)
SEND_HOUR_IST = 10  # 10 AM IST (server timezone conversion may be needed)
TIMEZONE_OFFSET_HOURS = 5 + 30 / 60  # IST = UTC +5.5 (used only for naive scheduling)
# ------------------------


def auth_gmail():
    """Load credentials from token.json and return gmail service."""
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return service


def find_latest_locked_files(directory, match_suffix="_locked.pdf", top_n=2):
    """Return list of latest files (by mtime) in directory that end with match_suffix."""
    pattern = os.path.join(directory, f"*{match_suffix}")
    files = glob.glob(pattern)
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:top_n]


def make_message_with_attachments(sender, to, subject, html_body, attachments):
    """Create a base64-encoded raw message for Gmail API with attachments."""
    msg = MIMEMultipart()
    from_header = f"{SENDER_NAME} <{sender}>" if sender else SENDER_NAME
    msg["From"] = from_header
    msg["To"] = to
    msg["Subject"] = subject

    msg.attach(MIMEText(html_body, "html"))

    for path in attachments:
        if not os.path.exists(path):
            continue
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(path, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition",
                        f"attachment; filename=\"{os.path.basename(path)}\"")
        msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def send_message(service, message_body):
    """Send message using Gmail API (userId = 'me')."""
    sent = service.users().messages().send(userId="me",
                                           body=message_body).execute()
    return sent


def build_email_html(date_str, attachments, recipient=RECIPIENT_EMAIL):
    """Construct the HTML body including an Approve button (mailto link)."""
    # Approve mailto link — replies to recipient with subject Approve JRAVIS <date>
    approve_subject = f"Approve JRAVIS {date_str}"
    approve_link = f"mailto:{recipient}?subject={approve_subject.replace(' ', '%20')}"
    html = f"""
    <html>
      <body>
        <p>Hi Boss,</p>
        <p>Attached are the encrypted JRAVIS reports for <strong>{date_str}</strong>.</p>
        <p><strong>Mission Lock Code:</strong> {MISSION_LOCK_CODE}</p>
        <p>
          <a href="{approve_link}" style="
            display:inline-block;padding:12px 20px;border-radius:8px;
            background:#1a73e8;color:#fff;text-decoration:none;font-weight:bold;">
            Approve
          </a>
        </p>
        <p>If you prefer to reply manually, reply to this email with subject "<em>Approve JRAVIS {date_str}</em>".</p>
        <hr>
        <small>JRAVIS Auto Mailer — This message includes encrypted attachments.</small>
      </body>
    </html>
    """
    return html


def send_daily_reports_once():
    service = auth_gmail()
    # find attachments (latest locked files)
    locked_files = find_latest_locked_files(ARCHIVE_DIR,
                                            "_locked.pdf",
                                            top_n=5)
    if not locked_files:
        print("[Email] No locked files found; nothing to send.")
        return False

    # choose top 2: summary & invoice (best-effort)
    attachments = locked_files[:2]
    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"JRAVIS Daily Report - {date_str}"
    html_body = build_email_html(date_str, attachments)

    # determine sender email: use authenticated user if SENDER_EMAIL is None
    sender = SENDER_EMAIL or "me"
    msg_body = make_message_with_attachments(
        sender if sender != "me" else get_authenticated_email(service),
        RECIPIENT_EMAIL, subject, html_body, attachments)
    sent = send_message(service, msg_body)
    print("[Email] Sent message id:", sent.get("id"))
    return True


def get_authenticated_email(service):
    """Query Gmail profile to get the authenticated user's email address."""
    profile = service.users().getProfile(userId="me").execute()
    return profile.get("emailAddress")


def run_daemon_loop():
    print(
        "[EmailDaemon] Starting — will try to send once per day at 10:00 IST (server tz conversion may be needed)."
    )
    # crude scheduling: if you want strict 10:00 IST, consider running via cron on server in IST or convert times
    last_sent_date = None
    while True:
        now = datetime.utcnow() + timedelta(
            hours=TIMEZONE_OFFSET_HOURS)  # approximate IST
        today_str = now.strftime("%Y-%m-%d")
        if last_sent_date != today_str and now.hour >= SEND_HOUR_IST:
            try:
                ok = send_daily_reports_once()
                if ok:
                    last_sent_date = today_str
            except Exception as e:
                print("[EmailDaemon][ERROR]", e)
        time.sleep(CHECK_INTERVAL)


def parse_args_and_run():
    p = argparse.ArgumentParser()
    p.add_argument("--once",
                   action="store_true",
                   help="Send email once and exit")
    args = p.parse_args()
    if args.once:
        send_daily_reports_once()
    else:
        run_daemon_loop()


if __name__ == "__main__":
    parse_args_and_run()
