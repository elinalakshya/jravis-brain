# scripts/trigger_daily.py
# Simple, robust trigger for JRAVIS daily report (safe for Render Cron)
import sys
import requests
import time

URL = "https://jravis-backend.onrender.com/api/send_daily_report?code=2040"
TIMEOUT = 30


def main():
    print(f"[trigger_daily] Calling {URL}")
    try:
        r = requests.get(URL, timeout=TIMEOUT)
        print(f"[trigger_daily] HTTP {r.status_code} - {r.text[:1000]}")
        if r.status_code == 200:
            print("[trigger_daily] SUCCESS")
            return 0
        else:
            print("[trigger_daily] FAILED: non-200 status")
            return 2
    except Exception as e:
        print(f"[trigger_daily] ERROR: {e}")
        return 3


import requests

if __name__ == "__main__":
    print("[trigger_daily] Calling JRAVIS backend...")
    res = requests.get(
        "https://jravis-backend.onrender.com/api/send_daily_report?code=2040")
    print(f"[trigger_daily] HTTP {res.status_code} - {res.text}")
