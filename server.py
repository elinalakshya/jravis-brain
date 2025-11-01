# ===============================================================
# JRAVIS Backend Server  (Phase 2 — Stable Build v2.1)
# ===============================================================
import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from connectors.income_bridge import run_daily as run_income_bridge

# ---------------------------------------------------------------
# Logging
# ---------------------------------------------------------------
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler()])
LOG = logging.getLogger("jravis-server")

# ---------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------
app = FastAPI(title="JRAVIS Backend",
              version="2.1",
              description="JRAVIS Passive-Income Backend — Mission 2040")


# Health-check endpoint (used by Render)
@app.get("/healthz")
async def healthz():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------
def orchestrate_report(report_type="daily"):
    """Main orchestrator for daily / weekly report + income bridge."""
    LOG.info("=== JRAVIS Report Orchestrator START (%s) ===", report_type)
    date_tag = datetime.utcnow().strftime("%d-%m-%Y")

    # 1️⃣ Run Income Bridge
    try:
        LOG.info("[IncomeBridge] Starting…")
        matched = run_income_bridge()
        LOG.info("[IncomeBridge] Matched %d transactions ✅", matched)
    except Exception as e:
        LOG.error("[IncomeBridge] Failed: %s", e)

    # 2️⃣ Placeholder for PDF + email logic (already handled by cron/emailer)
    report_path = f"/app/data/reports/{date_tag}-{report_type}.pdf"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(f"JRAVIS {report_type.capitalize()} Report — {date_tag}\n")
        f.write("Generated successfully ✅\n")

    LOG.info("=== JRAVIS Report Orchestrator END (%s) ===", report_type)
    return {
        "detail": f"{report_type.capitalize()} report orchestrator started",
        "date": date_tag
    }


# ---------------------------------------------------------------
# API Endpoints (used by Render Cron)
# ---------------------------------------------------------------
@app.get("/api/send_daily_report")
async def send_daily_report(code: str):
    """Trigger daily report via secure code."""
    if code != "2040":
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    res = orchestrate_report("daily")
    return JSONResponse(res)


@app.get("/api/send_weekly_report")
async def send_weekly_report(code: str):
    """Trigger weekly report via secure code."""
    if code != "2040":
        return JSONResponse({"error": "Unauthorized"}, status_code=403)
    res = orchestrate_report("weekly")
    return JSONResponse(res)


# ---------------------------------------------------------------
# Optional manual trigger (for local testing)
# ---------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    LOG.info("Starting JRAVIS Backend — Mission 2040")
    uvicorn.run("server:app",
                host="0.0.0.0",
                port=int(os.getenv("PORT", 8000)))
