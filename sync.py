# sync.py
from datetime import datetime
from db import upsert_stream_earnings, get_streams
import time, os

STATUS = {"last_sync": None, "running": False, "message": ""}

# import connector functions (stubs)
from connectors.printify import fetch_printify
from connectors.gumroad import fetch_gumroad
from connectors.shopify import fetch_shopify
from connectors.jravis_store import fetch_jravis_store


def get_status():
    return STATUS


def _run_sync(source="manual"):
    try:
        STATUS["running"] = True
        STATUS[
            "message"] = f"Sync started by {source} at {datetime.utcnow().isoformat()}"
        # Call connectors - each returns list of dicts: {"id","name","amount","currency"}
        results = []
        for fn in (fetch_printify, fetch_gumroad, fetch_shopify,
                   fetch_jravis_store):
            try:
                res = fn()
                if res:
                    results.extend(res)
            except Exception as e:
                # keep going even if one connector fails
                print("Connector error:", e)
        # write to DB
        for s in results:
            upsert_stream_earnings(s["id"], s["name"], float(s["amount"]),
                                   s.get("currency", "USD"))
        STATUS["last_sync"] = datetime.utcnow().isoformat()
        STATUS["message"] = f"Sync completed at {STATUS['last_sync']}"
    finally:
        STATUS["running"] = False


def run_full_sync():
    _run_sync("internal")


def trigger_manual_sync(source="manual"):
    # run in background thread to return immediately to HTTP
    if STATUS["running"]:
        return
    t = threading.Thread(target=_run_sync, args=(source, ), daemon=True)
    t.start()
