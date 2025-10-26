import os, logging
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET = os.getenv("VA_BOT_SECRET")


@app.route("/api/printify/order", methods=["POST"])
def receive_order():
    if request.headers.get("X-VA-Secret") != SECRET:
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json(force=True)
    logging.info("Received orders: %s", payload)
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
