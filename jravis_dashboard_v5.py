# -*- coding: utf-8 -*-
"""
JRAVIS Dashboard v5
Single-file Flask app to serve a simple Mission 2040 dashboard.

Features:
- / -> simple JSON dashboard summary (HTML could be plugged in)
- /health -> simple health check
- /api/live_progress -> JSON progress data
- /api/live_logs -> list of recent log lines (JSON array)
- /api/command -> POST to send a command (returns JSON)
- /api/trigger -> POST to trigger all streams (returns text)
- Background scheduler (APScheduler) to simulate progress updates
- Optional LOCK_CODE via environment variable (simple protection)

Dependencies: Flask, APScheduler, (optional) PyYAML for config
This file is intentionally self-contained and safe to deploy.
"""
from __future__ import annotations

import os
import sys
import time
import json
import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, List

from flask import Flask, jsonify, request, abort, make_response

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception as e:
    # Friendly error if APScheduler is missing
    raise RuntimeError(
        "APScheduler is required. Install APScheduler in your environment."
    ) from e

# ---------------------------
# Basic config & Flask app
# ---------------------------
APP_NAME = "JRAVIS Dashboard v5"
LOG_MAX_LINES = int(os.environ.get("LOG_MAX_LINES", "200"))
PROGRESS_STEP = float(os.environ.get("PROGRESS_STEP",
                                     "1.0"))  # percent per tick
PROGRESS_TICK_SECONDS = int(os.environ.get("PROGRESS_TICK_SECONDS",
                                           "10"))  # scheduler interval
LOCK_CODE = os.environ.get("LOCK_CODE")  # optional simple protection

app = Flask(__name__)
logger = logging.getLogger(APP_NAME)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------
# In-memory state (thread-safe)
# ---------------------------
_state_lock = threading.Lock()

_state: Dict[str, Any] = {
    "progress_percent": 0.0,
    "total_income": 0,
    "daily_income": 0,
    "last_loop": None,
    "streams_triggered": 0,
    "phase": 1,
}

_logs: deque[str] = deque(maxlen=LOG_MAX_LINES)


# ---------------------------
# Helpers
# ---------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def append_log(line: str) -> None:
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{ts}] {line}"
    with _state_lock:
        _logs.append(entry)
    logger.info(entry)


def get_logs(limit: int = 100) -> List[str]:
    with _state_lock:
        # Return newest-first for UI convenience (client can reverse)
        return list(_logs)[-limit:]


def money_fmt(amount: float) -> str:
    try:
        return f"{int(amount):,}"
    except Exception:
        return str(amount)


def check_lock(payload: Dict | None = None) -> bool:
    """
    If LOCK_CODE is set in env, require either:
    - Header 'X-Lock' matching LOCK_CODE OR
    - JSON body field 'lock' matching LOCK_CODE
    Otherwise allow.
    """
    if not LOCK_CODE:
        return True
    header = request.headers.get("X-Lock")
    if header and header == LOCK_CODE:
        return True
    if payload and isinstance(payload, dict):
        lock_field = payload.get("lock")
        if lock_field and str(lock_field) == LOCK_CODE:
            return True
    return False


# ---------------------------
# Scheduler job: heartbeat + progress update
# ---------------------------
def scheduler_tick():
    """
    Periodic job run by APScheduler.
    Updates progress and income metrics, writes logs.
    """
    try:
        with _state_lock:
            # Update progress
            prev = _state.get("progress_percent", 0.0)
            new = prev + PROGRESS_STEP
            if new >= 100.0:
                new = 0.0  # rollover when reaching 100
                _state["streams_triggered"] += 1
                append_log(
                    f"Progress reached 100% — loop completed (loops: {_state['streams_triggered']})"
                )
            _state["progress_percent"] = round(new, 3)

            # Simulate income increases
            inc = PROGRESS_STEP * 10.0  # raw simulation
            _state["total_income"] = int((_state.get("total_income", 0) or 0) +
                                         inc)
            _state["daily_income"] = int((_state.get("daily_income", 0) or 0) +
                                         inc / 6.0)

            _state["last_loop"] = now_iso()
            pct = _state["progress_percent"]

        append_log(
            f"Scheduler tick — progress now {pct}%; total_income INR {money_fmt(_state['total_income'])}"
        )
    except Exception as e:
        logger.exception("Error in scheduler_tick: %s", e)


# Start scheduler with safe defaults
scheduler = BackgroundScheduler(job_defaults={
    "max_instances": 2,
    "coalesce": True,
    "misfire_grace_time": 30
})
scheduler.add_job(scheduler_tick,
                  "interval",
                  seconds=PROGRESS_TICK_SECONDS,
                  id="scheduler_tick",
                  next_run_time=datetime.now())
scheduler.start()
logger.info("Scheduler started")


# ---------------------------
# Flask routes
# ---------------------------
@app.route("/health", methods=["GET"])
def health():
    """Simple health endpoint used by Render or load balancers."""
    return jsonify({"status": "ok", "time": now_iso()})


