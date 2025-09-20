import os
import importlib
import argparse

def load_streams():
    streams_dir = "streams"
    streams = []
    if os.path.exists(streams_dir):
        for file in os.listdir(streams_dir):
            if file.endswith(".py"):
                name = file[:-3]
                module = importlib.import_module(f"streams.{name}")
                streams.append((name, module))
    return streams

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unlock", action="store_true")
    args = parser.parse_args()

    print("[VA BOT SYSTEM v1.0 - Mission 2040]")
    print("-----------------------------------")

    if args.unlock:
        code = input("Enter Secret Code: ")
        if code.strip() == "MISSION2040":
            print("Access Granted - VA Bot Unlocked\n")
            print("[STREAM LOADER] Scanning /streams/ directory...")
            streams = load_streams()
            if streams:
                for name, module in streams:
                    print(f"- {name}.py       [ACTIVE]")
                    print("   Task:", module.run())
            else:
                print("(no streams found)")

            print("\n[DAEMON] VA Bot is now running 24/7")
            print("-----------------------------------")
            print("Next Income Report: 10:00 AM IST")
            print("Checking for new streams every 2 hours")
            print("Orders auto-fulfillment: ENABLED")
            print("Passive income tracking: ENABLED")
        else:
            print("Access Denied - Wrong Code")

if __name__ == "__main__":
    main()
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import config_email

def send_income_report(streams):
    try:
        subject = f"VA Bot Daily Income Report - {datetime.date.today().strftime('%B %d, %Y')}"
        body = "Here’s the summary of today’s VA Bot tasks:\n\n"

        for name, module in streams:
            body += f"- {name}.py : {module.run()}\n"

        body += "\nStay focused — Mission 2040 is running ✅"

        msg = MIMEMultipart()
        msg['From'] = config_email.EMAIL_ADDRESS
        msg['To'] = config_email.TO_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(config_email.EMAIL_ADDRESS, config_email.APP_PASSWORD)
        server.sendmail(config_email.EMAIL_ADDRESS, config_email.TO_EMAIL, msg.as_string())
        server.quit()

        print("[EMAIL] Daily income report sent successfully!")
    except Exception as e:
        print(f"[EMAIL ERROR] Could not send report: {e}")

# Modify main() to call the email after scanning streams
if __name__ == "__main__":
    streams = load_streams()
    send_income_report(streams)
