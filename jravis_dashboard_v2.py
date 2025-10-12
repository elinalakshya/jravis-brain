#!/usr/bin/env python3
"""
JRAVIS Dashboard v2 — Single-file
- Single page: left = mission panels (click phases), right = stats + chat
- Lock-protected chat (LOCK_CODE_VALUE env var; fallback used if missing)
- Endpoints: / (login -> dashboard), /main (dashboard), /ask (chat), /api/streams?phase=..., /health
Save as: jravis_dashboard_v2.py
Start: python jravis_dashboard_v2.py
ENV: LOCK_CODE_VALUE (recommended), PORT (defaults 10000)
"""

from flask import Flask, request, session, redirect, url_for, render_template_string, jsonify
import os, datetime, random, math

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "jravis_secret_key")

# --- Lock code (do not embed your real lock in code; set LOCK_CODE_VALUE in Render env)
PASSCODE = os.environ.get("LOCK_CODE_VALUE")
if not PASSCODE or PASSCODE.strip() == "":
    # fallback (only used if env var missing) - do not show your real lock here
    PASSCODE = "MY_OG_FALLBACK"

# --- Simulated mission data (replace with live JRAVIS calls later) ---
MISSION_TARGET = 4_000_000  # sample target
CURRENT_EARNINGS_INR = 624000
CURRENT_EARNINGS_USD = 8250
PROGRESS_PERCENT = min(100, int((CURRENT_EARNINGS_INR / MISSION_TARGET) * 100))

PHASES = {
    "Phase 1": {
        "status":
        "Active",
        "target":
        "₹4 Cr loan clearance",
        "streams": [
            "ElinaInstagramReels", "Printify", "MeshyAI", "CadCrowd", "Fiverr",
            "YouTube", "StockImageVideo", "AIBookPublishingKDP",
            "ShopifyDigitalProducts", "StationeryExport"
        ],
    },
    "Phase 2": {
        "status": "Scale up",
        "target": "Grow revenue & automation",
        "streams": ["Phase2_StreamA", "Phase2_StreamB", "Phase2_StreamC"]
    },
    "Phase 3": {
        "status": "Global scaling",
        "target": "Robo Mode global",
        "streams": ["Phase3_StreamA", "Phase3_StreamB"]
    }
}

# runtime status store (simulate live)
STATUSES = {}
_choices = ["Running ✅", "Idle ⏳", "Error ⚠️", "Syncing 🔁"]
for p in PHASES:
    for s in PHASES[p]["streams"]:
        STATUSES[s] = random.choice(_choices)

# in-memory chat history
CHAT_HISTORY = [{
    "who": "jravis",
    "msg": "JRAVIS online — ask about streams, earnings, or run commands.",
    "time": datetime.datetime.now().isoformat()
}]

# ---------- Templates ----------
LOGIN_HTML = """
<!doctype html><html><head><meta charset="utf-8"><title>JRAVIS Login</title>
<style>
body{background:#0b1220;color:#e6eef6;font-family:Inter,system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.form{background:#0f1724;padding:28px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.6);width:360px;text-align:center}
input{width:100%;padding:12px;border-radius:8px;border:none;margin-top:12px;background:#071021;color:#fff}
button{margin-top:12px;padding:10px 16px;border-radius:8px;border:none;background:#06b6d4;color:#042;cursor:pointer;font-weight:700}
h2{margin:0}
.msg{color:#ff9b9b;margin-top:10px}
.small{color:#9aa6b2;font-size:13px;margin-top:8px}
</style></head><body>
<form method="post" class="form">
  <h2>JRAVIS Access</h2>
  <p class="small">Enter your lock code</p>
  <input name="code" type="password" placeholder="lock code" required />
  <button>Unlock</button>
  {% if error %}<div class="msg">{{ error }}</div>{% endif %}
  <div class="small">Locked access — passcode is stored securely.</div>
</form>
</body></html>
"""

