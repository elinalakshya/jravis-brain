import requests, datetime, time

JRAVIS_API = "http://localhost:8000/api"


def weekly_refresh(source="va_bot_weekly"):
    try:
        r = requests.post(f"{JRAVIS_API}/trigger", json={"source": source})
        if r.status_code == 200:
            print("✅ Weekly dashboard refresh triggered at",
                  datetime.datetime.now())
        else:
            print(f"⚠️ Trigger failed: {r.status_code} {r.text}")
    except Exception as e:
        print("❌ Could not reach JRAVIS backend:", e)


if __name__ == "__main__":
    time.sleep(10)
    weekly_refresh()
