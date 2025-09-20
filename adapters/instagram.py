import os, requests, time
IG_USER_ID = os.getenv("IG_USER_ID")           # e.g. 1784... (Instagram Business User ID)
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")  # Long-lived access token

API_BASE = "https://graph.facebook.com/v19.0"

def post_reel(video_url: str, caption: str):
    if not IG_USER_ID or not FB_ACCESS_TOKEN:
        return {"ok": False, "why": "missing IG_USER_ID/FB_ACCESS_TOKEN"}
    # 1) Create media container
    r = requests.post(f"{API_BASE}/{IG_USER_ID}/media",
        data={"media_type":"REELS","video_url":video_url,"caption":caption},
        params={"access_token": FB_ACCESS_TOKEN}, timeout=60)
    if r.status_code != 200:
        return {"ok": False, "step":"media","status":r.status_code,"resp":r.text}
    container_id = r.json().get("id")
    time.sleep(2)
    # 2) Publish container
    r2 = requests.post(f"{API_BASE}/{container_id}/publish",
        params={"access_token": FB_ACCESS_TOKEN}, timeout=60)
    if r2.status_code != 200:
        return {"ok": False, "step":"publish","status":r2.status_code,"resp":r2.text}
    return {"ok": True, "id": r2.json().get("id")}
