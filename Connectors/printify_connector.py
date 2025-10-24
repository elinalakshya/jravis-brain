# printify_connector.py
# ✅ Self-locating version that works in Render, Replit, or locally.

import os, time, json, requests
from datetime import datetime
from token_manager import get_token

def log(msg):
    print(f"[{datetime.utcnow().isoformat()}Z] {msg}", flush=True)

def main():
    try:
        token = get_token("printify")
        shop_id = os.getenv("PRINTIFY_SHOP_ID")

        if not token:
            raise ValueError("❌ Missing or invalid PRINTIFY_TOKEN.")
        if not shop_id:
            raise ValueError("❌ Missing PRINTIFY_SHOP_ID in environment.")

        base_url = f"https://api.printify.com/v1/shops/{shop_id}/orders.json"
        log(f"🚀 Printify connector started for shop {shop_id}")

        # fetch recent orders
        resp = requests.get(
            base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

        if resp.status_code == 200:
            data = resp.json()
            log(f"✅ Connected! Found {len(data.get('data', []))} orders.")
            print(json.dumps(data, indent=2))
        else:
            log(f"❌ Error: {resp.status_code} — {resp.text}")

    except Exception as e:
        log(f"🔥 Fatal error: {e}")

if __name__ == "__main__":
    # change working directory to where this file is
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    log("🧠 JRAVIS Printify connector initializing...")
    main()
    log("✅ Finished execution.")
