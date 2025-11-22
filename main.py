#!/usr/bin/env python3
"""
JRAVIS Backend (MAIN) — Clean Architecture B
--------------------------------------------
This file is ONLY the API + Dashboard + Command Interface.

All automation (scheduler, gmail, daily reports, phase cycles)
is inside worker.py, running as a separate background process.

This keeps the server FAST, CLEAN, and NON-BLOCKING.
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Phase-1 Queue Engine
from p1_queue_engine import activate_phase1_fullpower_cycle

# ======================================================================
# 1️⃣ FLASK APP (Dashboard + Commands)
# ======================================================================
app = Flask(__name__)


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "status": "ok",
        "system": "JRAVIS Backend",
        "message": "🚀 JRAVIS Backend Active (Main Server)"
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "system": "JRAVIS Backend",
        "time": datetime.utcnow().isoformat()
    }), 200


@app.route("/command", methods=["POST"])
def command():
    """Manual command endpoint for Phase-1 cycle."""
    data = request.get_json(force=True)
    cmd = data.get("cmd", "").lower().strip()

    if cmd in [
            "begin_phase_1", "start_phase_1", "phase1_start",
            "begin_phase_1_cycle", "jravis begin phase 1 cycle"
    ]:
        result = activate_phase1_fullpower_cycle()
        return jsonify(result), 200

    return jsonify({"status": "unknown_command"}), 400


# ======================================================================
# 2️⃣ SIMPLE DASHBOARD (FastAPI)
# ======================================================================
api = FastAPI(title="JRAVIS Dashboard API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/summary")
def get_dashboard_summary():
    return {
        "system": "JRAVIS Dashboard",
        "today": datetime.utcnow().isoformat(),
        "status": "running",
        "note": "Dashboard API responding normally."
    }


# ======================================================================
# 3️⃣ MOUNT FASTAPI INSIDE FLASK
# ======================================================================
application = DispatcherMiddleware(app, {
    "/api": api,
})

# ======================================================================
# 4️⃣ STARTUP SERVER
# ======================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    port = int(os.getenv("PORT", 8080))
    logging.info(f"🚀 JRAVIS Main Server starting on port {port}")

    from werkzeug.serving import run_simple
    run_simple("0.0.0.0",
               port,
               application,
               use_reloader=False,
               use_debugger=False)
