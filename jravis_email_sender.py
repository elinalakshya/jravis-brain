import os, glob, smtplib, mimetypes
from email.message import EmailMessage
from datetime import datetime

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "elinalakshya@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS")  # your Gmail app password
EMAIL_FROM = os.getenv("EMAIL_FROM",
                       "JRAVIS Auto Mailer <elinalakshya@gmail.com>")
EMAIL_TO = os.getenv("EMAIL_TO", "nrveeresh327@gamil.com")


def find_locked_files(directory):
    return sorted(glob.glob(os.path.join(directory, "*_locked.pdf")),
                  key=os.path.getmtime,
                  reverse=True)[:2]


def send_email_with_attachments(directory="./archive"):
    files = find_locked_files(directory)
    if not files:
        print("❌ No locked PDF files found.")
        return
    date_str = datetime.now().strftime("%Y-%m-%d")
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = f"JRAVIS Daily Report - {date_str}"
    msg.set_content(
        f"Hi Boss,\n\nAttached are the encrypted JRAVIS reports for {date_str}.\n\nLock Code: 2040LOCK\n\n-- JRAVIS Auto Mailer"
    )

    for path in files:
        ctype, _ = mimetypes.guess_type(path)
        maintype, subtype = (ctype or "application/pdf").split("/", 1)
        with open(path, "rb") as f:
            msg.add_attachment(f.read(),
                               maintype=maintype,
                               subtype=subtype,
                               filename=os.path.basename(path))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    print(f"✅ Email sent successfully with {len(files)} attachments.")


if __name__ == "__main__":
    send_email_with_attachments("./archive")
