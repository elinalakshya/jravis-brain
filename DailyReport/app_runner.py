import threading, os, time, pandas as pd
from datetime import datetime
from flask import Flask
import pytz

from vabot.phase1_connectors import get_printify_shops, list_models, get_channel_stats
from send_daily_report import send_daily_report

app = Flask(__name__)


@app.route("/")
def index():
    return "✅ VA Bot is running 24/7 on Render!", 200


@app.route("/health")
def health():
    return "OK", 200


@app.route("/send-report")
def trigger_report():
    send_daily_report()
    return "Manual report sent ✅", 200


def run_phase1_cycle():
    log_file = "logs/phase1_log.csv"
    os.makedirs("logs", exist_ok=True)

    while True:
        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        now_str = now.strftime("%d-%m-%Y %I:%M %p IST")

        print(f"🚀 Running Phase 1 API checks at {now_str}...")

        results = []
        try:
            results.append({
                "Platform": "Printify",
                "Result": str(get_printify_shops())
            })
        except Exception as e:
            results.append({"Platform": "Printify", "Result": f"Error: {e}"})

        try:
            results.append({
                "Platform": "MeshyAI",
                "Result": str(list_models())
            })
        except Exception as e:
            results.append({"Platform": "MeshyAI", "Result": f"Error: {e}"})

        try:
            results.append({
                "Platform":
                "YouTube",
                "Result":
                str(get_channel_stats("UCe2cqtUKLMCm9v9vmsAkKaA"))
            })
        except Exception as e:
            results.append({"Platform": "YouTube", "Result": f"Error: {e}"})

        df = pd.DataFrame(results)
        df["Timestamp"] = now_str

        if os.path.exists(log_file):
            df.to_csv(log_file, mode="a", header=False, index=False)
        else:
            df.to_csv(log_file, index=False)

        print(f"✅ Logged results to {log_file}")
        print("⏳ Sleeping for 1 hour...")
        time.sleep(3600)


if __name__ == "__main__":
    threading.Thread(target=run_phase1_cycle, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)
