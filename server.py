# append to server.py (or create dashboard_api.py and import into server)
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
import re

# Phase -> streams mapping (use names exactly as you gave)
PHASE_MAP = {
    "phase1": [
        "Elina Instagram Reels", "Printify POD Store", "Meshy AI Store",
        "Cad Crowd Auto Work", "Fiverr AI Gig Automation",
        "YouTube Automation", "Stock Image/Video Sales",
        "AI Book Publishing (KDP)", "Shopify Digital Products",
        "Stationery Export (Lakshya Passive Stationery)"
    ],
    "phase2": [
        "Template/Theme Marketplace", "Course Resell Automation",
        "Printables Store (Etsy/Creative Market)",
        "Affiliate Marketing Automation", "AI SaaS Micro-Tools",
        "Newsletter + Ads Automation", "Subscription Box (Stationery/Digital)",
        "Gaming Assets Store", "Webflow Template Sales",
        "Skillshare Course Automation"
    ],
    "phase3": [
        "SaaS Reseller Bots", "Voiceover/AI Dubbing Automation",
        "Music/Beats Licensing", "Web Automation Scripts Marketplace",
        "AI Plugin/Extension Sales", "Educational Worksheets Store",
        "Digital/Virtual Events Automation", "AI Resume/CV Automation",
        "Crypto Microtask Automation (Legal Only)", "Global API Marketplace"
    ]
}


def aggregate_by_phase(streams):
    phases = {
        "phase1": {
            "total": 0,
            "count": 0,
            "streams": []
        },
        "phase2": {
            "total": 0,
            "count": 0,
            "streams": []
        },
        "phase3": {
            "total": 0,
            "count": 0,
            "streams": []
        }
    }
    name_map = {s["name"]: s for s in streams}
    for pkey, names in PHASE_MAP.items():
        total = 0
        for n in names:
            s = name_map.get(n)
            if s:
                total += float(s.get("amount", 0))
                phases[pkey]["streams"].append(s)
            else:
                # placeholder zero stream if missing
                phases[pkey]["streams"].append({
                    "id": n,
                    "name": n,
                    "amount": 0,
                    "currency": "INR",
                    "last_updated": None
                })
        phases[pkey]["total"] = round(total, 2)
        phases[pkey]["count"] = len(names)
    return phases


from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()  # ✅ This defines the FastAPI app instance


@app.get("/api/va_dashboard_data")
def va_dashboard_data():
    # use existing function get_streams() or call /api/earnings internally
    try:
        # if you have get_streams() available:
        streams = get_streams(
        )  # returns list of {id,name,amount,currency,last_updated}
    except Exception:
        # fallback: call earnings endpoint
        import requests, os
        backend = f"http://localhost:{os.getenv('PORT_BACKEND','8000')}"
        r = requests.get(f"{backend}/api/earnings")
        streams = r.json().get("streams", [])
    phases = aggregate_by_phase(streams)
    total_all = sum([phases[p]["total"] for p in phases])
    return {
        "total_all": total_all,
        "phases": phases,
        "last_sync": get_status().get("last_sync")
    }


# Simple dashboard chat endpoint — parses a few intents and responds from data
@app.post("/api/chat")
async def chat_endpoint(req: Request):
    data = await req.json()
    text = (data.get("text", "") or "").lower()
    # Basic intents
    if "phase 1" in text or "phase1" in text:
        phases = va_dashboard_data()["phases"]["phase1"]
        return JSONResponse({
            "reply":
            f"Phase 1 total is ₹{phases['total']}. Top streams: " + ", ".join([
                s['name']
                for s in sorted(phases["streams"],
                                key=lambda x: -float(x.get('amount', 0)))[:3]
            ])
        })
    if "show top" in text or "top" in text:
        all_streams = []
        for p in va_dashboard_data()["phases"].values():
            all_streams += p["streams"]
        tops = sorted(all_streams,
                      key=lambda x: -float(x.get("amount", 0)))[:5]
        return JSONResponse({
            "reply":
            "Top streams: " +
            ", ".join([f"{s['name']} (₹{s['amount']})" for s in tops])
        })
    if "total" in text or "income" in text:
        t = va_dashboard_data()["total_all"]
        return JSONResponse({
            "reply":
            f"Total combined live income across phases is approx ₹{t} per month."
        })
    # fallback
    return JSONResponse({
        "reply":
        "Boss, I understood: '" + data.get("text", "") +
        "'. Ask me about Phase 1/Phase 2/Phase 3, totals, or top streams."
    })


from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import subprocess
import os

app = FastAPI()

# Existing routes above this...


@app.get("/api/send_daily_report")
async def send_daily_report(request: Request):
    """Trigger daily report email with lock code verification"""
    params = dict(request.query_params)
    code = params.get("code", "")

    # ✅ Security check — must match your lock code
    if code != "2040":
        return JSONResponse({
            "status": "error",
            "message": "Unauthorized"
        },
                            status_code=401)

    try:
        # Run the email sender script
        subprocess.run(["python", "auto_dashboard_daily.py"],
                       cwd=os.getcwd(),
                       check=True)
        return JSONResponse({
            "status": "success",
            "message": "Daily report sent successfully"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        },
                            status_code=500)
