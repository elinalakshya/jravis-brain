# validate_streams.py
import os, json, requests, sys, time


def load_config(path="streams_config.json"):
    with open(path, "r") as f:
        return json.load(f)


def validate_stream(stream):
    api_key = os.getenv(stream["api_key_env"])
    token = os.getenv(stream.get("test_token_env", ""))
    if not api_key:
        return False, "Missing API key env: " + stream["api_key_env"]
    # simple ping
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        r = requests.get(stream["ping_endpoint"], headers=headers, timeout=8)
        if r.status_code in (200, 204):
            return True, f"OK ({r.status_code})"
        return False, f"Bad status {r.status_code}: {r.text[:120]}"
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    cfg = load_config()
    results = {}
    for s in cfg["streams"]:
        ok, msg = validate_stream(s)
        results[s["id"]] = {"ok": ok, "msg": msg}
        print(s["id"], ok, msg)
    # exit code non-zero if any failed
    if any(not v["ok"] for v in results.values()):
        sys.exit(2)
    print("All streams validated.")
