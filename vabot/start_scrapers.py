# vabot/start_scrapers.py
"""
Quick starter that runs the scraping connectors immediately (Fiverr, Upwork, Etsy, Redbubble,
Freelancer, CadCrowd, KDP). These connector functions should exist in phase1_connectors.py.
This script forces them to run now and writes a combined JSON.
"""
import json, os
from datetime import datetime
from vabot import phase1_connectors


def run_scrapers_once():
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "streams": []
    }
    # pick connectors we consider 'auto' (names from your phase1_connectors)
    auto_connectors = [
        phase1_connectors.fiverr_ai, phase1_connectors.upwork,
        phase1_connectors.redbubble, phase1_connectors.etsy_store,
        phase1_connectors.freelancer_work, phase1_connectors.cadcrowd_auto,
        phase1_connectors.amazon_kdp
    ]

    for conn in auto_connectors:
        name = getattr(conn(), "get",
                       lambda: {})()  # not used; just call safely
        try:
            data = conn()
            summary["streams"].append(data)
            print(f"✅ {data.get('platform', conn.__name__)} fetched")
        except Exception as e:
            summary["streams"].append({
                "platform": conn.__name__,
                "error": str(e)
            })
            print(f"❌ {conn.__name__} failed: {e}")

    out_file = "DailyReport/out/phase1_auto_scrape.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"📄 Auto-scrape JSON saved at {out_file}")
    return summary


if __name__ == "__main__":
    run_scrapers_once()
