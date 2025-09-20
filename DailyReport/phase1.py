# DailyReport/phase1.py
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import json, os, time

from team_login import get_login  # central credential router

IST = ZoneInfo("Asia/Kolkata")


def _ts() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def _mask(s: str) -> str:
    if not s:
        return ""
    # mask email partly for logs (don't leak secrets)
    if "@" in s:
        name, dom = s.split("@", 1)
        return (name[:2] + "***@" + dom) if len(name) > 2 else "***@" + dom
    return "***"


# -------------------------
# Elina’s 10 streams
# -------------------------


def stream_1_instagram_reels():
    """
    Sl.No 1 — Elina Instagram Reels
    Requirement: use Elina's login (EMAIL/PASSWORD or ELINA_EMAIL/ELINA_PASS).
    If using Meta Graph API, the login is not used by API (it needs tokens),
    but we still record which account should own the action.
    """
    creds = get_login(1)
    email = creds[
        "email"]  # password available as creds["password"] if web login is needed
    # TODO: replace with real web login (Playwright/Selenium) OR Meta Graph API post
    # Example (API): adapters.instagram.post_reel(video_url, caption)
    details = f"ready (account={creds['owner']}, email={_mask(email)})"
    return {
        "task": "Elina Instagram Reels",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


def stream_6_etsy_digital_store():
    """
    Sl.No 6 — Etsy Digital Store (Elina)
    """
    from adapters.etsy import login_and_sync
    creds = get_login(6)
    res = login_and_sync(headless=True)
    status = "ok" if res.get("ok") else "skipped"
    details = res.get("why") or "done"
    if res.get("screenshot"): details += f" (shot: {res['screenshot']})"
    return {"task": "Etsy Digital Store", "status": status, "details": details, "account": creds["owner"], "at": _ts()}


def stream_9_notion_templates():
    """
    Sl.No 9 — Notion Template Store (Elina)
    """
    creds = get_login(9)
    email = creds["email"]
    # TODO: adapters.notion.push_template(email, creds["password"])
    details = f"ready (login with { _mask(email) })"
    return {
        "task": "Notion Template Store",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


def stream_12_udemy_skillshare():
    """
    Sl.No 12 — Udemy/Skillshare AI Courses (Elina)
    """
    creds = get_login(12)
    email = creds["email"]
    # TODO: adapters.udemy.publish_course(email, creds["password"]); adapters.skillshare.publish_course(...)
    details = f"ready (login with { _mask(email) })"
    return {
        "task": "Udemy/Skillshare AI Courses",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


def stream_14_pinterest_affiliate():
    """
    Sl.No 14 — Pinterest Affiliate Automation (Elina)
    """
    creds = get_login(14)
    email = creds["email"]
    # TODO: adapters.pinterest.auto_pin(email, creds["password"])
    details = f"ready (login with { _mask(email) })"
    return {
        "task": "Pinterest Affiliate Automation",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


def stream_17_stock_photos_ai_art():
    """
    Sl.No 17 — Stock Photos & AI Art (Elina)
    """
    creds = get_login(17)
    email = creds["email"]
    # TODO: adapters.stock.upload_assets(email, creds["password"])
    details = f"ready (login with { _mask(email) })"
    return {
        "task": "Stock Photos & AI Art",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


def stream_21_ai_voiceover_gigs():
    """
    Sl.No 21 — AI Voiceover Gigs (Elina)
    """
    creds = get_login(21)
    email = creds["email"]
    # TODO: adapters.voiceover.push_gig(email, creds["password"])
    details = f"ready (login with { _mask(email) })"
    return {
        "task": "AI Voiceover Gigs",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


def stream_22_podcast_repurposing():
    """
    Sl.No 22 — Podcast Repurposing Automation (Elina)
    """
    creds = get_login(22)
    email = creds["email"]
    # TODO: adapters.podcast.repurpose(email, creds["password"])
    details = f"ready (login with { _mask(email) })"
    return {
        "task": "Podcast Repurposing Automation",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


def stream_27_virtual_events():
    """
    Sl.No 27 — Virtual/Digital Events System (Elina)
    """
    creds = get_login(27)
    email = creds["email"]
    # TODO: adapters.events.publish_event(email, creds["password"])
    details = f"ready (login with { _mask(email) })"
    return {
        "task": "Virtual/Digital Events System",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


def stream_29_affiliate_bundles():
    """
    Sl.No 29 — Affiliate Product Bundles (Elina)
    """
    creds = get_login(29)
    email = creds["email"]
    # TODO: adapters.affiliates.publish_bundle(email, creds["password"])
    details = f"ready (login with { _mask(email) })"
    return {
        "task": "Affiliate Product Bundles",
        "status": "skipped",
        "details": details,
        "account": creds["owner"],
        "at": _ts()
    }


# -------------------------
# Runner
# -------------------------


def run_all():
    """
    Executes Elina’s 10 streams (each pulls Elina’s email+password automatically).
    Add adapters later to switch status from 'skipped' to real actions.
    """
    tasks = [
        stream_2_printify_pod,
        stream_1_instagram_reels,
        stream_6_etsy_digital_store,
        stream_9_notion_templates,
        stream_12_udemy_skillshare,
        stream_14_pinterest_affiliate,
        stream_17_stock_photos_ai_art,
        stream_21_ai_voiceover_gigs,
        stream_22_podcast_repurposing,
        stream_27_virtual_events,
        stream_29_affiliate_bundles,
    ]

    results = []
    for fn in tasks:
        try:
            results.append(fn())
        except Exception as e:
            results.append({
                "task": fn.__name__,
                "status": "error",
                "details": str(e),
                "account": "n/a",
                "at": _ts()
            })

    outdir = Path("DailyReport/out")
    outdir.mkdir(parents=True, exist_ok=True)
    fname = outdir / datetime.now(IST).strftime("phase1_%Y-%m-%d.json")
    fname.write_text(json.dumps({
        "date": _ts(),
        "results": results
    },
                                ensure_ascii=False,
                                indent=2),
                     encoding="utf-8")
    return results


def stream_2_printify_pod():
    """
    Sl.No 2 — Printify POD Store (real API).
    Requires PRINTIFY_API_KEY + PRINTIFY_SHOP_ID in env.
    Owner rule: Kael+Elina → Elina account recorded.
    """
    from adapters.printify import sync_check
    from team_login import get_login
    creds = get_login(2)
    res = sync_check()
    if res.get("ok"):
        status = "synced"; details = f"products={res.get('products')}"
    else:
        status = "skipped"; details = res.get("why") or res.get("resp") or f"status={res.get('status')}"
    return {"task":"Printify POD Store","status":status,"details":details,"account":creds["owner"],"at":_ts()}
