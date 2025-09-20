import os
import smtplib
import ssl
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz


def send_daily_report():
    """Build and send the VA Bot daily report via Gmail."""

    EMAIL = os.getenv("VA_EMAIL")
    APP_PASS = os.getenv("VA_PASSWORD")
    TO_EMAIL = "nrveeresh327@gmail.com"

    if not EMAIL or not APP_PASS:
        print("❌ Missing VA_EMAIL or VA_PASSWORD in environment variables!")
        return

    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    now_str = now.strftime("%d-%m-%Y %I:%M %p IST")

    # Load last logs (if available)
    log_file = "logs/phase1_log.csv"
    if os.path.exists(log_file):
        try:
            log_data = pd.read_csv(log_file).tail(10).to_html(index=False)
        except Exception as e:
            log_data = f"<p>⚠️ Error reading logs: {e}</p>"
    else:
        log_data = "<p>No logs yet.</p>"

    # Build the email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"✅ VA Bot Daily Report – {now_str}"
    msg["From"] = EMAIL
    msg["To"] = TO_EMAIL

    text = f"Boss, here’s your daily report at {now_str}."
    html = f"""
    <html>
      <body>
        <h2>✅ VA Bot Daily Report</h2>
        <p>Boss, VA Bot is running 24/7 and executed the workflow.</p>
        <p><b>Latest Logs:</b></p>
        {log_data}
        <p>🚀 Mission 2040 on track.</p>
        <p>- Dhruvayu</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    # Send the email via Gmail SMTP
    try:
        print(f"📧 Connecting to Gmail as {EMAIL}...")
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465,
                              context=context) as server:
            server.login(EMAIL, APP_PASS)
            server.sendmail(EMAIL, TO_EMAIL, msg.as_string())
        print(f"✅ Daily report email sent successfully at {now_str}")
    except Exception as e:
        print(f"❌ Error sending daily report: {e}")


if __name__ == "__main__":
    print("🚀 Sending daily report (no Flask)...")
    send_daily_report()
