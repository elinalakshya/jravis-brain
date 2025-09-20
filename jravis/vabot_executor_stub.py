# vabot_executor_stub.py
from flask import Flask, request, jsonify
import time, requests, os

app = Flask(__name__)

# Brain callback URL (where to report step status)
BRAIN_CALLBACK = os.getenv("BRAIN_CALLBACK",
                           "http://localhost:5001/step_status")


def fake_execute_step(step: dict):
    """
    Simulates executing a step.
    In real VA Bot, replace this with actual logic (API call, file operation, etc.).
    """
    print(f"Executing step: {step}")
    time.sleep(1)  # simulate work

    # Example: simulate failure if action = "fail_test"
    if step.get("action") == "fail_test":
        return False, "Simulated failure"

    return True, f"Executed {step.get('action')} successfully"


@app.route("/execute_plan", methods=["POST"])
def execute_plan():
    plan = request.json or {}
    request_id = plan.get("request_id", "unknown")
    steps = plan.get("plan", [])

    for step in steps:
        step_id = step.get("step_id")
        success, message = fake_execute_step(step)

        # Report status back to brain
        payload = {
            "request_id": request_id,
            "step_id": step_id,
            "status": "success" if success else "fail",
            "output": message
        }
        try:
            requests.post(BRAIN_CALLBACK, json=payload, timeout=10)
        except Exception as e:
            print(f"Failed to callback brain: {e}")

        if not success:
            return jsonify({"error": "Step failed", "step": step}), 500

    return jsonify({"ok": True}), 202


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
