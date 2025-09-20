#!/usr/bin/env python3
"""
connectors/printify_pod_connector.py
Single combined Printify connector:
- Reads PRINTIFY_API_KEY from env
- Polls shops and orders every PRINTIFY_INTERVAL_S seconds
- Creates a simple invoice PDF in DailyReport/out/<orderid>_invoice.pdf for each new order
- Maintains seen_orders.json to avoid duplicates

Usage:
export PRINTIFY_API_KEY="your_token"
export PRINTIFY_INTERVAL_S=300   # default 300 seconds
python3 connectors/printify_pod_connector.py
"""
import os, time, json, logging, requests
from datetime import datetime
from pathlib import Path

# Optional PDF lib
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:
    reportlab = None
else:
    reportlab = True

LOG = logging.getLogger("printify")
LOG.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
LOG.addHandler(handler)

API_KEY = os.getenv("PRINTIFY_API_KEY")
BASE_URL = "https://api.printify.com/v1"
INTERVAL = int(os.getenv("PRINTIFY_INTERVAL_S", "300"))

OUT_DIR = Path("DailyReport/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = Path("connectors/printify_seen_orders.json")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# load seen orders
if STATE_FILE.exists():
    try:
        seen_orders = set(json.load(STATE_FILE))
    except Exception:
        seen_orders = set()
else:
    seen_orders = set()


def save_state():
    try:
        with open(STATE_FILE, "w") as fh:
            json.dump(list(seen_orders), fh)
    except Exception:
        LOG.exception("Failed to save state file")


def api_get(endpoint):
    if not API_KEY:
        LOG.error("PRINTIFY_API_KEY not set.")
        return None, 401
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code >= 400:
            return r.text, r.status_code
        return r.json(), r.status_code
    except Exception as e:
        LOG.exception("Printify API request failed: %s", e)
        return None, 500


def fetch_shops():
    data, status = api_get("/shops.json")
    if status != 200:
        LOG.error("Failed to fetch shops: status=%s body=%s", status, data)
        return []
    # Printify returns a list; if wrapper used, adapt accordingly
    return data if isinstance(data, list) else []


def fetch_orders(shop_id):
    data, status = api_get(f"/shops/{shop_id}/orders.json")
    if status != 200:
        LOG.error("Failed to fetch orders for shop %s: status=%s body=%s",
                  shop_id, status, data)
        return []
    # Printify returns dict with 'data' key sometimes; handle both
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data if isinstance(data, list) else []


def make_invoice_pdf(order):
    """
    Create a minimal invoice PDF using reportlab if available, else write a simple text .txt fallback.
    Filename: DailyReport/out/<orderid>_invoice.pdf (or .txt)
    """
    order_id = str(
        order.get("id") or order.get("order_id") or order.get("order_number")
        or datetime.now().timestamp())
    filename_pdf = OUT_DIR / f"{order_id}_invoice.pdf"
    filename_txt = OUT_DIR / f"{order_id}_invoice.txt"

    # prepare fields
    status = order.get("status", "")
    total = order.get("total_price") or order.get("total") or ""
    buyer = order.get("shipping_address") or order.get("recipient") or {}
    recipient = buyer.get("name", "") if isinstance(buyer, dict) else ""
    address = " ".join(
        [buyer.get(k, "")
         for k in ("address1", "city",
                   "country")]) if isinstance(buyer, dict) else ""

    items = order.get("line_items") or order.get("items") or []

    if reportlab:
        try:
            c = canvas.Canvas(str(filename_pdf), pagesize=A4)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(40, 800, f"Invoice — Order {order_id}")
            c.setFont("Helvetica", 11)
            c.drawString(40, 780, f"Status: {status}")
            c.drawString(40, 760, f"Total: {total}")
            c.drawString(40, 740, f"Recipient: {recipient}")
            c.drawString(40, 720, f"Address: {address}")
            y = 680
            for it in items:
                if y < 60: break
                title = it.get("title") or it.get("product_title") or str(
                    it.get("id", ""))
                qty = it.get("quantity", it.get("qty", 1))
                price = it.get("price", "")
                c.drawString(40, y, f"{title}  x{qty}   {price}")
                y -= 18
            c.showPage()
            c.save()
            return filename_pdf
        except Exception:
            LOG.exception("Failed to write PDF invoice; falling back to text")
    # fallback: write a text invoice
    try:
        with open(filename_txt, "w") as fh:
            fh.write(
                f"Invoice — Order {order_id}\nStatus: {status}\nTotal: {total}\nRecipient: {recipient}\nAddress: {address}\n\nItems:\n"
            )
            for it in items:
                title = it.get("title") or it.get("product_title") or str(
                    it.get("id", ""))
                qty = it.get("quantity", it.get("qty", 1))
                price = it.get("price", "")
                fh.write(f"- {title} x{qty} {price}\n")
        return filename_txt
    except Exception:
        LOG.exception("Failed to write fallback invoice file")
        return None


def process_orders_for_shop(shop):
    shop_id = shop.get("id")
    shop_title = shop.get("title") or shop.get("name") or str(shop_id)
    LOG.info("Checking shop %s (%s)", shop_title, shop_id)
    orders = fetch_orders(shop_id)
    if not orders:
        LOG.info("No orders for shop %s", shop_id)
        return
    # orders is expected list of dicts
    for order in orders:
        # identify order id
        oid = str(
            order.get("id") or order.get("order_id")
            or order.get("order_number"))
        if not oid:
            LOG.warning("Skipping order without id: %s", order)
            continue
        if oid in seen_orders:
            LOG.debug("Order %s already seen", oid)
            continue
        LOG.info("New order found: %s", oid)
        # create invoice
        try:
            pdf = make_invoice_pdf(order)
            LOG.info("Created invoice file: %s", pdf)
        except Exception:
            LOG.exception("Failed to create invoice for order %s", oid)
        # mark seen and persist
        seen_orders.add(oid)
        save_state()


def run_once():
    LOG.info("Starting Printify connector run at %s",
             datetime.utcnow().isoformat())
    shops = fetch_shops()
    if not shops:
        LOG.warning("No shops found or failed to fetch shops.")
        return
    for s in shops:
        process_orders_for_shop(s)


def main_loop():
    LOG.info("Printify connector starting. Interval %s seconds", INTERVAL)
    while True:
        try:
            run_once()
        except Exception:
            LOG.exception("Unhandled error in main loop")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main_loop()
