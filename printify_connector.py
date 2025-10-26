import os
import time
import requests
from datetime import datetime
from token_manager import get_token

# ----------------------------------------------------------------------
# ✅ JRAVIS → Printify Connector
# Automatically syncs and polls Printify shop via API.
# ----------------------------------------------------------------------


def log(msg: str):
    """Timestamped logger."""
    print(f"[{datetime.utcnow().isoformat()}Z] {msg}", flush=True)


def get_shop_orders(shop_id: str, token: str):
    """Fetch latest orders for a given Printify shop."""
    url = f"https://api.printify.com/v1/shops/{shop_id}/orders.json?page=1&limit=10"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 200:
        return r.json()
    else:
        log(f"⚠️ Error fetching orders: {r.status_code} - {r.text}")
        return None


def main():
    try:
        # 1️⃣ Get environment variables
        shop_id = os.getenv("PRINTIFY_SHOP_ID")
        if not shop_id:
            raise ValueError(
                "PRINTIFY_SHOP_ID not found in environment variables.")

        # 2️⃣ Decrypt API key securely
        token = get_token("printify")

        # 3️⃣ Start connector
        log(f"✅ JRAVIS Printify Connector started for shop {shop_id}")
        log("Polling for new orders every 5 minutes...")

        while True:
            orders = get_shop_orders(shop_id, token)
            if orders and isinstance(orders, dict) and orders.get("data"):
                log(f"🟢 Found {len(orders['data'])} new orders")
            else:
                log("No new orders found.")

            time.sleep(300)  # 5-minute interval

    except Exception as e:
        log(f"❌ Fatal error in connector: {e}")


if __name__ == "__main__":
    main()
