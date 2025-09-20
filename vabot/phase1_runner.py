# vabot/phase1_runner.py
import json
from datetime import datetime
from vabot import phase1_connectors


def run_phase1():
    summary = {"date": datetime.now().strftime("%Y-%m-%d"), "streams": []}

    for connector in phase1_connectors.CONNECTORS:
        try:
            data = connector()
            summary["streams"].append(data)
            print(f"✅ {data.get('platform', connector.__name__)} fetched")
        except Exception as e:
            summary["streams"].append({
                "platform": connector.__name__,
                "error": str(e)
            })
            print(f"❌ {connector.__name__} failed: {e}")

    return summary


def print_dashboard(report):
    print("\n📊 Phase 1 Report —", report["date"])
    print("─" * 65)

    for stream in report["streams"]:
        platform = stream.get("platform", "Unknown")

        if "error" in stream:
            print(f"{platform:<22} ❌ ERROR: {stream['error']}")
        elif "status" in stream and "Awaiting" in stream["status"]:
            print(f"{platform:<22} 🔑 {stream['status']}")
        else:
            details = " | ".join(
                [f"{k}: {v}" for k, v in stream.items() if k != "platform"])
            print(f"{platform:<22} {details}")
    print("─" * 65)


if __name__ == "__main__":
    report = run_phase1()

    # Save JSON
    out_file = "DailyReport/out/phase1_summary.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print_dashboard(report)
    print(f"✅ JSON saved at {out_file}")
