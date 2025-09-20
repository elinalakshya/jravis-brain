# jarvis_brain.py
import os, uuid, json, time, requests
from flask import Flask, request, jsonify
import openai
from memory_store import save_task, save_report, save_mission, search_memory

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
VA_BOT_WEBHOOK = os.getenv("VA_BOT_WEBHOOK")  # your executor endpoint

PLANNER_SYSTEM = """You are Jarvis Brain. Convert the user_command into a strict JSON Plan using the Plan Schema.
Plan Schema keys: request_id, user_command, intent, priority, plan[], post_actions, mission_check.
Each plan[] item must include: step_id, action, target, params, expected_result, retry_policy.
Check long-term memory for Mission 2040 facts and set mission_check.aligns_with_2040 true|false and explain in notes.
Return ONLY the JSON object."""

app = Flask(__name__)


def generate_plan(user_command, mission_context=""):
    prompt = f"Mission context: {mission_context}\nUser command: \"{user_command}\""
    resp = openai.ChatCompletion.create(
        model="gpt-5",  # replace as needed
        messages=[{
            "role": "system",
            "content": PLANNER_SYSTEM
        }, {
            "role": "user",
            "content": prompt
        }],
        max_tokens=900,
        temperature=0.0)
    text = resp['choices'][0]['message']['content'].strip()
    try:
        plan = json.loads(text)
    except Exception:
        import re
        m = re.search(r'\{.*\}', text, flags=re.S)
        plan = json.loads(m.group(0)) if m else {
            "error": "parse_failed",
            "raw": text
        }
    return plan


def submit_plan(plan: dict):
    if not VA_BOT_WEBHOOK:
        return False, "VA_BOT_WEBHOOK not set"
    r = requests.post(VA_BOT_WEBHOOK, json=plan, timeout=30)
    return (r.status_code in (200, 202)), r.text


@app.route("/command", methods=["POST"])
def command():
    data = request.json or {}
    cmd = data.get("command") or data.get("text")
    mission_ctx = data.get("mission_context", "")
    if not cmd:
        return jsonify({"error": "no command"}), 400
    plan = generate_plan(cmd, mission_ctx)
    # record permanently
    task_id = str(uuid.uuid4())
    save_task(task_id, plan.get("request_id"), cmd, plan, status="submitted")
    ok, resp = submit_plan(plan)
    return jsonify({
        "submitted": ok,
        "vabot_resp": resp,
        "plan": plan
    }), (202 if ok else 500)


@app.route("/step_status", methods=["POST"])
def step_status():
    data = request.json or {}
    # save step report as a permanent record (we'll store under reports or tasks updates)
    request_id = data.get("request_id")
    step_id = data.get("step_id")
    status = data.get("status")
    output = data.get("output")
    # append to a permanent log (as a report)
    rid = f"steplog_{request_id}_{step_id}_{int(time.time())}"
    save_report(rid, time.ctime(), "step_status", "", summary=json.dumps(data))
    # update task status (simple)
    # (In full system, update tasks table row with newest status)
    return jsonify({"ok": True})


@app.route("/memory_search", methods=["GET"])
def mem_search():
    q = request.args.get("q", "")
    if not q:
        return jsonify([]), 200
    res = search_memory(q, n_results=5)
    return jsonify(res)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
