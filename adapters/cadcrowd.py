import os, requests
# If CADCROWD_API_URL + CADCROWD_TOKEN present, poll; otherwise return skipped
CADCROWD_API_URL = os.getenv("CADCROWD_API_URL")
CADCROWD_TOKEN = os.getenv("CADCROWD_TOKEN")

def fetch_one():
    if not CADCROWD_API_URL or not CADCROWD_TOKEN:
        return {"ok": False, "why": "missing CADCROWD_API_URL/CADCROWD_TOKEN"}
    r = requests.get(f"{CADCROWD_API_URL}/jobs?limit=1",
                     headers={"Authorization": f"Bearer {CADCROWD_TOKEN}"}, timeout=60)
    if r.status_code != 200:
        return {"ok": False, "status": r.status_code, "resp": r.text}
    data = r.json()
    job = (data or [{}])[0]
    return {"ok": True, "job": job.get("title","(unknown)")}