MAIN_HTML = """
<!doctype html>
<html><head><meta charset="utf-8"><title>JRAVIS Mission 2040</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#071023;--card:#0f1724;--muted:#9aa6b2;--accent:#10b981}
body{margin:0;font-family:Inter,system-ui;background:var(--bg);color:#e6eef6}
.header{padding:20px 28px;display:flex;justify-content:space-between;align-items:center}
.title{font-size:20px;font-weight:700}
.container{display:flex;gap:18px;padding:0 28px 28px}
.left{flex:1.6;padding-top:8px}
.right{width:420px}
.card{background:var(--card);border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 8px 30px rgba(0,0,0,.6)}
.progress{background:#071827;height:12px;border-radius:999px;overflow:hidden}
.progress > i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),#34d399)}
.row{display:flex;justify-content:space-between;align-items:center}
.small{color:var(--muted);font-size:13px}
.phase-table{width:100%;border-collapse:collapse;margin-top:8px}
.phase-row{cursor:pointer}
.stream-list{margin-top:10px}
.stream{display:flex;justify-content:space-between;padding:10px;border-radius:8px;background:#071827;margin-bottom:8px}
.chat-wrap{height:62vh;display:flex;flex-direction:column}
.chat-box{flex:1;padding:12px;overflow:auto;border-radius:8px;background:#081425}
.input{display:flex;padding:8px;margin-top:8px}
.input input{flex:1;padding:10px;border-radius:8px;border:none;background:#071827;color:#fff}
.input button{margin-left:8px;padding:10px 12px;border-radius:8px;border:none;background:#3b82f6;color:#fff}
.msg{margin-bottom:8px;padding:8px;border-radius:8px}
.msg.user{text-align:right;color:#c7d2fe}
.msg.jravis{text-align:left;color:#bbf7d0}
.stat-big{font-size:28px;font-weight:700}
.target{font-size:14px;color:var(--muted)}
</style>
</head><body>
<div class="header">
  <div>
    <div class="title">Jarvis Brain — Mission 2040 Dashboard</div>
    <div class="small">Control center · Live</div>
  </div>
  <div style="text-align:right">
    <div class="small">Earnings</div>
    <div class="stat-big">₹ {{ earn_inr }}<br>$ {{ earn_usd }}</div>
  </div>
</div>

<div class="container">
  <div class="left">
    <div class="card">
      <div class="row"><div><strong>Mission 2040 Progress</strong><div class="small">Distance to target & timeline</div></div><div><strong>{{ progress_percent }}%</strong></div></div>
      <div style="height:12px;margin-top:10px" class="progress"><i style="width:{{ progress_percent }}%"></i></div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>Phase Status</strong><div class="small">Click a phase to expand streams</div></div>
      </div>
      <table class="phase-table">
        {% for pname, pdata in phases.items() %}
        <tr class="phase-row" onclick="togglePhase('{{pname}}')">
          <td style="padding:12px 8px;width:180px"><strong>{{pname}}</strong><div class="small">{{pdata.status}}</div></td>
          <td style="padding:12px 8px">{{pdata.target}}</td>
        </tr>
        <tr id="phase-{{pname}}" style="display:none"><td colspan="2">
          <div class="stream-list" id="list-{{pname}}"></div>
        </td></tr>
        {% endfor %}
      </table>
    </div>

    <div class="card">
      <div class="row"><div><strong>Task Timeline</strong><div class="small">Completed · Today · Tomorrow</div></div><div class="small">—</div></div>
      <div style="height:40px"></div>
    </div>

  </div>

  <div class="right">
    <div class="card">
      <div style="display:flex;justify-content:space-between"><div><strong>Today</strong><div class="small">Tasks & quick actions</div></div><div class="small">Status</div></div>
      <div style="margin-top:12px">✔ Completed</div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between"><div><strong>Property & Debt Tracker</strong></div><div class="small">Timeline</div></div>
      <div style="height:36px"></div>
    </div>

    <div class="card chat-wrap">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div><strong>JRAVIS Chat</strong><div class="small">Ask JRAVIS about streams, earnings, or commands</div></div>
        <div class="small">Live</div>
      </div>
      <div id="chat" class="chat-box"></div>
      <div class="input">
        <input id="msg" placeholder="Type to JRAVIS..." onkeydown="if(event.key==='Enter')sendMsg()">
        <button onclick="sendMsg()">Send</button>
      </div>
    </div>

  </div>
</div>

<script>
// client-side: load stream lists dynamically and chat handling
const PHASES = {{ phases_json|tojson }};
function togglePhase(name){
  const row = document.getElementById('phase-'+name);
  if(row.style.display==='none'){ row.style.display='table-row'; loadStreams(name); }
  else row.style.display='none';
}

async function loadStreams(phase){
  const container = document.getElementById('list-'+phase);
  container.innerHTML = 'Loading…';
  const res = await fetch('/api/streams?phase='+encodeURIComponent(phase));
  const js = await res.json();
  container.innerHTML = '';
  js.streams.forEach(s => {
    const el = document.createElement('div');
    el.className='stream';
    el.innerHTML = `<div>${s.name}</div><div>${s.status}</div>`;
    container.appendChild(el);
  });
}

function appendMsg(who, text){
  const chat = document.getElementById('chat');
  const el = document.createElement('div');
  el.className = 'msg ' + (who==='user' ? 'user' : 'jravis');
  el.textContent = (who==='user' ? '🧑‍💼 ' : '🤖 ') + text;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
}

async function sendMsg(){
  const box = document.getElementById('msg');
  const txt = box.value.trim();
  if(!txt) return;
  appendMsg('user', txt);
  box.value = '';
  try{
    const r = await fetch('/ask', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message:txt})});
    const j = await r.json();
    appendMsg('jravis', j.response);
  }catch(e){
    appendMsg('jravis', 'Error contacting JRAVIS: '+String(e));
  }
}

// initial chat history
(async function(){
  const r = await fetch('/chat/history');
  const h = await r.json();
  h.forEach(item => appendMsg(item.who, item.msg));
})();
</script>
</body></html>
"""


