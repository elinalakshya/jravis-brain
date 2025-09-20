# support_request.py
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_support_request():
    EMAIL = os.getenv("VA_EMAIL")
    APP_PASS = os.getenv("VA_PASSWORD")

    if not EMAIL or not APP_PASS:
        print("❌ Missing VA_EMAIL or VA_PASSWORD in environment variables!")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "StationeryExport Support Request"
    msg["From"] = EMAIL
    msg["To"] = "seller-support@amazon.in"
    msg["Cc"] = "nrveeresh327@gmail.com"

    body = """Boss, this is a support request email from VA Bot."""
    msg.attach(MIMEText(body, "plain"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(EMAIL, APP_PASS)
            server.sendmail(EMAIL, [msg["To"], msg["Cc"]], msg.as_string())
        print("✅ Support email sent successfully")
    except Exception as e:
        print("❌ Error sending support email:", e)


if __name__ == "__main__":
    send_support_request()
