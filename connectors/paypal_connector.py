# connectors/paypal_connector.py
import os, requests, base64

client = os.getenv("PAYPAL_CLIENT_ID")
secret = os.getenv("PAYPAL_SECRET")
mode = os.getenv("PAYPAL_MODE", "live")

base = "https://api-m.paypal.com" if mode == "live" else "https://api-m.sandbox.paypal.com"
auth = base64.b64encode(f"{client}:{secret}".encode()).decode()

headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
data = {"grant_type": "client_credentials"}

try:
    resp = requests.post(f"{base}/v1/oauth2/token", headers=headers, data=data, timeout=30)
    if resp.status_code == 200:
        print("✅ PayPal Connected — Live Mode")
    else:
        print(f"❌ PayPal Error: {resp.status_code} → {resp.text}")
except Exception as e:
    print(f"❌ Connection failed: {e}")

