import os, requests
PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
PRINTIFY_SHOP_ID = os.getenv("PRINTIFY_SHOP_ID")  # numeric id

BASE = "https://api.printify.com/v1"

def sync_check():
    if not PRINTIFY_API_KEY or not PRINTIFY_SHOP_ID:
        return {"ok": False, "why": "missing PRINTIFY_API_KEY/PRINTIFY_SHOP_ID"}
    headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}
    r = requests.get(f"{BASE}/shops/{PRINTIFY_SHOP_ID}/products.json", headers=headers, timeout=60)
    if r.status_code != 200:
        return {"ok": False, "status": r.status_code, "resp": r.text}
    data = r.json()
    count = len(data) if isinstance(data, list) else 0
    return {"ok": True, "products": count}
