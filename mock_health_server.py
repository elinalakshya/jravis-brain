from flask import Flask, jsonify
from datetime import datetime
import random

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def mock_health():
    # Random health states for testing
    healthy = random.choice([True, True, True, False])
    error_count = random.randint(0, 3) if not healthy else 0
    now = datetime.utcnow().isoformat() + "Z"

    return jsonify({
        "healthy": healthy,
        "error_count": error_count,
        "last_cycle": now,
        "last_success": now if healthy else None
    })


if __name__ == '__main__':
    print("🩺 Mock Health Server running on http://localhost:8080/health")
    app.run(host='0.0.0.0', port=8080)
