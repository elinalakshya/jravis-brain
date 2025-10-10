#!/usr/bin/env python3
"""
income_system_bundle.py

Integrates:
1️⃣ Income Tracker (auto-updates after each VA Bot task)
2️⃣ Report Generator (daily + weekly summary/invoice)
3️⃣ Progress API for JRAVIS Dashboard
4️⃣ Scheduler for auto daily/weekly reports

✅ 100% Legal & Transparent
✅ Auto-updates progress for Mission 2040
"""

import os
import json
import datetime
import threading
import time
import pdfkit
from flask import Flask, jsonify, render_template_string

# ==============================
# ⚙️ CONFIG
# ==============================
INCOME_FILE = "./income_log.json"
SUMMARY_DIR = "./reports"
TARGET = 40000000  # ₹4 Crore
DAILY_TIME = (4, 30)  # 10:00 AM IST = 04:30 UTC
WEEKLY_DAY = 6  # Sunday (0=Monday ... 6=Sunday)

os.makedirs(SUMMARY_DIR, exist_ok=True)


# ==============================
# 💰 INCOME TRACKER
# ==============================
def record_income(stream: str, amount: float):
    entry = {
        "stream": stream,
        "amount": float(amount),
        "timestamp": datetime.datetime.now().isoformat()
    }
    data = []
    if os.path.exists(INCOME_FILE):
        try:
            with open(INCOME_FILE) as f:
                data = json.load(f)
        except Exception:
            data = []
    data.append(entry)
    with open(INCOME_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[INCOME] Added {stream}: ₹{amount}")


# ==============================
# 📊 REPORT GENERATOR
# ==============================
def generate_reports():
    today = datetime.date.today().strftime("%d-%m-%Y")
    if not os.path.exists(INCOME_FILE):
        print("[REPORTS] No income file found.")
        return
    with open(INCOME_FILE) as f:
        data = json.load(f)
    total = sum(x["amount"] for x in data)
    html = f"""
    <h1>{today} Summary Report</h1>
    <p>Total Streams: {len(data)}</p>
    <p>Total Income: ₹{total:,.2f}</p>
    <p>Generated automatically by JRAVIS & VA BOT</p>
    """
    pdfkit.from_string(
        html, os.path.join(SUMMARY_DIR, f"{today} summary report.pdf"))

    invoice_html = f"<h1>Invoice - {today}</h1><p>Generated for legal filing.</p>"
    pdfkit.from_string(invoice_html,
                       os.path.join(SUMMARY_DIR, f"{today} invoices.pdf"))
    print(f"[REPORTS] Generated PDFs for {today}")


# ==============================
# 📈 PROGRESS API (Dashboard)
# ==============================
app = Flask(__name__)


def get_progress():
    if not os.path.exists(INCOME_FILE):
        return 0
    with open(INCOME_FILE) as f:
        data = json.load(f)
    total = sum(x["amount"] for x in data)
    return min(round(total / TARGET * 100, 2), 100)


@app.route("/progress")
def progress():
    percent = get_progress()
    html = f"""
    <html>
    <head>
        <style>
            body {{ background:#0b0c10; color:#fff; font-family:sans-serif; text-align:center; padding:50px; }}
            .bar-container {{ width:80%; background:#333; border-radius:10px; margin:auto; height:25px; }}
            .bar {{ height:25px; border-radius:10px; background:linear-gradient(90deg,#00ffff,#00ff00); width:{percent}%; }}
        </style>
    </head>
    <body>
        <h1>Mission 2040 Progress</h1>
        <div class="bar-container"><div class="bar"></div></div>
        <p>{percent}% of ₹4 Cr debt cleared — Target June 2027</p>
    </body>
    </html>
    """
    return render_template_string(html)


# ==============================
# 🕒 AUTO SCHEDULER
# ==============================
def schedule_reports():
    while True:
        now = datetime.datetime.utcnow()
        # Daily trigger at 04:30 UTC (10 AM IST)
        if (now.hour, now.minute) == DAILY_TIME:
            generate_reports()

        # Weekly trigger (Sunday 00:00 UTC)
        if now.weekday() == WEEKLY_DAY and now.hour == 0 and now.minute == 0:
            generate_reports()

        time.sleep(60)  # Check every minute


def start_scheduler():
    t = threading.Thread(target=schedule_reports, daemon=True)
    t.start()
    print("[SCHEDULER] Daily/weekly auto-report thread started.")


# ==============================
# 🚀 ENTRY POINT
# ==============================
if __name__ == "__main__":
    start_scheduler()
    port = int(os.environ.get("PORT", 10050))
    print(f"[INCOME SYSTEM] Running on port {port}")
    app.run(host="0.0.0.0", port=port)
