#!/usr/bin/env python3
"""
health_check.py
- Check list of service endpoints.
- If an endpoint fails (HTTP not 200) after retries:
   - Send alert email
   - Trigger a restart via Render API for that service id
Env vars required:
  - RENDER_API_KEY (Render service API key)
  - SERVICE_CHECKS (JSON string: [{"id":"crn-...","name":"jravis-backend","url":"https://.../health"} , ...])
  - SENDGRID_API_KEY (optional, for email alerts)
  - ALERT_EMAIL_TO, ALERT_EMAIL_FROM (if using SendGrid)
  - MAX_RETRIES (optional, default 2)
  - RETRY_DELAY (seconds, optional default 10)
  - DRY_RUN (optional, "1" to not trigger restarts)
"""
import os, json, time, requests, sys

RENDER_API_KEY = os.getenv("RENDER_API_KEY")
SERVICE_CHECKS = os.getenv("SERVICE_CHECKS")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", ALERT_EMAIL_TO)
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "10"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

HEADERS_RENDER = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json"
}

import os, smtplib
from email.message import EmailMessage


def send_email(subject, content):
    # Try SendGrid first (existing)
    sg_key = os.getenv("SENDGRID_API_KEY")
    to = os.getenv("ALERT_EMAIL_TO")
    sender = os.getenv("ALERT_EMAIL_FROM", to)
    if sg_key and to:
        try:
            import requests
            url = "https://api.sendgrid.com/v3/mail/send"
            payload = {
                "personalizations": [{
                    "to": [{
                        "email": to
                    }],
                    "subject": subject
                }],
                "from": {
                    "email": sender
                },
                "content": [{
                    "type": "text/plain",
                    "value": content
                }]
            }
            r = requests.post(url,
                              json=payload,
                              headers={
                                  "Authorization": f"Bearer {sg_key}",
                                  "Content-Type": "application/json"
                              },
                              timeout=15)
            print("SendGrid status:", r.status_code)
            if 200 <= r.status_code < 300:
                return
            print("SendGrid failed, falling back to SMTP.")
        except Exception as e:
            print("SendGrid exception:", e)

    # Fallback: Gmail SMTP
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
    if not (gmail_user and gmail_pass and to):
        print("No SMTP creds or recipients set; skipping email.")
        return

    try:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(content)

        # Use TLS
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(gmail_user, gmail_pass)
            smtp.send_message(msg)
        print("Email sent via Gmail SMTP to", to)
    except Exception as e:
        print("Gmail SMTP send failed:", e)


def restart_render_service(service_id):
    if DRY_RUN:
        print("[DRY_RUN] would restart", service_id)
        return
    # Create a new deploy for the service (Render API)
    deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys"
    payload = {"clearCache": False}
    r = requests.post(deploy_url,
                      json=payload,
                      headers=HEADERS_RENDER,
                      timeout=30)
    print("restart_render_service:", r.status_code, r.text)
    return r.status_code, r.text


def check_url(url):
    try:
        r = requests.get(url, timeout=10)
        return r.status_code, r.text[:400]
    except Exception as e:
        return None, str(e)


def main():
    if not SERVICE_CHECKS:
        print("SERVICE_CHECKS env var not set; nothing to do.")
        sys.exit(1)
    checks = json.loads(SERVICE_CHECKS)
    issues = []
    for svc in checks:
        sid = svc.get("id")
        name = svc.get("name")
        url = svc.get("url")
        ok = False
        last_err = None
        for attempt in range(1, MAX_RETRIES + 2):
            status, body = check_url(url)
            print(f"[{name}] attempt {attempt} status={status}")
            if status and (200 <= status < 400):
                ok = True
                break
            last_err = body
            time.sleep(RETRY_DELAY)
        if not ok:
            issues.append((svc, status, last_err))
    if not issues:
        print("All services OK.")
        sys.exit(0)

    # handle issues
    msg_lines = []
    for svc, status, err in issues:
        name = svc.get("name")
        sid = svc.get("id")
        url = svc.get("url")
        line = f"{name} ({sid}) failed. URL: {url}. Status: {status}. Err: {err}"
        msg_lines.append(line)
        print(line)
        if sid and RENDER_API_KEY:
            restart_render_service(sid)
    # send alert
    subject = f"JRAVIS ALERT: {len(issues)} services unhealthy"
    content = "\n".join(msg_lines)
    send_email(subject, content)
    sys.exit(2)


if __name__ == "__main__":
    main()
