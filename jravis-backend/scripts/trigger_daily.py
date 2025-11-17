import requests

if __name__ == "__main__":
    try:
        print("[trigger_daily] Calling JRAVIS backend...")
        url = "https://jravis-backend.onrender.com/api/send_daily_report?code=JRV2040_LOCKED_KEY_001"
        res = requests.get(url, timeout=30)
        print(f"[trigger_daily] HTTP {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[trigger_daily] Error: {e}")
