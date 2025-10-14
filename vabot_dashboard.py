# =====================================================
# ✅ VA Bot Dashboard — Mission 2040 Interface
# =====================================================

from flask import Flask, jsonify
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "VA Bot Dashboard online ✅",
        "timestamp": datetime.datetime.now().isoformat(),
        "mission": "Lakshya Mission 2040 Phase 1"
    })

@app.route('/health')
def health():
    return jsonify({
        "ok": True,
        "service": "vabot-dashboard",
        "uptime": "running smoothly"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
