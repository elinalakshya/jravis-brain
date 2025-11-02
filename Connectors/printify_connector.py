# connectors/printify_connector.py
import os, requests

PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
BASE_URL = "https://api.printify.com/v1"
HEADERS = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}


def get_shops():
    r = requests.get(f"{BASE_URL}/shops.json", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def get_products(shop_id):
    r = requests.get(f"{BASE_URL}/shops/{shop_id}/products.json",
                     headers=HEADERS,
                     timeout=30)
    r.raise_for_status()
    return r.json()


def test_connection():
    try:
        data = get_shops()
        print("[Printify] Connected ✅")
        for shop in data:
            print(f"→ Shop: {shop.get('title')} (ID: {shop.get('id')})")
        return True
    except Exception as e:
        print(f"[Printify] Error: {e}")
        return False


if __name__ == "__main__":
    test_connection()
