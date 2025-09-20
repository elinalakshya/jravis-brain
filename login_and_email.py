# login_and_email.py — Phase 1 FINAL

import os
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any

import yaml
from rich import print
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from email_templates import render_api_email, SupportPayload, render_boss_summary, BOSS_EMAIL

# Folders
DATA = Path("data")
SCREENS = DATA / "screens"
COOKIES = DATA / "cookies"
LOGS = DATA / "logs"
for pth in (SCREENS, COOKIES, LOGS):
    pth.mkdir(parents=True, exist_ok=True)

# Secrets
load_dotenv()
EMAIL = os.getenv("EMAIL")
APP_PASS = os.getenv("APP_PASS")
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL", "")
SUPPORT_CC = os.getenv("SUPPORT_CC", "")

if not EMAIL or not APP_PASS:
    raise ValueError("❌ Missing EMAIL or APP_PASS in Replit Secrets!")
if not PAYPAL_EMAIL:
    raise ValueError("❌ Missing PAYPAL_EMAIL in Replit Secrets!")

# Config
with open("platforms.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
PLATFORMS = cfg.get("platforms", [])


# ── Email helper ─────────────────────────────────────────────────────────────
def send_email_raw(to_addr: str, subject: str, body: str, cc: str = "") -> str:
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to_addr
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",
                              465,
                              context=ssl.create_default_context()) as server:
            server.login(EMAIL, APP_PASS)
            recipients = [to_addr] + ([cc] if cc else [])
            server.sendmail(EMAIL, recipients, msg.as_string())
        return "sent"
    except Exception as e:
        return f"error: {e}"


# ── Login via Playwright ─────────────────────────────────────────────────────
def login_and_capture(page, platform: Dict[str, Any]) -> str:
    sel = platform["selectors"]
    try:
        page.goto(platform["login_url"], timeout=60000)
        page.wait_for_selector(sel.get("user"), timeout=30000)
        page.fill(sel.get("user"), os.getenv(platform["username_secret"], ""))
        page.fill(sel.get("pass"), os.getenv(platform["password_secret"], ""))
        page.click(sel.get("submit"))
        page.wait_for_selector(sel.get("post_login_wait_selector"),
                               timeout=60000)
        page.screenshot(path=str(SCREENS / f"{platform['name']}.png"),
                        full_page=True)
        cookies = page.context.cookies()
        (COOKIES / f"{platform['name']}.json").write_text(
            json.dumps(cookies, indent=2))
        return "ok"
    except PWTimeout:
        page.screenshot(path=str(SCREENS / f"{platform['name']}_timeout.png"),
                        full_page=True)
        return "timeout/MFA?"
    except Exception as e:
        return f"error: {e}"


# ── Main ─────────────────────────────────────────────────────────────────────
def run():
    sent_rows = []
    with sync_playwright() as pw:
        # Replit-friendly flags; ignore the install-deps warning
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context()
        page = context.new_page()

        for p in PLATFORMS:
            plat_name = p["name"]
            print(f"[bold cyan]→ Logging into {plat_name}[/bold cyan]")
            login_status = login_and_capture(page, p)
            print(f"   status: {login_status}")

            status = "skipped"
            if p.get("api_request"):
                payload = SupportPayload(
                    platform=plat_name,
                    boss_email=BOSS_EMAIL,
                    paypal_email=PAYPAL_EMAIL,
                    sandbox_ok=True,
                    webhook_url=None,
                )
                body = render_api_email(payload)

                if p.get("support_email"):
                    status = send_email_raw(
                        to_addr=p.get("support_email"),
                        subject=
                        f"API access + PayPal linking request — {plat_name}",
                        body=body,
                        cc=",".join([x for x in [BOSS_EMAIL, SUPPORT_CC]
                                     if x]),
                    )
                elif p.get("support_portal_url"):
                    portal_note = (
                        f"Portal ticket needed for {plat_name}:\n"
                        f"Open: {p.get('support_portal_url')}\n\n"
                        f"Use this request text (copy/paste):\n\n{body}\n")
                    status = send_email_raw(
                        to_addr=BOSS_EMAIL,
                        subject=f"Portal ticket needed — {plat_name}",
                        body=portal_note,
                        cc=SUPPORT_CC,
                    )
                else:
                    status = "no support target configured"

            sent_rows.append({
                "platform":
                plat_name,
                "to":
                p.get("support_email")
                or p.get("support_portal_url", "(none)"),
                "status":
                status,
                "login":
                login_status,
            })

        summary = render_boss_summary(sent_rows)
        send_email_raw(BOSS_EMAIL,
                       "Phase 1 — Logins done + Support outreach queued",
                       summary)

        browser.close()


if __name__ == "__main__":
    run()

sudo apt-get update
sudo apt-get install -y libnspr4 libnss3 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcb1 libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 libgbm1 libcairo2 libpango-1.0-0 libasound2
python -m playwright install chromium
python login_and_email.py
