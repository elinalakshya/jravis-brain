import os, requests
MESHY_API_URL = os.getenv("MESHY_API_URL")  # e.g. https://api.meshy.ai/...
MESHY_API_KEY = os.getenv("MESHY_API_KEY")

def push_asset(title: str, file_url: str):
    if not MESHY_API_URL or not MESHY_API_KEY:
        return {"ok": False, "why": "missing MESHY_API_URL/MESHY_API_KEY"}
    r = requests.post(f"{MESHY_API_URL}/assets",
                      headers={"Authorization": f"Bearer {MESHY_API_KEY}"},
                      json={"title": title, "file_url": file_url}, timeout=60)
    if r.status_code not in (200,201):
        return {"ok": False, "status": r.status_code, "resp": r.text}
    return {"ok": True, "id": r.json().get("id")}
