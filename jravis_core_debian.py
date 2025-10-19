# ============================================================
# JRAVIS Core (Debian Build)
# All-in-one lightweight version
# ============================================================

print("🚀 JRAVIS Core Debian Build Starting...")

# ---- 1. Imports ----
try:
    from flask import Flask, jsonify
    from tinydb import TinyDB
    from datetime import datetime
except ModuleNotFoundError:
    print("📦 Installing missing modules... please wait...")
    import os
    os.system("pip install flask tinydb")
    from flask import Flask, jsonify
    from tinydb import TinyDB
    from datetime import datetime

# ---- 2. Memory Store ----
db = TinyDB("jr_memory.json")
app = Flask(__name__)


# ---- 3. API Route ----
@app.route("/")
def home():
    return "JRAVIS OK ✅ — Debian Core Active"


@app.route("/api/dashboard", methods=["GET"])
def dashboard_data():
    earnings_table = db.table("earnings")
    reports_table = db.table("reports")

    # Simulate some data if empty
    if not earnings_table:
        earnings_table.insert({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "amount": 50000
        })
    total_earnings = sum(e["amount"] for e in earnings_table)

    last_report = (reports_table.all()[-1]["date"]
                   if len(reports_table) > 0 else "No reports yet")

    data = {
        "timestamp": datetime.now().isoformat(),
        "total_earnings_inr": total_earnings,
        "streams_active": len(earnings_table),
        "system_health":
        "OK ✅" if total_earnings > 0 else "⚠️ Pending Validation",
        "last_report": last_report
    }
    return jsonify(data)


# ---- 4. Run ----
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 3300))  # Render uses dynamic port
    print(f"🧠 JRAVIS Core is Live at: http://0.0.0.0:{port}/")
    app.run(host="0.0.0.0", port=port)
