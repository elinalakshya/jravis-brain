#!/usr/bin/env python3
"""
Phase-1 runner:
- Imports connectors/<name>.py modules (each must expose run() -> dict)
- Runs each with timeout & simple retry
- Writes DailyReport/out/connector_results.json
- Triggers local VA Bot endpoint /send-now via GET to send the report
"""

import importlib
import json
import os
import sys
import multiprocessing as mp
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "DailyReport" / "out"
OUT.mkdir(parents=True, exist_ok=True)

# Connector module names (adjust to match your repo)
CONNECTORS = [
    "printify",
    "meshy",
    "youtube",
    "instagram",
    "printify",  # kept here only if you have multiple variants — remove duplicates
    "cadcrowd",
    "fiverr",
    "youtube_analytics",  # examples — make them match your actual filenames
    "meshy_store",
    "misc_payments"
]

# Timeout per connector run (seconds)
TIMEOUT = 60 * 3
RETRIES = 2


def _run_module(connector_name, return_dict):
    """Child process target: import module and call run()"""
    try:
        mod = importlib.import_module(f"connectors.{connector_name}")
    except Exception as e:
        return_dict['error'] = f"import_error: {e}"
        return
    if not hasattr(mod, "run"):
        return_dict['error'] = "no_run_function"
        return
    try:
        res = mod.run()
        return_dict['result'] = res
    except Exception as e:
        return_dict['error'] = f"run_exception: {e}"


def run_with_timeout(name, timeout=TIMEOUT, retries=RETRIES):
    for attempt in range(1, retries + 1):
        manager = mp.Manager()
        return_dict = manager.dict()
        p = mp.Process(target=_run_module, args=(name, return_dict))
        p.start()
        p.join(timeout)
        if p.is_alive():
            p.terminate()
            p.join()
            status = {"status": "timeout", "attempt": attempt}
        else:
            status = {"status": "done", "attempt": attempt}
            if 'result' in return_dict:
                status.update(return_dict['result'])
            elif 'error' in return_dict:
                status['error'] = return_dict['error']
        # if successful (no error and done), return
        if status.get("status") == "done" and "error" not in status:
            return status
        # otherwise retry
        time.sleep(1)
    return status


def load_env_or_secret(key, filename=None):
    val = os.getenv(key)
    if val:
        return val
    if filename:
        p = ROOT / "secrets" / filename
        if p.exists():
            return p.read_text().strip()
    return None


def trigger_send_now():
    url = "http://127.0.0.1:8000/send-now"
    try:
        req = Request(url, headers={"User-Agent": "va-bot-runner/1"})
        with urlopen(req, timeout=10) as r:
            return {
                "ok": True,
                "code": r.getcode(),
                "msg": r.read(200).decode(errors="ignore")
            }
    except HTTPError as e:
        return {"ok": False, "code": e.code, "reason": str(e)}
    except URLError as e:
        return {"ok": False, "reason": str(e)}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


def main():
    results = {}
    # ensure connectors package is importable
    sys.path.insert(0, str(ROOT))

    # Check required creds (Printify, Meshy, YouTube)
    missing = []
    if not (load_env_or_secret("PRINTIFY_API_KEY", "printify.key")):
        missing.append("PRINTIFY_API_KEY / secrets/printify.key")
    if not (load_env_or_secret("MESHY_API_KEY", "meshy.key")):
        missing.append("MESHY_API_KEY / secrets/meshy.key")
    # YouTube needs client id/secret/refresh
    ycid = load_env_or_secret("YOUTUBE_CLIENT_ID")
    ycsec = load_env_or_secret("YOUTUBE_CLIENT_SECRET")
    yrt = load_env_or_secret("YOUTUBE_REFRESH_TOKEN", "youtube.json")
    if not (ycid and ycsec and yrt):
        missing.append(
            "YouTube credentials (YOUTUBE_CLIENT_ID/SECRET/REFRESH or secrets/youtube.json)"
        )

    if missing:
        print("⚠️ Missing required credentials (provide these and re-run):")
        for m in missing:
            print("  -", m)
        # still proceed to run non-dependent connectors
    else:
        print("✅ Required credentials present (Printify, Meshy, YouTube)")

    for name in CONNECTORS:
        name = name.strip()
        if not name:
            continue
        print(f"→ Running connector: {name}")
        try:
            r = run_with_timeout(name)
        except Exception as e:
            r = {"status": "exception", "error": str(e)}
        results[name] = r
        print(f"  <- {r}")

    # write results to disk
    out_file = OUT / "connector_results.json"
    out_file.write_text(
        json.dumps({
            "ts": time.time(),
            "results": results
        }, indent=2))
    print(f"Results written to {out_file}")

    # Optionally trigger the VA Bot send-now to generate/send report (GET)
    print(
        "Triggering VA Bot send-now endpoint to assemble report and send email..."
    )
    send_result = trigger_send_now()
    print("send-now result:", send_result)
    results["_send_now"] = send_result

    # final write
    out_file.write_text(
        json.dumps({
            "ts": time.time(),
            "results": results
        }, indent=2))
    print("Done.")


if __name__ == "__main__":
    main()
