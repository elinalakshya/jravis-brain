#!/usr/bin/env python3
"""
income_core_cloud.py  — JRAVIS Phase 2 Income Core (LIVE MODE)

Usage:
  - Provide all required environment variables (see top of file)
  - Register webhooks in provider dashboards pointing to:
        https://<your-render-or-replit-url>/webhook/paypal
        https://<your-url>/webhook/printify
        https://<your-url>/webhook/etsy
        https://<your-url>/webhook/fiverr
  - Run: python income_core_cloud.py

Notes & Safety:
  - This is live-mode code. Do NOT commit credentials to git.
  - You must create app credentials on each platform and paste them into your environment secrets.
"""

import os
import time
import hmac
import json
import base64
import hashlib
import threading
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
from fpdf import FPDF

# ------------------------
# Configuration via env
# ------------------------
LIVE_MODE = os.getenv("LIVE_MODE", "1")  # "1" means live
PORT = int(os.getenv("PORT", "3300"))
HOST = "0.0.0.0"

# PayPal
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_WEBHOOK_ID = os.getenv(
    "PAYPAL_WEBHOOK_ID")  # PayPal webhook ID registered in dashboard

# Printify
PRINTIFY_TOKEN = os.getenv("PRINTIFY_TOKEN")
PRINTIFY_SHOP_ID = os.getenv("PRINTIFY_SHOP_ID")

# Etsy (API key / oauth token)
ETSY_API_KEY = os.getenv("ETSY_API_KEY")
ETSY_OAUTH_TOKEN = os.getenv("ETSY_OAUTH_TOKEN")

# Fiverr (API credentials)
FIVERR_API_KEY = os.getenv("FIVERR_API_KEY")
FIVERR_SECRET = os.getenv("FIVERR_SECRET")

# JRAVIS email/invoice config (reuses daily_cycle settings)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
RECEIVER_EMAIL = os.getenv("REPORT_RECIPIENT", "nrveeresh327@gmail.com")
LOCK_CODE = os.getenv("LOCK_CODE")  # optional PDF lock

# Data & DB
DB_FILE = os.getenv("JRAVIS_DB", "jravis_ledger.json")
db = TinyDB(DB_FILE)


# Logging helper
def now():
    return datetime.utcnow().isoformat() + "Z"


def log(*args):
    print("[IncomeCore]", now(), *args)


# ------------------------
# PayPal helpers
# ------------------------
_paypal_token_cache = {"token": None, "expires_at": 0}


def paypal_get_access_token():
    """Get OAuth token from PayPal (live)."""
    if _paypal_token_cache["token"] and _paypal_token_cache[
            "expires_at"] > time.time() + 30:
        return _paypal_token_cache["token"]
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise RuntimeError("PayPal credentials missing in environment.")
    url = "https://api.paypal.com/v1/oauth2/token"
    auth = (PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET)
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    r = requests.post(url, headers=headers, data=data, auth=auth, timeout=15)
    r.raise_for_status()
    j = r.json()
    token = j["access_token"]
    expires_in = int(j.get("expires_in", 3600))
    _paypal_token_cache["token"] = token
    _paypal_token_cache["expires_at"] = time.time() + expires_in
    log("Got PayPal access token.")
    return token


def paypal_verify_webhook(headers, body_json):
    """
    Verify PayPal webhook using the verify API. Requires PAYPAL_WEBHOOK_ID env var.
    Returns True if verified.
    """
    if not PAYPAL_WEBHOOK_ID:
        log("WARN: PAYPAL_WEBHOOK_ID not set; skipping verify.")
        return False
    token = paypal_get_access_token()
    url = "https://api.paypal.com/v1/notifications/verify-webhook-signature"
    payload = {
        "auth_algo": headers.get("paypal-auth-algo"),
        "cert_url": headers.get("paypal-cert-url"),
        "transmission_id": headers.get("paypal-transmission-id"),
        "transmission_sig": headers.get("paypal-transmission-sig"),
        "transmission_time": headers.get("paypal-transmission-time"),
        "webhook_id": PAYPAL_WEBHOOK_ID,
        "webhook_event": body_json
    }
    resp = requests.post(url,
                         json=payload,
                         headers={"Authorization": f"Bearer {token}"},
                         timeout=15)
    try:
        resp.raise_for_status()
        verified = resp.json().get("verification_status") == "SUCCESS"
        log("PayPal webhook verification status:", verified)
        return verified
    except Exception as e:
        log("PayPal webhook verify error:", e,
            resp.text if resp is not None else "")
        return False


