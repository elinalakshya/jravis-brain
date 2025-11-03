import os
import requests
from fastapi import FastAPI

app = FastAPI(title="JRAVIS Brain", version="1.0")

BACKEND_URL = os.getenv("BACKEND_URL", "https://jravis-backend.onrender.com")


@app.get("/")
def root():
    return {"status": "JRAVIS Brain active", "backend_linked": BACKEND_URL}


@app.get("/ping-backend")
def ping_backend():
    try:
        r = requests.get(f"{BACKEND_URL}/healthz", timeout=5)
        return {"backend_status": r.json()}
    except Exception as e:
        return {"backend_status": "unreachable", "error": str(e)}


@app.get("/healthz")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("jravis_brain:app", host="0.0.0.0", port=port)
