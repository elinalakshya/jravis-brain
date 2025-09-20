# alert_guard.py — pause-all + email-on-alert (simple)

import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

# ---- Config (reads from Replit Secrets) ----
TZ = ZoneInfo("Asia/Kolkata")

# Prefer your existing bot creds if present, else fall back to generic names
SENDER_EMAIL = os.getenv("ELINA_EMAIL") or os.getenv("EMAIL")
SENDER_PASS  = os.getenv("APP_PASSWORD") or os.getenv("APP_PASS")
BOSS_EMAIL   = os.getenv("MY_EMAIL") or os.getenv("BOSS_EMAIL")

# Suspend flag path
SUSPEND_FILE = Path("SUSPEND.flag")


# ---------- Public API ----------

def is_paused() -> bool:
    """Return True if bot is currently paused (SUSPEND.flag exists)."""
    return SUSPEND_FILE.exists()


def alert_and_pause(subject: str, html_message: str, pause: bool = True):
    """
    Create pause flag (optional) and send an alert email to boss.
    Use for any 'error or fishy' situation.
    """
    if pause:
        SUSPEND_FILE.write_text(f"Paused @ {now_ist_str()} | {subject}", encoding="utf-8")

    # If email config missing, fail silently but keep the pause
    if not (SENDER_EMAIL and SENDER_PASS and BOSS_EMAIL):
        print("⚠️ alert_guard: missing email secrets; paused but no email sent.")
        return

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = BOSS_EMAIL
    msg["Subject"] = f"[ALERT] {subject}"
    body = f"""<h3>⚠️ VA Bot Alert</h3>
<p>{html_message}</p>
<p><b>Time (IST):</b> {now_ist_str()}</p>
<p><i>Auto-action:</i> {'Paused' if pause else 'Not paused'}</p>"""
    msg.attach(MIMEText(body, "html"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, [BOSS_EMAIL], msg.as_string())
        print("✅ alert_guard: alert email sent.")
    except Exception as e:
        print(f"❌ alert_guard: failed to send alert email: {e}")


def resume():
    """Clear pause flag to resume work."""
    if SUSPEND_FILE.exists():
        SUSPEND_FILE.unlink()
        print("✅ alert_guard: resumed (pause flag cleared).")


# ---------- Helpers ----------

def now_ist_str() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
