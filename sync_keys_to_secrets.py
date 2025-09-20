cat > sync_keys_to_secrets.py << 'PY'
#!/usr/bin/env python3
"""
sync_keys_to_secrets.py

Watches generated_api_keys.json and prints a ready-to-paste secrets file or attempts to set Replit secrets via API
(if REPLIT_TOKEN/REPLIT_OWNER/REPLIT_SLUG are provided).
"""
import os, time, json, sys, hashlib
from pathlib import Path

WATCH_FILE = Path("generated_api_keys.json")
LAST_HASH = None
POLL_INTERVAL = int(os.getenv("SYNC_POLL_INTERVAL", "6"))


def file_hash(path: Path):
    if not path.exists():
        return None
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"[sync] Failed to read JSON: {e}")
        return {}


def print_and_save_secrets(to_set: dict):
    pairs = {}
    for platform, info in to_set.items():
        if isinstance(info, dict):
            for k, v in info.items():
                name = f"{platform.upper()}_{k.upper()}"
                pairs[name] = str(v)
        else:
            name = f"{platform.upper()}_API_KEY"
            pairs[name] = str(info)
    if not pairs:
        print("[sync] No keys to save.")
        return
    out_lines = []
    out_lines.append("# Paste these into Replit Secrets (key = value):\n")
    for k, v in pairs.items():
        out_lines.append(f"{k} = {v}\n")
    out_text = "".join(out_lines)
    Path("secrets_to_add.txt").write_text(out_text)
    print(out_text)
    print("[sync] Written secrets_to_add.txt with keys ready for Replit UI.")


def attempt_replit_api_set(pairs: dict):
    token = os.getenv("REPLIT_TOKEN")
    owner = os.getenv("REPLIT_OWNER")
    slug = os.getenv("REPLIT_SLUG")
    if not token or not owner or not slug:
        return False, "missing REPLIT_TOKEN/REPLIT_OWNER/REPLIT_SLUG"
    try:
        import requests
    except Exception as e:
        return False, f"requests not installed: {e}"
    base = f"https://api.replit.com/v0"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    success = []
    failures = {}
    for k, v in pairs.items():
        payload = {"key": k, "value": v}
        url = f"{base}/repls/{owner}/{slug}/secrets"
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code in (200, 201):
                success.append(k)
            else:
                failures[k] = f"{r.status_code}:{r.text}"
        except Exception as e:
            failures[k] = str(e)
    return (len(success) > 0), {"success": success, "failures": failures}


def main_loop():
    global LAST_HASH
    LAST_HASH = file_hash(WATCH_FILE)
    print("[sync] starting watch on generated_api_keys.json")
    while True:
        cur = file_hash(WATCH_FILE)
        if cur and cur != LAST_HASH:
            LAST_HASH = cur
            data = load_json(WATCH_FILE)
            to_set = {}
            gen = data.get("generated", {})
            for platform, info in gen.items():
                to_set[platform] = info
            if not to_set:
                print("[sync] No generated keys found in JSON.")
            else:
                pairs = {}
                for platform, info in to_set.items():
                    if isinstance(info, dict):
                        for k, v in info.items():
                            name = f"{platform.upper()}_{k.upper()}"
                            pairs[name] = v
                    else:
                        pairs[f"{platform.upper()}_API_KEY"] = info
                ok, result = attempt_replit_api_set(pairs)
                if ok:
                    print("[sync] Replit API set results:", result)
                else:
                    print("[sync] Replit API method unavailable or failed:",
                          result)
                    print_and_save_secrets(pairs)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("sync_keys_to_secrets.py stopped by user.")
        sys.exit(0)
PY
