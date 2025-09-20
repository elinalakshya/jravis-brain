# vabot/send_daily_email.py
import os, json, smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from vabot.phase1_runner import run_phase1

TO_EMAIL = os.getenv("TO_EMAIL", "nrveeresh327@gamil.com")
FROM_EMAIL = os.getenv("EMAIL")
APP_PASS = os.getenv("APP_PASS")


def build_body(report):
    lines = [f"Phase 1 Report — {report['date']}"]
    for s in report["streams"]:
        plat = s.get("platform", "Unknown")
        if "error" in s:
            lines.append(f"❌ {plat}: {s['error']}")
        elif "status" in s:
            lines.append(f"🔑 {plat}: {s['status']}")
        else:
            details = " | ".join(
                [f"{k}: {v}" for k, v in s.items() if k != 'platform'])
            lines.append(f"✅ {plat}: {details}")
    return "\n".join(lines)


def main():
    report = run_phase1()
    os.makedirs("DailyReport/out", exist_ok=True)
    with open("DailyReport/out/phase1_summary.json", "w",
              encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if not FROM_EMAIL or not APP_PASS:
        raise RuntimeError("Missing EMAIL/APP_PASS env vars")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"VA Bot Phase 1 Report — {report['date']}"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(build_body(report), "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com",
                          465,
                          context=ssl.create_default_context()) as s:
        s.login(FROM_EMAIL, APP_PASS)
        s.sendmail(FROM_EMAIL, [TO_EMAIL], msg.as_string())


if __name__ == "__main__":
    main()
