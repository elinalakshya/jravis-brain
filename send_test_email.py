import os, smtplib
from email.mime.text import MIMEText

EMAIL = os.getenv("ELINA_EMAIL")  # sender (Elina's Gmail)
PASSWORD = os.getenv("APP_PASSWORD")  # Gmail app password
RECEIVER = "nrveeresh327@gmail.com"  # your email

msg = MIMEText("Test email from VA Bot ✅")
msg["Subject"] = "VA Bot Test"
msg["From"] = EMAIL
msg["To"] = RECEIVER

with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, RECEIVER, msg.as_string())

print("✅ Test email sent successfully to", RECEIVER)

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email, subject, body, team_member="Elina", system="General"):
    # Sender email and app password from Replit secrets
    from_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    # Build subject line with team member + system
    final_subject = f"[{team_member}] {subject} – {system}"

    # Create email
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = final_subject

    # Build body with details
    final_body = f"""
Team Member: {team_member}
System: {system}

{body}
"""
    msg.attach(MIMEText(final_body, "plain"))

    try:
        # Connect to Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent successfully by {team_member} for {system}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")


# Example test
if __name__ == "__main__":
    send_email("nrveeresh327@gamil.com",
               subject="Support Request",
               body="Need Boss approval for new product launch.",
               team_member="Kael",
               system="Meshy AI Store")
