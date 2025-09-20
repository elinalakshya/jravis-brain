# login_manager.py
# Centralized login + schedule manager for Phase 1–3 streams

import os
from datetime import datetime
from zoneinfo import ZoneInfo

# ==========================
# Timezone
# ==========================
IST = ZoneInfo("Asia/Kolkata")

# ==========================
# Fast-track switch (optional)
# If you set ACTIVATE_ALL_NOW=1 in Replit Secrets,
# all platforms are treated as active immediately.
# ==========================
FAST_TRACK_ALL = os.getenv("ACTIVATE_ALL_NOW", "0") == "1"


# ==========================
# Team login fetcher (from Replit Secrets)
# Requires:
#   ELINA_EMAIL, ELINA_PASS
#   KAEL_EMAIL,  KAEL_PASS
#   RIVA_EMAIL,  RIVA_PASS
# ==========================
def _key(member: str, suffix: str) -> str:
    return f"{member.upper()}_{suffix}"


def get_login(member: str):
    """
    Returns (email, password) for a given team member ('elina'|'kael'|'riva').
    Raises a clear error if secrets are missing.
    """
    member = member.lower().strip()
    email_key = _key(member, "EMAIL")
    pass_key = _key(member, "PASS")

    email = os.getenv(email_key)
    password = os.getenv(pass_key)

    missing = []
    if not email: missing.append(email_key)
    if not password: missing.append(pass_key)

    if missing:
        raise ValueError(
            f"❌ Missing login details for {member}. Add these Secrets: {', '.join(missing)}"
        )
    return email, password


# ==========================
# 30 Streams → owner + activation date
# platform_id : { member, activate_on (YYYY-MM-DD), title }
# ==========================
PLATFORM_SCHEDULE = {
    # 1–10
    "instagram_reels": {
        "member": "elina",
        "activate_on": "2025-08-21",
        "title": "Elina Instagram Reels"
    },
    "printify_pod": {
        "member": "kael",
        "activate_on": "2025-08-23",
        "title": "Printify POD Store"
    },
    "meshy_ai_store": {
        "member": "kael",
        "activate_on": "2025-08-25",
        "title": "Meshy AI Store"
    },
    "cad_crowd": {
        "member": "riva",
        "activate_on": "2025-08-27",
        "title": "Cad Crowd Auto Work"
    },
    "affiliate_marketing": {
        "member": "kael",
        "activate_on": "2025-08-29",
        "title": "Affiliate Marketing"
    },
    "lakshya_flights": {
        "member": "kael",
        "activate_on": "2025-09-01",
        "title": "Lakshya Global – Flights"
    },
    "airbnb": {
        "member": "elina",
        "activate_on": "2025-09-03",
        "title": "Lakshya Global – Airbnb"
    },
    "cabs_zoomcar_ola": {
        "member": "kael",
        "activate_on": "2025-09-05",
        "title": "Cabs/Zoomcar/Ola"
    },
    "digitutor_academic": {
        "member": "riva",
        "activate_on": "2025-09-07",
        "title": "DigiTutor Academic"
    },
    "digitutor_music": {
        "member": "riva",
        "activate_on": "2025-09-09",
        "title": "DigiTutor Music"
    },
    # 11–20
    "youtube_ai_channel": {
        "member": "kael",
        "activate_on": "2025-09-11",
        "title": "YouTube AI Channel"
    },
    "pinterest_affiliate": {
        "member": "kael",
        "activate_on": "2025-09-13",
        "title": "Pinterest Affiliate System"
    },
    "gumroad_ai_store": {
        "member": "kael",
        "activate_on": "2025-09-15",
        "title": "Gumroad AI Product Store"
    },
    "etsy_digital_store": {
        "member": "elina",
        "activate_on": "2025-09-17",
        "title": "Etsy Digital Store"
    },
    "canva_templates": {
        "member": "riva",
        "activate_on": "2025-09-19",
        "title": "Canva Template Store"
    },
    "notion_templates": {
        "member": "kael",
        "activate_on": "2025-09-21",
        "title": "Notion Template Sales"
    },
    "substack_newsletter": {
        "member": "riva",
        "activate_on": "2025-09-23",
        "title": "Substack AI Newsletter"
    },
    "online_courses": {
        "member": "kael",
        "activate_on": "2025-09-25",
        "title": "Online Course Sales"
    },
    "ai_storybook_generator": {
        "member": "kael",
        "activate_on": "2025-09-27",
        "title": "AI Storybook Generator"
    },
    "medium_blogging": {
        "member": "riva",
        "activate_on": "2025-09-29",
        "title": "Medium Blogging (Affiliate)"
    },
    # 21–30
    "fiverr_automation": {
        "member": "kael",
        "activate_on": "2025-10-01",
        "title": "Fiverr Gig Automation"
    },
    "plr_store": {
        "member": "kael",
        "activate_on": "2025-10-03",
        "title": "PLR Product Store"
    },
    "academic_case_study_engine": {
        "member": "riva",
        "activate_on": "2025-10-05",
        "title": "Academic Case Study Engine"
    },
    "ai_case_study_seller": {
        "member": "riva",
        "activate_on": "2025-10-07",
        "title": "AI Case Study Seller"
    },
    "etsy_printables": {
        "member": "elina",
        "activate_on": "2025-10-09",
        "title": "Etsy Printable Empire"
    },
    "surprisemyday_mini_gigs": {
        "member": "kael",
        "activate_on": "2025-10-11",
        "title": "SurpriseMyDay Mini Gigs"
    },
    "mini_event_agency": {
        "member": "kael",
        "activate_on": "2025-10-13",
        "title": "Mini Event Execution Agency"
    },
    "ai_pdf_report_generator": {
        "member": "kael",
        "activate_on": "2025-10-15",
        "title": "AI PDF Report Generator"
    },
    "case_study_marketplace": {
        "member": "riva",
        "activate_on": "2025-10-17",
        "title": "Case Study Marketplace"
    },
    "eco_friendly_global_store": {
        "member": "kael",
        "activate_on": "2025-10-19",
        "title": "Eco Friendly Global Store"
    },
}


