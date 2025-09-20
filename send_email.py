import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Load secrets
EMAIL = os.environ.get("EMAIL")
APP_PASS = os.environ.get("APP_PASS")

if not EMAIL or not APP_PASS:
    raise ValueError(
        "❌ Gmail EMAIL and APP_PASS must be set in Replit Secrets.")

# Dates
today = datetime.now()
yesterday = today - timedelta(days=1)

today_str = today.strftime("%d-%m-%Y")
yesterday_str = yesterday.strftime("%d-%m-%Y")

# Create message
msg = MIMEMultipart()
msg["From"] = EMAIL
msg["To"] = "nrveeresh327@gmail.com"
msg["Subject"] = f"VA BOT Daily Report – {today_str}"

body = f"""
Hello Boss 👑,

✅ Yesterday ({yesterday_str}) Summary:
- Task A completed
- Task B completed
- Task C had an issue (retry today)

📌 Today ({today_str}) Plan:
- Run System 1 (Elina Instagram Reels)
- Upload new Printify designs
- Generate invoices
- Send approval request

🔮 Tomorrow ({(today + timedelta(days=1)).strftime('%d-%m-%Y')}) Preview:
- Continue automation testing
- Add Phase 2 income streams

-- 
Your VA BOT 🤖
"""

msg.attach(MIMEText(body, "plain"))

# Send mail
try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, APP_PASS)
    server.sendmail(EMAIL, "nrveeresh327@gmail.com", msg.as_string())
    server.quit()
    print("✅ Daily email sent successfully to Boss!")
except Exception as e:
    print(f"❌ Failed to send email: {e}")
