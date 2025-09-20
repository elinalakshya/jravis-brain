"""
Team credential router for all 30 streams.

Rules:
1) Elina & Kael shared  -> use Elina's login
2) Kael & Riva shared   -> use Kael's login
3) Solo streams         -> use that person's login

Secrets supported:
- Elina: EMAIL or ELINA_EMAIL; PASSWORD or ELINA_PASS
- Kael:  KAEL_EMAIL, KAEL_PASS
- Riva:  RIVA_EMAIL, RIVA_PASS
"""

from __future__ import annotations
import os
from typing import Dict, List, Tuple

# --- Stream ownership map (Sl.No -> owners) -------------------------------
STREAM_OWNERS: Dict[int, List[str]] = {
    # Elina solo
    1: ["elina"],
    6: ["elina"],
    9: ["elina"],
    12: ["elina"],
    14: ["elina"],
    17: ["elina"],
    21: ["elina"],
    22: ["elina"],
    27: ["elina"],
    29: ["elina"],

    # Riva solo
    7: ["riva"],
    15: ["riva"],
    18: ["riva"],
    24: ["riva"],
    10: ["riva"],

    # Kael solo
    3: ["kael"],
    8: ["kael"],
    11: ["kael"],
    16: ["kael"],
    19: ["kael"],
    25: ["kael"],
    28: ["kael"],

    # Shared (Elina + Kael -> Elina)
    2: ["elina", "kael"],
    13: ["elina", "kael"],
    23: ["elina", "kael"],

    # Shared (Kael + Riva -> Kael)
    4: ["kael", "riva"],
    20: ["kael", "riva"],
    26: ["kael", "riva"],
    30: ["kael", "riva"],
}

# Names of Elina’s 10 streams for quick reference (optional)
ELINA_TEN = {
    1: "Elina Instagram Reels",
    6: "Etsy Digital Store",
    9: "Notion Template Store",
    12: "Udemy/Skillshare AI Courses",
    14: "Pinterest Affiliate Automation",
    17: "Stock Photos & AI Art",
    21: "AI Voiceover Gigs",
    22: "Podcast Repurposing Automation",
    27: "Virtual/Digital Events System",
    29: "Affiliate Product Bundles",
}


# --- Helper to decide the controlling owner for a stream ------------------
def owner_for_stream(stream_no: int) -> str:
    owners = STREAM_OWNERS.get(stream_no, [])
    if not owners:
        raise ValueError(f"No owners defined for stream {stream_no}")

    # Shared priority rules
    if "elina" in owners and "kael" in owners:
        return "elina"
    if "kael" in owners and "riva" in owners:
        return "kael"
    # Solo or any other single owner
    return owners[0]


# --- Fetch email/pass for a given logical owner ---------------------------
def _fetch_owner_creds(owner: str) -> Tuple[str, str]:
    if owner == "elina":
        # Elina supports either EMAIL/PASSWORD *or* ELINA_EMAIL/ELINA_PASS
        email = os.getenv("EMAIL") or os.getenv("ELINA_EMAIL")
        password = os.getenv("PASSWORD") or os.getenv("ELINA_PASS")
    elif owner == "kael":
        email = os.getenv("KAEL_EMAIL")
        password = os.getenv("KAEL_PASS")
    elif owner == "riva":
        email = os.getenv("RIVA_EMAIL")
        password = os.getenv("RIVA_PASS")
    else:
        raise RuntimeError(f"Unknown owner: {owner}")

    if not email or not password:
        raise RuntimeError(f"Missing login secrets for {owner.upper()}")
    return email, password


# --- Public API: get login for any stream ---------------------------------
def get_login(stream_no: int) -> Dict[str, str]:
    """
    Return the correct credentials for the stream:
    {
      'owner': 'elina|kael|riva',
      'email': '...',
      'password': '...'
    }
    """
    owner = owner_for_stream(stream_no)
    email, password = _fetch_owner_creds(owner)
    return {"owner": owner, "email": email, "password": password}


# Convenience: explicit getter for Elina’s 10 streams (optional nice-to-have)
def get_elina_login_for(stream_no: int) -> Dict[str, str]:
    if stream_no not in ELINA_TEN:
        raise ValueError(
            f"Stream {stream_no} is not one of Elina's 10 streams.")
    return get_login(stream_no)


from team_login import get_login

# 1) Instagram Reels (Sl.No 1) — Elina’s creds
creds = get_login(1)
ig_email = creds["email"]  # Elina’s email
ig_password = creds["password"]  # Elina’s password

# 6) Etsy Store — Elina’s creds
etsy_creds = get_login(6)
etsy_email, etsy_password = etsy_creds["email"], etsy_creds["password"]

# 3) Meshy (Kael solo) — Kael’s creds
meshy_creds = get_login(3)
kael_email, kael_password = meshy_creds["email"], meshy_creds["password"]

# 4) Cad Crowd (Kael + Riva) — Kael’s creds (shared rule)
cad_creds = get_login(4)
