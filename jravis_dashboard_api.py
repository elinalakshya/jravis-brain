# jravis_dashboard_api.py
# JRAVIS Dashboard Data API — Phase 1 Bridge
# Author: Dhruvayu

from tinydb import TinyDB
from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)
db = TinyDB('jr_memory.json')


@app.route("/api/dashboard", methods=["GET"])
def dashboard_data():
    earnings_table = db.table("earnings")
    reports_table = db.table("reports")

    # Get total earnings (for month)
    today = datetime.now()
    this_month = today.strftime("%Y-%m")
    total_earnings = sum(e["amount"] for e in earnings_table.all()
                         if e["date"].startswith(this_month))

    # Get last report
    last_report = None
    if len(reports_table) > 0:
        last_report = reports_table.all()[-1]
    last_report_date = (last_report["date"]
                        if last_report else "No reports yet")

    # Get stream health (simplified for Phase 1)
    health = "OK ✅" if total_earnings > 0 else "⚠️ Pending Validation"

    data = {
        "timestamp": datetime.now().isoformat(),
        "total_earnings_inr": total_earnings,
        "streams_active": len(earnings_table),
        "system_health": health,
        "last_report": last_report_date,
    }
    return jsonify(data)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3300))
    print(
        f"🚀 JRAVIS Dashboard API running at http://localhost:{port}/api/dashboard"
    )
    app.run(host="0.0.0.0", port=port)
