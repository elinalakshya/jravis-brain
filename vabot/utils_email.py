"""
Email utility for VA Bot alerts
"""

import os
import smtplib
from email.mime.text import MIMEText

EMAIL = os.getenv("EMAIL")
APP_PASS = os.getenv("APP_PASS")
TO_EMAIL = "nrveeresh327@gmail.com"  # Boss


def send_alert_email(errors):
    msg = MIMEText("\n".join(errors))
    msg["Subject"] = "❌ VA Bot Alert - Failures Detected"
    msg["From"] = EMAIL
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, APP_PASS)
        server.sendmail(EMAIL, TO_EMAIL, msg.as_string())

    print("📧 Alert email sent to Boss!")
