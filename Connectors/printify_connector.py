"""
JRAVIS Printify Connector — Phase 1c Final 🔗
Author: Team Lakshya 2040
Purpose:
  • Connect JRAVIS Core to Printify API.
  • Authenticate securely using encrypted token from token_manager.py.
  • Sync shop details, verify connection, and prepare for auto-order handling.

Works perfectly in Render, Replit, or Docker.
"""

import os
import time
import requests
from datetime import datetime
from token_manager import get_token

PRINTIFY_API_BASE = "https://api.printify.com/v1"

def log(msg):
    """Timestamped logging for clarity"""
    print(f"[{datetime.utcnow().isoformat()}Z] {msg}", flush=True)


def get_headers():
    """Builds auth header using decrypted token"""
    token = get_token("printify")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def verify_connection():
    """Checks if Printify token works and fetches shop info"""
    try:
        log("Connecting to Printify...")
        r = requests.get(f"{PRINTIFY_API_BASE}/shops.json", headers=get_headers())
        if r.status_code == 200:
            shops = r.json()
            if isinstance(shops, list) and len(shops) > 0:
                shop = shops[0]
                log(f"✅ Authenticated with Printify")
                log(f"✅ Shop ID: {shop.get('id')} — {shop.get('title')}")
                return shop.get("id")
            else:
                log("⚠️ No shops found. Please create one in Printify Dashboard.")
                return None
        else:
            log(f"❌ Error: {r.status_code} — {r.text}")
            return None
    except Exception as e:
        log(f"❌ Connection failed: {e}")
        return None


def fetch_orders(shop_id):
    """Fetches latest orders from Printify"""
    try:
        url = f"{PRINTIFY_API_BASE}/shops/{shop_id}/orders.json?page=1&limit=20"
        r = requests.get(url, headers=get_headers())
        if r.status_code == 200:
            data = r.json()
            log(f"📦 Found {len(data.get('data', []))} orders.")
        else:
            log(f"⚠️ Order fetch error {r.status_code}: {r.text}")
    except Exception as e:
        log(f"❌ Order sync failed: {e}")


def main():
    log("JRAVIS Printify Connector started 🚀")
    shop_id = verify_connection()
    if not shop_id:
        log("❌ Stopping connector: Shop verification failed.")
        return

    log("✅ Sync online. Polling for new orders every 5 minutes...")
    while True:
        fetch_orders(shop_id)
        time.sleep(300)  # 5-minute interval


if __name__ == "__main__":
    main()
