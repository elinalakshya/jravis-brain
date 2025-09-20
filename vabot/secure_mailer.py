"""
Secure Mailer with Mission 2040 protection
- Code lock (MY OG)
- Rotating token (OTP-like)
- Safe PayPal lock
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from vabot.security import verify_code, verify_token, generate_token

EMAIL = os.getenv("EMAIL")  # Sender Gmail
APP_PASS = os.getenv("APP_PASS")  # Gmail App Password
TO_EMAIL = os.getenv("TO_EMAIL",
                     "nrveeresh327@gmail.com")  # Always Boss' PayPal email


def send_secure_email(subject: str, body: str, boss_code: str,
                      boss_token: str):
    """
    Send email ONLY if boss code and token are valid.
    """
    if not verify_code(boss_code):
        raise PermissionError("❌ Invalid Boss code. Access denied.")

    if not verify_token("VA_BOT_SECRET", boss_token):
        raise PermissionError("❌ Invalid OTP token. Secure lock engaged.")

    # Email setup
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL, APP_PASS)
        server.sendmail(EMAIL, TO_EMAIL, msg.as_string())

    return "✅ Secure email sent to Boss."


if __name__ == "__main__":
    print("🔐 Secure Mailer Test")
    print("Generated token:", generate_token("VA_BOT_SECRET"))

    # Example manual test
    code = input("Enter Boss code: ")
    token = input("Enter OTP token: ")
    try:
        status = send_secure_email("Mission 2040 Test",
                                   "This is a secure test.", code, token)
        print(status)
    except Exception as e:
        print(e)
