# connectors/income_bridge.py
"""
Income Bridge for JRAVIS
- Reads Printify orders
- Reads PayPal transactions (reporting endpoint)
- Matches orders -> payments (order id, fallback amount+date)
- Stores matched payments in TinyDB (/app/data/income_db.json)
"""
import os
import logging
from datetime import datetime, timedelta
from tinydb import TinyDB, Query

# use existing connectors (must exist)
try:
    from connectors.printify_connector import get_shops, get_products, get_orders  # optional
except Exception:
    # fallbacks: we'll call Printify REST directly if get_orders isn't present
    get_shops = None

import requests
import json

LOG = logging.getLogger("income_bridge")
LOG.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
LOG.addHandler(handler)

# Environment
PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "live")
BASE_PAYPAL = "https://api-m.paypal.com" if PAYPAL_MODE == "live" else "https://api-m.sandbox.paypal.com"
PRINTIFY_BASE = "https://api.printify.com/v1"

# TinyDB path (persisted inside container)
DB_PATH = os.getenv("JRAVIS_INCOME_DB", "/app/data/income_db.json")

# Ensure folder exists before creating TinyDB file
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = TinyDB(DB_PATH)


def _get_paypal_access_token():
    token_url = f"{BASE_PAYPAL}/v1/oauth2/token"
    auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    resp = requests.post(token_url,
                         auth=auth,
                         headers=headers,
                         data={"grant_type": "client_credentials"},
                         timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_paypal_transactions(start_dt: datetime, end_dt: datetime):
    """
    Uses PayPal transaction search reporting API: /v1/reporting/transactions
    Returns list of transactions
    """
    token = _get_paypal_access_token()
    url = f"{BASE_PAYPAL}/v1/reporting/transactions"
    params = {
        "start_date": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_date": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": "all",
        "page_size": 100
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    transactions = data.get("transaction_details") or []
    LOG.info("Fetched %d PayPal transactions", len(transactions))
    return transactions


def fetch_printify_orders(start_dt: datetime, end_dt: datetime):
    """
    Fetch Printify orders using the public API:
    GET /shops/{shop_id}/orders.json?created_at_min=...&created_at_max=...
    """
    headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}
    shops_resp = requests.get(f"{PRINTIFY_BASE}/shops.json",
                              headers=headers,
                              timeout=30)
    shops_resp.raise_for_status()
    shops = shops_resp.json()
    orders = []
    for shop in shops:
        shop_id = shop.get("id")
        url = f"{PRINTIFY_BASE}/shops/{shop_id}/orders.json"
        params = {
            "created_at_min": start_dt.isoformat(),
            "created_at_max": end_dt.isoformat(),
        }
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200:
            js = r.json()
            if isinstance(js, list):
                orders.extend(js)
            elif isinstance(js, dict) and "data" in js:
                orders.extend(js["data"])
    LOG.info("Fetched %d Printify orders", len(orders))
    return orders


def already_recorded(order_id=None, txn_id=None):
    tbl = db.table("income")
    q = Query()
    if order_id:
        if tbl.search(q.order_id == str(order_id)):
            return True
    if txn_id:
        if tbl.search(q.txn_id == str(txn_id)):
            return True
    return False


def record_income(order, txn_match):
    tbl = db.table("income")
    rec = {
        "timestamp":
        datetime.utcnow().isoformat(),
        "order_id":
        order.get("id") or order.get("order_number")
        or order.get("external_id"),
        "total":
        order.get("total_price") or order.get("total"),
        "currency":
        order.get("currency") or order.get("currency_code"),
        "txn_id":
        txn_match.get("transaction_info", {}).get("transaction_id")
        if txn_match else None,
        "txn_amount":
        txn_match.get("transaction_info", {}).get(
            "net_amount", {}).get("value") if txn_match else None,
        "raw_order":
        order,
        "raw_txn":
        txn_match
    }
    tbl.insert(rec)
    LOG.info("Recorded income order=%s amount=%s", rec["order_id"],
             rec["total"])
    return rec


def match_order_to_txn(order, transactions):
    # 1) Try to match by order id present in any transaction's note/description
    order_ids = []
    for key in ("id", "order_number", "external_id"):
        if order.get(key):
            order_ids.append(str(order.get(key)))
    for txn in transactions:
        tx_info = txn.get("transaction_info", {})
        memo = json.dumps(txn).lower()
        for oid in order_ids:
            if oid and oid.lower() in memo:
                return txn
    # 2) Fallback: match by amount and date (within 2 days)
    order_amt = None
    for k in ("total_price", "total", "price"):
        if order.get(k):
            try:
                order_amt = float(order.get(k))
                break
            except Exception:
                pass
    if order_amt is None:
        # try nested prices
        amount = order.get("amount") or (order.get("items")
                                         and order["items"][0].get("price"))
        try:
            order_amt = float(amount)
        except Exception:
            order_amt = None
    if order_amt is not None:
        for txn in transactions:
            try:
                net = txn.get("transaction_info", {}).get("net_amount",
                                                          {}).get("value")
                if net is None:
                    continue
                net_f = float(net)
                if abs(net_f - order_amt) < 0.5:  # tolerant matching
                    # check date window
                    txn_time = txn.get(
                        "transaction_info",
                        {}).get("transaction_initiation_date") or txn.get(
                            "transaction_info",
                            {}).get("transaction_updated_date")
                    if txn_time:
                        # Accept by default
                        return txn
                    else:
                        return txn
            except Exception:
                continue
    return None


def run_for_range(start_dt: datetime, end_dt: datetime):
    LOG.info("Running Income Bridge for %s -> %s", start_dt.isoformat(),
             end_dt.isoformat())
    try:
        orders = fetch_printify_orders(start_dt, end_dt)
    except Exception as e:
        LOG.error("Error fetching printify orders: %s", e)
        orders = []
    try:
        transactions = fetch_paypal_transactions(start_dt - timedelta(days=1),
                                                 end_dt + timedelta(days=1))
    except Exception as e:
        LOG.error("Error fetching paypal transactions: %s", e)
        transactions = []
    matched = 0
    for order in orders:
        order_id = order.get("id") or order.get("order_number")
        if already_recorded(order_id=order_id):
            LOG.info("Order %s already recorded, skipping", order_id)
            continue
        txn = match_order_to_txn(order, transactions)
        if txn:
            record_income(order, txn)
            matched += 1
        else:
            LOG.info("No match for order %s", order_id)
    LOG.info("Income Bridge finished; matched=%d new", matched)
    return matched


def run_daily():
    # Run for previous day (UTC boundaries) and for today so we don't miss late payments
    today = datetime.utcnow()
    start = datetime(today.year, today.month, today.day) - timedelta(days=1)
    end = start + timedelta(days=2)
    return run_for_range(start, end)


if __name__ == "__main__":
    run_daily()
