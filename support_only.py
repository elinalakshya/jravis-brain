# support_only.py — verbose mode (prints progress & writes logs/support_log.csv)

import os, ssl, smtplib, yaml, time, csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

from email_templates import render_api_email, SupportPayload, render_boss_summary, BOSS_EMAIL


def log_print(*a):
    print(*a, flush=True)


load_dotenv()
EMAIL = os.getenv("EMAIL")
APP_PASS = os.getenv("APP_PASS")
PAYPAL_EMAIL = os.getenv("PAYPAL_EMAIL", "")
SUPPORT_CC = os.getenv("SUPPORT_CC", "")

if not EMAIL or not APP_PASS:
    raise ValueError("❌ Missing EMAIL or APP_PASS in Replit Secrets!")
if not PAYPAL_EMAIL:
    raise ValueError("❌ Missing PAYPAL_EMAIL in Replit Secrets!")

log_print("🔐 Secrets loaded. Sender:", EMAIL)

with open("platforms.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f) or {}
PLATFORMS = cfg.get("platforms", [])
if not PLATFORMS:
    raise ValueError("❌ platforms.yaml has no 'platforms' entries.")

log_print(f"📦 Platforms loaded: {[p['name'] for p in PLATFORMS]}")


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


def main():
    sent_rows = []
    os.makedirs("logs", exist_ok=True)
    csv_path = "logs/support_log.csv"
    with open(csv_path, "a", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(["ts", "platform", "target", "status"])

        for p in PLATFORMS:
            plat = p["name"]
            log_print(f"\n➡️  {plat}: preparing support request…")
            status = "skipped"
            target = p.get("support_email") or p.get("support_portal_url",
                                                     "(none)")

            if p.get("api_request"):
                payload = SupportPayload(
                    platform=plat,
                    boss_email=BOSS_EMAIL,
                    paypal_email=PAYPAL_EMAIL,
                    sandbox_ok=True,
                    webhook_url=None,
                )
                body = render_api_email(payload)

                if p.get("support_email"):
                    log_print(
                        f"   📧 emailing {p['support_email']} (CC: {BOSS_EMAIL}{', '+SUPPORT_CC if SUPPORT_CC else ''})…"
                    )
                    status = send_email_raw(
                        to_addr=p["support_email"],
                        subject=f"API access + PayPal linking request — {plat}",
                        body=body,
                        cc=",".join([x for x in [BOSS_EMAIL, SUPPORT_CC]
                                     if x]),
                    )
                elif p.get("support_portal_url"):
                    log_print(
                        f"   🧾 portal-only → sending you a ticket draft for {plat}…"
                    )
                    portal_note = (
                        f"Portal ticket needed for {plat}:\n"
                        f"Open: {p['support_portal_url']}\n\n"
                        f"Use this request text (copy/paste):\n\n{body}\n")
                    status = send_email_raw(
                        to_addr=BOSS_EMAIL,
                        subject=f"Portal ticket needed — {plat}",
                        body=portal_note,
                        cc=SUPPORT_CC,
                    )
                else:
                    status = "no support target configured"
                    log_print(
                        "   ⚠️ no support_email or portal URL configured")

            sent_rows.append({
                "platform": plat,
                "to": target,
                "status": status,
                "login": "skipped (no-browser)"
            })
            writer.writerow([
                datetime.now().isoformat(timespec="seconds"), plat, target,
                status
            ])
            log_print(f"   ✅ status: {status}")

    # final summary to Boss
    summary = render_boss_summary(sent_rows)
    log_print("\n📨 sending summary email to Boss…")
    final = send_email_raw(BOSS_EMAIL,
                           "Phase 1 — Support emails sent (no-browser mode)",
                           summary)
    log_print(f"   📬 summary status: {final}")
    log_print(f"\n🗂️  Log saved: {csv_path}")
    log_print("🎯 Done.")


if __name__ == "__main__":
    main()


def already_sent_in_24h(csv_path, platform):
    import csv, datetime as dt
    if not os.path.exists(csv_path): return False
    cutoff = dt.datetime.utcnow() - dt.timedelta(hours=24)
    with open(csv_path, newline="", encoding="utf-8") as fp:
        r = csv.DictReader(fp)
        for row in r:
            if row["platform"] == platform and row["status"].startswith(
                    "sent"):
                try:
                    ts = dt.datetime.fromisoformat(row["ts"])
                    if ts >= cutoff:
                        return True
                except:
                    pass
    return False


def main():
    sent_rows = []
    os.makedirs("logs", exist_ok=True)
    csv_path = "logs/support_log.csv"
    new_file = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        if new_file:
            writer.writerow(["ts", "platform", "target", "status"])

        for p in PLATFORMS:
            plat = p["name"]
            if already_sent_in_24h(csv_path, plat):
                print(f"⏭️  {plat}: skipped (already sent in last 24h)",
                      flush=True)
                sent_rows.append({
                    "platform": plat,
                    "to": "-",
                    "status": "skipped-24h",
                    "login": "n/a"
                })
                continue
            # ... keep the rest unchanged ...
