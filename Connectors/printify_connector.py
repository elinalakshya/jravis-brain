# printify_connector.py
"""
Printify connector for JRAVIS Income Core
- Uses PRINTIFY_TOKEN_ENC and PRINTIFY_SHOP_ID from env (token_manager decrypts)
- Polls orders and forwards new ones to INCOME_CORE_URL (default http://127.0.0.1:3300/vendor_hook)
- Keeps a small seen-id file to avoid duplicates
"""

import os, time, requests, json
from datetime import datetime, timezone
from token_manager import get_token

SHOP_ID = os.getenv("PRINTIFY_SHOP_ID")
INCOME_CORE_URL = os.getenv("INCOME_CORE_URL",
                            "http://127.0.0.1:3300/vendor_hook")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
SEEN_FILE = ".printify_seen_ids"


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        for s in sorted(seen):
            f.write(s + "\n")


def get_printify_token():
    return get_token("printify")


def fetch_orders(token, page=1, limit=20):
    url = f"https://api.printify.com/v1/shops/{SHOP_ID}/orders.json?page={page}&limit={limit}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


def normalize_orders(raw):
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        if isinstance(raw.get("data"), list):
            return raw["data"]
        if isinstance(raw.get("orders"), list):
            return raw["orders"]
    return []


def forward_to_income_core(order):
    payload = {
        "vendor": "printify",
        "shop_id": SHOP_ID,
        "order_id": str(order.get("id") or order.get("order_id")),
        "created_at": order.get("created_at"),
        "total_price": order.get("total_price"),
        "currency": order.get("currency"),
        "raw": order
    }
    try:
        r = requests.post(INCOME_CORE_URL, json=payload, timeout=15)
        return r.status_code
    except Exception as e:
        print("Forward error:", e)
        return None


def poll_loop():
    if not SHOP_ID:
        raise SystemExit("PRINTIFY_SHOP_ID not set in env.")
    token = get_printify_token()
    seen = load_seen()
    print(
        f"[{datetime.now(timezone.utc).isoformat()}] Printify connector started for shop {SHOP_ID}"
    )
    while True:
        try:
            orders = normalize_orders(fetch_orders(token))
            for o in orders:
                oid = str(o.get("id") or o.get("order_id"))
                if not oid or oid in seen:
                    continue
                code = forward_to_income_core(o)
                print(
                    f"[{datetime.now().isoformat()}] Forwarded order {oid} -> status={code}"
                )
                seen.add(oid)
            save_seen(seen)
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Error:", e)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    poll_loop()
