# connect_elina.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ELINA_EMAIL = os.environ.get("ELINA_EMAIL")
ELINA_PASS = os.environ.get("ELINA_PASS")
ELINA_PASS_ALT = os.environ.get("ELINA_PASS_ALT")


def connect_elina_email():
    """
    Connects to Gmail SMTP using ELINA_PASS first, falls back to ELINA_PASS_ALT if needed.
    Returns the SMTP connection object if successful.
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    for password in [ELINA_PASS, ELINA_PASS_ALT]:
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(ELINA_EMAIL, password)
            print(
                f"[Email] Connected successfully using {'primary' if password == ELINA_PASS else 'alternative'} password"
            )
            return server
        except smtplib.SMTPAuthenticationError:
            print(
                f"[Email] Failed to connect using {'primary' if password == ELINA_PASS else 'alternative'} password"
            )
        except Exception as e:
            print(f"[Email] Unexpected error: {e}")
    raise Exception("Unable to connect to Elina's Gmail with both passwords")


# Example usage:
if __name__ == "__main__":
    server = connect_elina_email()
    # You can now send a test email if needed
    msg = MIMEMultipart()
    msg['From'] = ELINA_EMAIL
    msg['To'] = ELINA_EMAIL  # send test to self
    msg['Subject'] = "VA Bot Test Email"
    msg.attach(MIMEText("This is a test email from VA Bot.", 'plain'))
    try:
        server.send_message(msg)
        print("[Email] Test email sent successfully")
    except Exception as e:
        print(f"[Email] Failed to send test email: {e}")
    finally:
        server.quit()
