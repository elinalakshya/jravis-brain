import os

# Mapping of stream number → owner(s)
STREAM_OWNERS = {
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

    # Shared (Elina + Kael → Elina login)
    2: ["elina", "kael"],
    13: ["elina", "kael"],
    23: ["elina", "kael"],

    # Shared (Kael + Riva → Kael login)
    4: ["kael", "riva"],
    20: ["kael", "riva"],
    26: ["kael", "riva"],
    30: ["kael", "riva"],
}


def get_login(stream_no: int):
    owners = STREAM_OWNERS.get(stream_no, [])
    if not owners:
        raise ValueError(f"No owners defined for stream {stream_no}")

    # Shared rules
    if "elina" in owners and "kael" in owners:
        owner = "elina"  # Elina wins
    elif "kael" in owners and "riva" in owners:
        owner = "kael"  # Kael wins
    else:
        owner = owners[0]

    # Map owner → secret keys
    if owner == "elina":
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

    return {"owner": owner, "email": email, "password": password}