@app.route("/", methods=["GET"])
def dashboard():
    """Return a concise JSON dashboard summary (UI can be swapped in later)."""
    with _state_lock:
        snapshot = {
            "system": APP_NAME,
            "time": now_iso(),
            "progress_percent": _state.get("progress_percent", 0.0),
            "total_income": _state.get("total_income", 0),
            "daily_income": _state.get("daily_income", 0),
            "last_loop": _state.get("last_loop"),
            "phase": _state.get("phase", 1),
            "streams_triggered": _state.get("streams_triggered", 0),
        }
    return jsonify(snapshot)


@app.route("/api/live_progress", methods=["GET"])
def api_live_progress():
    with _state_lock:
        data = {
            "progress_percent": _state.get("progress_percent", 0.0),
            "total_income": _state.get("total_income", 0),
            "daily_income": _state.get("daily_income", 0),
            "last_loop": _state.get("last_loop"),
            "phase": _state.get("phase", 1),
            "streams_triggered": _state.get("streams_triggered", 0),
        }
    return jsonify(data)


@app.route("/api/live_logs", methods=["GET"])
def api_live_logs():
    # Return most recent logs (client can poll and update)
    limit = int(request.args.get("limit", "200"))
    logs = get_logs(limit=limit)
    return jsonify(logs)


@app.route("/api/command", methods=["POST"])
def api_command():
    """
    Accepts JSON: {"cmd": "<text>", "lock": "<code>" (optional if LOCK_CODE set)}
    Recognized commands:
      - "phase <n>" : set dashboard phase
      - "reset" : reset progress counters
      - "status" : returns current status
      - "trigger all" : triggers streams (same as /api/trigger)
    """
    if not request.is_json:
        return make_response(jsonify({"error": "expected JSON body"}), 400)
    payload = request.get_json()
    if not check_lock(payload):
        return make_response(jsonify({"error": "invalid lock code"}), 403)

    cmd = (payload.get("cmd") or "").strip()
    if not cmd:
        return make_response(jsonify({"error": "no cmd provided"}), 400)

    lower = cmd.lower()
    resp: Dict[str, Any] = {"cmd": cmd, "time": now_iso()}

    if lower.startswith("phase"):
        # parse number
        parts = cmd.split()
        n = 1
        if len(parts) >= 2:
            try:
                n = int(parts[1])
            except Exception:
                n = 1
        with _state_lock:
            _state["phase"] = n
        append_log(f"Manual command: set phase -> {n}")
        resp["result"] = f"phase set to {n}"

    elif lower == "reset":
        with _state_lock:
            _state["progress_percent"] = 0.0
            _state["total_income"] = 0
            _state["daily_income"] = 0
            _state["streams_triggered"] = 0
        append_log("Manual command: reset progress and income counters")
        resp["result"] = "reset done"

    elif "trigger all" in lower or lower == "trigger":
        # delegate to trigger endpoint behavior
        perform_trigger_actions()
        resp["result"] = "triggered"
    elif lower == "status":
        with _state_lock:
            resp["status"] = {
                "progress_percent": _state["progress_percent"],
                "total_income": _state["total_income"],
                "daily_income": _state["daily_income"],
                "phase": _state["phase"],
            }
    else:
        append_log(f"Unknown command received: {cmd}")
        resp["result"] = "unknown command"

    return jsonify(resp)


def perform_trigger_actions():
    """Simulate triggers across streams — safe to call from endpoints or scheduler."""
    with _state_lock:
        _state["streams_triggered"] = _state.get("streams_triggered", 0) + 1
        bonus = 500  # simulate bonus income for a trigger
        _state["total_income"] = int((_state.get("total_income", 0) or 0) +
                                     bonus)
        _state["daily_income"] = int((_state.get("daily_income", 0) or 0) +
                                     bonus / 6.0)
        _state["last_loop"] = now_iso()
    append_log(f"Triggered all streams (manual). Bonus INR {bonus}")


@app.route("/api/trigger", methods=["POST"])
def api_trigger():
    # simple trigger endpoint, protected by LOCK_CODE if set
    if not check_lock():
        return make_response("invalid lock code", 403)
    perform_trigger_actions()
    return "triggered"


# ---------------------------
# Graceful shutdown handling
# ---------------------------
def _shutdown_scheduler():
    try:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down gracefully")
    except Exception:
        logger.exception("Error shutting down scheduler")


import atexit

atexit.register(_shutdown_scheduler)

# ---------------------------
# CLI / run guard for local testing
# ---------------------------
if __name__ == "__main__":
    # Local dev run; Render and gunicorn will import this module and use `app`
    logger.info(f"Starting {APP_NAME} (dev mode)")
    try:
        port = int(os.environ.get("PORT", 8080))
    except Exception:
        port = 8080
    # Development server: not for production use — Gunicorn will be used in production
    app.run(host="0.0.0.0", port=port)
