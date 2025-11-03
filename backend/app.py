from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="JRAVIS Backend", version="1.0")

# Allow CORS for all origins (adjust later if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Query


@app.get("/api/send_daily_report")
def send_daily_report(code: str = Query(...)):
    """Triggered by JRAVIS Daily Report Worker"""
    if code != "2040":
        return {"detail": "Unauthorized"}

    # === Your daily report generation logic goes here ===
    print("[Backend] 🗓️ Generating daily report...")

    # Example: return success message
    return {"status": "Daily report sent successfully"}


@app.get("/")
def root():
    return {"status": "JRAVIS Backend running", "version": "1.0"}


@app.get("/healthz")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