# ------------------------
# Vendor API placeholders (live endpoints)
# ------------------------
# Printify: https://developers.printify.com
def printify_get_order(order_id):
    if not PRINTIFY_TOKEN:
        raise RuntimeError("PRINTIFY_TOKEN not configured.")
    url = f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/orders/{order_id}.json"
    headers = {"Authorization": f"Bearer {PRINTIFY_TOKEN}"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


# Etsy (example polling; real API uses OAuth2 and different endpoints)
def etsy_get_order(order_id):
    if not ETSY_OAUTH_TOKEN:
        raise RuntimeError("ETSY_OAUTH_TOKEN missing.")
    # This is illustrative; adapt to your Etsy API plan
    url = f"https://openapi.etsy.com/v3/application/shops/{ETSY_API_KEY}/receipts/{order_id}"
    headers = {"Authorization": f"Bearer {ETSY_OAUTH_TOKEN}"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


# Fiverr placeholder (official API access is via approved partners / API)
def fiverr_get_order(order_id):
    if not FIVERR_API_KEY:
        raise RuntimeError("FIVERR_API_KEY missing.")
    url = f"https://api.fiverr.com/v1/orders/{order_id}"
    headers = {"Authorization": f"Bearer {FIVERR_API_KEY}"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ------------------------
# Order processing: unify different platform payloads
# ------------------------
def generate_invoice_pdf(order_record, out_path):
    """Generate a simple invoice PDF for a single order."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, f"JRAVIS Invoice", ln=True)
    pdf.cell(0, 8, f"Order ID: {order_record['order_id']}", ln=True)
    pdf.cell(0, 8, f"Platform: {order_record['platform']}", ln=True)
    pdf.cell(0, 8, f"Buyer: {order_record.get('buyer_name','-')}", ln=True)
    pdf.cell(0,
             8,
             f"Amount: {order_record['currency']} {order_record['amount']}",
             ln=True)
    pdf.ln(6)
    pdf.multi_cell(0, 6, f"Details: {order_record.get('notes','-')}")
    pdf.output(out_path)
    return out_path


def record_order_in_ledger(order_record):
    # Save to TinyDB ledger (deduplicate by platform+order_id)
    Orders = Query()
    existing = db.search((Orders.platform == order_record["platform"])
                         & (Orders.order_id == order_record["order_id"]))
    if existing:
        log("Order already recorded:", order_record["platform"],
            order_record["order_id"])
        return False
    db.insert({
        "platform": order_record["platform"],
        "order_id": order_record["order_id"],
        "amount": order_record["amount"],
        "currency": order_record.get("currency", "USD"),
        "buyer": order_record.get("buyer_name"),
        "timestamp": now(),
        "raw": order_record
    })
    log("Recorded order in ledger:", order_record["platform"],
        order_record["order_id"])
    return True


def notify_post_order(order_record, invoice_path):
    # This ties into daily/weekly report pipelines — we just log + attach invoice to backups
    log("Order processed:", order_record["platform"], order_record["order_id"],
        "invoice:", invoice_path)
    # Optionally email a quick notification (reusing daily mail settings)
    # Keep it lightweight in live mode to avoid rate limits


# The unified order pipeline
def process_order_unified(platform,
                          order_id,
                          amount,
                          currency="USD",
                          buyer_name=None,
                          notes=None):
    order_record = {
        "platform": platform,
        "order_id": str(order_id),
        "amount": float(amount),
        "currency": currency,
        "buyer_name": buyer_name or "",
        "notes": notes or ""
    }
    recorded = record_order_in_ledger(order_record)
    if not recorded:
        return False
    # generate invoice
    invoices_dir = os.path.join(os.getcwd(), "invoices")
    os.makedirs(invoices_dir, exist_ok=True)
    invoice_filename = f"invoice_{platform}_{order_id}.pdf"
    invoice_path = os.path.join(invoices_dir, invoice_filename)
    generate_invoice_pdf(order_record, invoice_path)
    notify_post_order(order_record, invoice_path)
    return True


# ------------------------
# Flask Webhooks
# ------------------------
app = Flask("income_core")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": now()})


@app.route("/webhook/paypal", methods=["POST"])
def webhook_paypal():
    try:
        body = request.get_json(force=True)
    except Exception as e:
        log("Invalid JSON in PayPal webhook:", e)
        return jsonify({"error": "invalid json"}), 400

    headers = {k.lower(): v for k, v in request.headers.items()}
    verified = False
    try:
        verified = paypal_verify_webhook(headers, body)
    except Exception as e:
        log("PayPal verify error:", e)
    # If unable to verify but in LIVE mode, reject; if no webhook id, accept but log
    if not verified and PAYPAL_WEBHOOK_ID:
        log("Paypal webhook not verified; rejecting")
        return jsonify({"error": "not verified"}), 400

    # Check event type
    event_type = body.get("event_type")
    log("PayPal webhook event:", event_type)
    # Example: CHECKOUT.ORDER.APPROVED or PAYMENT.CAPTURE.COMPLETED
    if event_type in ("CHECKOUT.ORDER.APPROVED", "PAYMENT.CAPTURE.COMPLETED",
                      "CHECKOUT.ORDER.COMPLETED"):
        resource = body.get("resource", {})
        # resource may be capture or order, adapt as needed
        order_id = resource.get("id") or resource.get(
            "order_id") or resource.get("invoice_id")
        # Try to derive amount
        amount = None
        currency = "USD"
        if resource.get("amount") and isinstance(resource["amount"], dict):
            amount = resource["amount"].get("value")
            currency = resource["amount"].get("currency_code", "USD")
        elif resource.get("purchase_units"):
            pu = resource["purchase_units"][0]
            amount = pu.get("amount", {}).get("value")
            currency = pu.get("amount", {}).get("currency_code", "USD")
        if amount:
            # record
            ok = process_order_unified(
                "paypal",
                order_id,
                amount,
                currency,
                buyer_name=resource.get("payer", {}).get("name",
                                                         {}).get("given_name"))
            return jsonify({"ok": ok}), 200
    return jsonify({"ok": False, "note": "unhandled_event"}), 200


@app.route("/webhook/printify", methods=["POST"])
def webhook_printify():
    # Printify posts order payloads; refer to Printify docs for exact shape
    try:
        data = request.get_json(force=True)
    except Exception as e:
        log("Invalid JSON in Printify webhook:", e)
        return jsonify({"error": "invalid json"}), 400
    log("Printify webhook received.")
    order_id = data.get("id") or data.get("order_id")
    total = None
    if data.get("total_price"):
        total = data["total_price"]
    if order_id and total:
        ok = process_order_unified("printify",
                                   order_id,
                                   total,
                                   currency=data.get("currency", "USD"),
                                   buyer_name=data.get("recipient",
                                                       {}).get("name"))
        return jsonify({"ok": ok}), 200
    return jsonify({"ok": False}), 200


@app.route("/webhook/etsy", methods=["POST"])
def webhook_etsy():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        log("Invalid JSON in Etsy webhook:", e)
        return jsonify({"error": "invalid json"}), 400
    # Etsy payloads vary; adapt mapping
    order_id = data.get("receipt_id") or data.get("order_id") or data.get("id")
    total = data.get("grandtotal", {}).get("amount") if isinstance(
        data.get("grandtotal"),
        dict) else data.get("price") or data.get("total")
    if order_id and total:
        ok = process_order_unified("etsy",
                                   order_id,
                                   total,
                                   currency="USD",
                                   buyer_name=data.get("buyer_user_name"))
        return jsonify({"ok": ok}), 200
    return jsonify({"ok": False}), 200


@app.route("/webhook/fiverr", methods=["POST"])
def webhook_fiverr():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        log("Invalid JSON in Fiverr webhook:", e)
        return jsonify({"error": "invalid json"}), 400
    order_id = data.get("order_id") or data.get("id")
    total = data.get("amount") or data.get("price")
    if order_id and total:
        ok = process_order_unified("fiverr",
                                   order_id,
                                   total,
                                   currency="USD",
                                   buyer_name=data.get("buyer"))
        return jsonify({"ok": ok}), 200
    return jsonify({"ok": False}), 200


# ------------------------
# Pollers as fallback (in case webhooks not configured)
# ------------------------
def poll_printify_orders():
    log("Polling Printify for new orders...")
    # Example: printify_get_orders with date filter
    try:
        # Placeholder: adapt to Printify API to list orders
        url = f"https://api.printify.com/v1/shops/{PRINTIFY_SHOP_ID}/orders.json"
        headers = {"Authorization": f"Bearer {PRINTIFY_TOKEN}"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        orders = resp.json().get("orders", [])
        for o in orders:
            order_id = o.get("id")
            total = o.get("total_price")
            # attempt processing (recording is deduplicated)
            process_order_unified("printify",
                                  order_id,
                                  total,
                                  currency=o.get("currency", "USD"),
                                  buyer_name=o.get("recipient",
                                                   {}).get("name"))
    except Exception as e:
        log("Printify poll error:", e)


def poll_etsy_orders():
    log("Polling Etsy for new orders...")
    # Etsy API usage depends on your app scope; keep placeholder
    # Implement according to your Etsy API plan
    return


def poll_fiverr_orders():
    log("Polling Fiverr for new orders...")
    # Placeholder for Fiverr API polling
    return


# ------------------------
# Background scheduler thread to poll periodically
# ------------------------
def start_pollers_loop(interval_seconds=300):

    def loop():
        while True:
            try:
                poll_printify_orders()
                poll_etsy_orders()
                poll_fiverr_orders()
            except Exception as e:
                log("Poller loop error:", e)
            time.sleep(interval_seconds)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    log("Started vendor poller thread (interval seconds =", interval_seconds,
        ")")


# ------------------------
# Start app
# ------------------------
if __name__ == "__main__":
    log("Starting JRAVIS Income Core (LIVE MODE)" if LIVE_MODE ==
        "1" else "starting in sandbox mode")
    # Start poller thread
    start_pollers_loop(
        interval_seconds=300)  # poll every 5 minutes as fallback
    # Run Flask app
    app.run(host=HOST, port=PORT)
