#!/usr/bin/env python3
"""
connectors/meshy_youtube_connector.py

Combined connector for:
- Meshy AI Store (sales & invoices)
- YouTube Automation (daily stats summary)

Behavior:
- Reads MESHY_API_KEY and MESHY_API_URL (optional) from env
- Reads YOUTUBE_API_KEY (recommended) or falls back to YOUTUBE_CLIENT_ID/SECRET (not implemented OAuth) from env
- Polls both services every MESHY_YT_INTERVAL_S seconds (default 300s)
- Writes output JSON to DailyReport/out/meshy_<DD-MM-YYYY>.json and youtube_<DD-MM-YYYY>.json
- For each new Meshy sale, creates a minimal invoice PDF in DailyReport/out/<saleid>_meshy_invoice.pdf
- Keeps seen-state JSON files in connectors/ to avoid duplicate invoices

Requirements:
- pip install requests reportlab

Start (background):
  export MESHY_API_KEY="..."
  export YOUTUBE_API_KEY="..."
  nohup python3 connectors/meshy_youtube_connector.py > logs/meshy_youtube.log 2>&1 &

"""

import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

# PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# Config
LOG = logging.getLogger("meshy_youtube")
LOG.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
LOG.addHandler(handler)

MESHY_API_KEY = os.getenv("MESHY_API_KEY")
MESHY_API_URL = os.getenv("MESHY_API_URL", "https://api.meshy.ai/v1")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
# Optional: YOUTUBE_CLIENT_ID/SECRET not used in this simple connector

