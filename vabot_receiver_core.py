import os
import logging
from flask import Flask, request, jsonify

# -----------------------------
# Configuration
# -----------------------------
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Shared secret key with Render bridge
SECRET = os.getenv("VA_BOT_SECRET", "LakshyaSecureKey@2025")

# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "VA Bot Receiver is running ✅"}), 200


@app.route("/api/printify/order", methods=["POST"])
def receive_order():
    """Endpoint that receives order JSON data from JRAVIS Bridge"""
    header_secret = request.headers.get("X-VA-Secret")

    if header_secret != SECRET:
        logging.warning("Unauthorized request: invalid secret header.")
        return jsonify({"error": "unauthorized"}), 401

    try:
        payload = request.get_json(force=True)
    except Exception as e:
        logging.error("Invalid JSON payload: %s", e)
        return jsonify({"error": "invalid JSON"}), 400

    logging.info("✅ Received orders: %s", payload)
    return jsonify({"status": "ok"}), 200


# -----------------------------
# App Runner
# -----------------------------
if __name__ == "__main__":
    # Replit automatically provides PORT
    port = int(os.getenv("PORT", "10000"))
    logging.info(f"Starting VA Bot Receiver on port {port}")
    app.run(host="0.0.0.0", port=port)
