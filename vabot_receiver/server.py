from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os, datetime
from tinydb import TinyDB

app = FastAPI(title="VA Bot Receiver")

DB_PATH = os.getenv("INCOME_DB_PATH", "/data/income_db.json")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = TinyDB(DB_PATH)


@app.post("/api/printify/order")
async def receive_order(request: Request):
    data = await request.json()
    now = datetime.datetime.utcnow().isoformat()
    db.insert({"timestamp": now, "source": "Printify", "data": data})
    print(f"[Receiver] ✅ Order received at {now}")
    return JSONResponse({"status": "success", "received": now})


@app.get("/healthz")
async def health_check():
    return {"status": "VA Bot Receiver Online"}
