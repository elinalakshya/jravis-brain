# auto_dashboard_trigger.py
import requests, datetime, time

JRAVIS_API = "http://localhost:8000/api"


def trigger_dashboard(source="va_bot"):
    try:
        r = requests.post(f"{JRAVIS_API}/trigger", json={"source": source})
        if r.status_code == 200:
            print("✅ JRAVIS dashboard sync triggered at",
                  datetime.datetime.now())
        else:
            print("⚠️ Trigger failed:", r.status_code, r.text)
    except Exception as e:
        print("❌ Could not reach JRAVIS backend:", e)


if __name__ == "__main__":
    # wait 15 s so email scripts finish first
    time.sleep(15)
    trigger_dashboard()