INTERVAL = int(os.getenv("MESHY_YT_INTERVAL_S", "300"))
OUT_DIR = Path("DailyReport/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR = Path("connectors")
STATE_DIR.mkdir(parents=True, exist_ok=True)

MESHY_STATE = STATE_DIR / "meshy_seen_sales.json"
# YouTube doesn't create invoices, but we can track last-pulled timestamp
YOUTUBE_STATE = STATE_DIR / "youtube_state.json"

# Load state helpers


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
        return default
    except Exception:
        LOG.exception("Failed to load state %s", path)
        return default


def save_json(path, data):
    try:
        path.write_text(json.dumps(data, indent=2))
    except Exception:
        LOG.exception("Failed to save state %s", path)


seen_sales = set(load_json(MESHY_STATE, []))
youtube_state = load_json(YOUTUBE_STATE, {"last_pull": None})

# ---------------- Meshy functions ----------------


def meshy_api_get(endpoint, params=None):
    if not MESHY_API_KEY:
        LOG.error("MESHY_API_KEY not set in env")
        return None, 401
    url = MESHY_API_URL.rstrip("/") + endpoint
    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        if r.status_code >= 400:
            LOG.error("Meshy API error %s: %s", r.status_code, r.text)
            return r.text, r.status_code
        return r.json(), r.status_code
    except Exception as e:
        LOG.exception("Meshy API request failed: %s", e)
        return None, 500


def fetch_meshy_sales(since=None):
    """Fetch recent sales from Meshy. `since` can be an ISO timestamp to fetch incremental sales if supported."""
    params = {}
    if since:
        params["since"] = since
    data, status = meshy_api_get("/sales", params=params)
    if status != 200:
        return []
    # Expect list of sales
    if isinstance(data, dict) and data.get("data"):
        sales = data["data"]
    elif isinstance(data, list):
        sales = data
    else:
        sales = []
    return sales


def make_invoice_pdf_for_sale(sale):
    order_id = str(
        sale.get("id") or sale.get("sale_id") or f"meshy-{int(time.time())}")
    filename_pdf = OUT_DIR / f"{order_id}_meshy_invoice.pdf"
    filename_txt = OUT_DIR / f"{order_id}_meshy_invoice.txt"

    buyer = sale.get("buyer") or sale.get("customer") or {}
    items = sale.get("items") or sale.get("line_items") or []
    total = sale.get("total_amount") or sale.get("total") or sale.get("price")

    if REPORTLAB_AVAILABLE:
        try:
            c = canvas.Canvas(str(filename_pdf), pagesize=A4)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(40, 800, f"Invoice — Meshy Sale {order_id}")
            c.setFont("Helvetica", 11)
            c.drawString(40, 780, f"Total: {total}")
            c.drawString(40, 760, f"Buyer: {buyer.get('name','')}")
            c.drawString(40, 740, f"Email: {buyer.get('email','')}")
            y = 700
            for it in items:
                if y < 60:
                    break
                title = it.get("title") or it.get("name") or str(
                    it.get("id", ""))
                qty = it.get("quantity", it.get("qty", 1))
                price = it.get("price", "")
                c.drawString(40, y, f"{title}  x{qty}   {price}")
                y -= 16
            c.showPage()
            c.save()
            LOG.info("Wrote Meshy invoice PDF %s", filename_pdf)
            return str(filename_pdf)
        except Exception:
            LOG.exception(
                "Failed to write reportlab PDF, will fallback to text")
    # fallback: write text invoice
    try:
        with open(filename_txt, "w") as fh:
            fh.write(
                f"Invoice — Meshy Sale {order_id}\nTotal: {total}\nBuyer: {buyer.get('name','')}\nEmail: {buyer.get('email','')}\n\nItems:\n"
            )
            for it in items:
                title = it.get("title") or it.get("name") or str(
                    it.get("id", ""))
                qty = it.get("quantity", it.get("qty", 1))
                price = it.get("price", "")
                fh.write(f"- {title} x{qty} {price}\n")
        LOG.info("Wrote Meshy invoice text %s", filename_txt)
        return str(filename_txt)
    except Exception:
        LOG.exception("Failed to write fallback Meshy invoice file")
        return None


# ---------------- YouTube functions ----------------


def fetch_youtube_stats(api_key, channel_id=None):
    """Fetch simple daily stats using YouTube Data API (requires API key and channelId). Returns summary dict."""
    if not api_key:
        LOG.error("YOUTUBE_API_KEY not set in env")
        return None
    # Use the YouTube Analytics / Data APIs; for simplicity we can pull channel statistics
    # Endpoint: https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channelId}&key={api_key}
    # If channel_id is not provided, the API requires OAuth; so we expect YOUTUBE_CHANNEL_ID env if using API key.
    channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
    if not channel_id:
        LOG.warning(
            "YOUTUBE_CHANNEL_ID not set — cannot fetch channel stats with API key. Set YOUTUBE_CHANNEL_ID or use OAuth."
        )
        return None
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics,snippet",
        "id": channel_id,
        "key": api_key,
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            LOG.error("YouTube API error %s: %s", r.status_code, r.text)
            return None
        data = r.json()
        items = data.get("items", [])
        if not items:
            LOG.warning("No channel data returned for channel_id %s",
                        channel_id)
            return None
        ch = items[0]
        stats = ch.get("statistics", {})
        snippet = ch.get("snippet", {})
        summary = {
            "channelId": channel_id,
            "title": snippet.get("title"),
            "subscribers": int(stats.get("subscriberCount") or 0),
            "views": int(stats.get("viewCount") or 0),
            "videoCount": int(stats.get("videoCount") or 0),
            "fetched_at": datetime.utcnow().isoformat(),
        }
        return summary
    except Exception:
        LOG.exception("Failed to fetch YouTube stats")
        return None


# ---------------- Main loop ----------------


def run_once():
    LOG.info("Starting Meshy+YouTube run at %s", datetime.utcnow().isoformat())
    date_str = datetime.now().strftime("%d-%m-%Y")

    # Meshy: fetch sales
    try:
        last_since = None
        # If we have seen sales, we can pass last pull time
        if youtube_state.get("last_pull"):
            last_since = youtube_state.get("last_pull")
        sales = fetch_meshy_sales(since=last_since)
        LOG.info("Fetched %d sales from Meshy", len(sales))
        # Save full dump
        mesh_out = OUT_DIR / f"meshy_{date_str}.json"
        mesh_out.write_text(json.dumps(sales, indent=2))
        # Process new sales
        for s in sales:
            sid = str(s.get("id") or s.get("sale_id") or s.get("order_id"))
            if not sid:
                continue
            if sid in seen_sales:
                LOG.debug("Meshy sale %s already processed", sid)
                continue
            LOG.info("Processing new Meshy sale %s", sid)
            invoice = make_invoice_pdf_for_sale(s)
            if invoice:
                LOG.info("Generated invoice for sale %s -> %s", sid, invoice)
            seen_sales.add(sid)
        save_json(MESHY_STATE, list(seen_sales))
    except Exception:
        LOG.exception("Error during Meshy processing")

    # YouTube: fetch stats
    try:
        yt_summary = fetch_youtube_stats(YOUTUBE_API_KEY)
        if yt_summary:
            yt_out = OUT_DIR / f"youtube_{date_str}.json"
            yt_out.write_text(json.dumps(yt_summary, indent=2))
            LOG.info("Wrote YouTube summary to %s", yt_out)
        # update last pull
        youtube_state["last_pull"] = datetime.utcnow().isoformat()
        save_json(YOUTUBE_STATE, youtube_state)
    except Exception:
        LOG.exception("Error during YouTube processing")


def main_loop():
    LOG.info("Starting Meshy+YouTube connector. Interval %s seconds", INTERVAL)
    while True:
        try:
            run_once()
        except Exception:
            LOG.exception("Unhandled exception in main loop")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main_loop()