# ==========================
# Activation check (with fast-track)
# ==========================
def _is_active(platform_id: str, now_ist: datetime | None = None) -> bool:
    """Return True if platform is active by date, or FAST_TRACK_ALL is enabled."""
    if FAST_TRACK_ALL:
        return True

    now_ist = now_ist or datetime.now(IST)
    info = PLATFORM_SCHEDULE.get(platform_id)
    if not info:
        return False
    try:
        start = datetime.fromisoformat(info["activate_on"]).replace(tzinfo=IST)
    except Exception:
        return False
    return now_ist >= start


# ==========================
# Public helpers
# ==========================
def get_platform_login(platform_id: str):
    """
    Returns (email, password) for the teammate bound to this platform_id,
    enforcing the activation date. Raises if unknown/not active/missing creds.
    """
    pid = platform_id.lower().strip()
    info = PLATFORM_SCHEDULE.get(pid)
    if not info:
        raise ValueError(f"❌ Unknown platform '{platform_id}'")

    if not _is_active(pid):
        raise ValueError(
            f"⏳ '{info['title']}' not active yet. Activates on {info['activate_on']}"
        )

    member = info["member"]
    return get_login(member)


def list_active_platforms(now_ist: datetime | None = None):
    """Returns list of (platform_id, title, member, activate_on) active as of now IST."""
    now_ist = now_ist or datetime.now(IST)
    out = []
    for pid, meta in PLATFORM_SCHEDULE.items():
        if _is_active(pid, now_ist):
            out.append(
                (pid, meta["title"], meta["member"], meta["activate_on"]))
    out.sort(key=lambda t: (t[3], t[0]))  # by activation date then id
    return out


def next_activation_after(now_ist: datetime | None = None):
    """Returns the next (platform_id, title, member, activate_on) that will become active, or None."""
    now_ist = now_ist or datetime.now(IST)
    upcoming = []
    for pid, meta in PLATFORM_SCHEDULE.items():
        try:
            start = datetime.fromisoformat(
                meta["activate_on"]).replace(tzinfo=IST)
        except Exception:
            continue
        if start > now_ist:
            upcoming.append(
                (pid, meta["title"], meta["member"], meta["activate_on"]))
    upcoming.sort(key=lambda t: t[3])
    return upcoming[0] if upcoming else None


def next_activation(now_ist: datetime | None = None):
    """Alias for compatibility with older test code."""
    return next_activation_after(now_ist)