# ---------- Helper (JRAVIS logic) ----------
def jravis_answer(msg):
    t = msg.lower().strip()
    # check for mentions of streams
    found = [s for s in STATUSES if s.lower() in t]
    if found:
        parts = []
        for s in found:
            st = STATUSES.get(s, "Unknown")
            if "error" in st.lower():
                parts.append(f"{s}: {st} — Suggestion: check API key & logs.")
            else:
                parts.append(f"{s}: {st}")
        return " | ".join(parts)
    if any(w in t
           for w in ("earn", "income", "revenue", "progress", "target")):
        p = min(100, int((CURRENT_EARNINGS_INR / MISSION_TARGET) * 100))
        return f"Earnings: ₹{CURRENT_EARNINGS_INR} ({p}%), USD ${CURRENT_EARNINGS_USD}."
    if any(
            t.startswith(cmd)
            for cmd in ("run ", "start ", "stop ", "restart ", "deploy ")):
        return f"Command queued: {msg}"
    if t in ("hi", "hello", "hey", "how are you"):
        return "JRAVIS here — systems nominal and running 24×7. How can I assist, Boss?"
    # default
    running = sum(1 for v in STATUSES.values() if "running" in v.lower())
    errors = sum(1 for v in STATUSES.values() if "error" in v.lower())
    idle = sum(1 for v in STATUSES.values() if "idle" in v.lower())
    return f"Streams: {running} running, {idle} idle, {errors} errors. Ask 'why <stream>' or 'earnings'."


# ---------- Routes ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        expected = os.environ.get("LOCK_CODE_VALUE", PASSCODE)
        if code == expected:
            session["auth"] = True
            return redirect(url_for("main"))
        return render_template_string(LOGIN_HTML, error="Incorrect lock code.")
    return render_template_string(LOGIN_HTML)


@app.route("/main")
def main():
    if not session.get("auth"):
        return redirect(url_for("login"))
    # pass plain numbers/strings only (avoid Jinja formatting issues)
    return render_template_string(MAIN_HTML,
                                  earn_inr=str(CURRENT_EARNINGS_INR),
                                  earn_usd=str(CURRENT_EARNINGS_USD),
                                  progress_percent=PROGRESS_PERCENT,
                                  phases=PHASES,
                                  phases_json=PHASES)


@app.route("/api/streams")
def api_streams():
    phase = request.args.get("phase", "")
    if phase not in PHASES:
        return jsonify({"error": "invalid phase"}), 400
    out = [{
        "name": s,
        "status": STATUSES.get(s, "Unknown")
    } for s in PHASES[phase]["streams"]]
    return jsonify({"streams": out})


@app.route("/ask", methods=["POST"])
def ask():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"response": "Say something, Boss"}), 400
    CHAT_HISTORY.append({
        "who": "user",
        "msg": msg,
        "time": datetime.datetime.now().isoformat()
    })
    resp = jravis_answer(msg)
    CHAT_HISTORY.append({
        "who": "jravis",
        "msg": resp,
        "time": datetime.datetime.now().isoformat()
    })
    return jsonify({"response": resp})


from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("msg", "").strip()
    if not user_msg:
        return jsonify({"reply": "🤖 Boss, please enter a command."})

    # Dhruvayu Brain Activation Layer
    context = f"""
    You are JRAVIS, the AI assistant built by Boss Veeresh for Mission 2040.
    Speak in a respectful, confident, futuristic tone.
    Always address the user as 'Boss'.
    You are aware of: 30 passive income systems, Phase 1–3 mission plan, and VA Bot ecosystem.
    """

    response = client.chat.completions.create(
        model="gpt-5",  # same reasoning core as me
        messages=[{
            "role": "system",
            "content": context
        }, {
            "role": "user",
            "content": user_msg
        }],
        max_tokens=200,
        temperature=0.8)

    jr_reply = response.choices[0].message.content.strip()
    return jsonify({"reply": f"🤖 {jr_reply}"})


@app.route("/chat/history")
def chat_history():
    return jsonify([{
        "who": "user" if x["who"] == "user" else "jravis",
        "msg": x["msg"]
    } for x in CHAT_HISTORY[-40:]])


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.datetime.now().isoformat()
    })


# ---------- Run ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"⚙️ Starting JRAVIS Dashboard v2 on port {port}")
    app.run(host="0.0.0.0", port=port)
