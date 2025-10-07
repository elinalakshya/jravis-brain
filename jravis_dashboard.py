#!/usr/bin/env python3
"""
JRAVIS Mission 2040 — Single-file Dashboard (Chat + Phase/Streams UI)
Save as: jravis_mission2040.py
Deploy: python jravis_mission2040.py  (Render start command)
Notes: login with your lock code (not printed here)
"""

from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string
import os, datetime, random, math

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "JRAVIS_SECRET")

# --------- Config & Simulated Data (replace with live hooks later) ----------
LOCK_CODE_NAME = "lock code"  # refer to lock code privately (do not print)
PASSCODE = os.environ.get(
    "LOCK_CODE_VALUE",
    "REPLACE_ME")  # set your lock code in Render env var instead of embedding

# Simulated mission/earnings/progress
MISSION_TARGET = 10000000  # target (for progress bar demo)
CURRENT_EARNINGS_INR = 624000
CURRENT_EARNINGS_USD = 8250

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
        ]
    },
    "Phase 2": {
        "status": "Scale up",
        "target": "Grow revenue & automation",
        "streams": ["Phase2_StreamA", "Phase2_StreamB", "Phase2_StreamC"]
    },
    "Phase 3": {
        "status": "Global scaling",
        "target": "Robo Mode worldwide",
        "streams": ["Phase3_StreamA", "Phase3_StreamB"]
    }
}

# Simulated status store (can be replaced by actual JRAVIS worker API)
STATUSES = {}
_status_choices = ["Running ✅", "Idle ⏳", "Error ⚠️", "Starting…"]
for p in PHASES:
    for s in PHASES[p]["streams"]:
        STATUSES[s] = random.choice(_status_choices)

# In-memory chat history (limited)
CHAT_HISTORY = []  # list of {who:'user'|'jravis', msg, time}


# ----------------- Helper logic for smarter replies -----------------
def jravis_answer(user_text):
    """
    Deterministic-ish logic to answer:
    - If user asks about errors or specific streams, respond with statuses and suggestions
    - If user asks about earnings/progress, return calculated values
    - If user issues a command (starts with 'run'/'start'/'stop'/'deploy'), acknowledge
    - Fallback: succinct system status
    """
    txt = user_text.strip().lower()

    # Check for direct stream status requests
    # if user mentions some stream names we know, return their status
    mentioned = [s for s in STATUSES.keys() if s.lower() in txt]
    if mentioned:
        parts = []
        for s in mentioned:
            st = STATUSES.get(s, "Unknown")
            # give short troubleshooting hint for Error
            if "error" in st.lower():
                parts.append(
                    f"{s}: {st} — Suggestion: check API key & recent logs.")
            else:
                parts.append(f"{s}: {st}")
        reply = " | ".join(parts)
        return reply

    # If user asks why multiple streams are in error
    if any(w in txt
           for w in ["why", "what happened", "errors", "showing error"]):
        # collect errors
        errs = [s for s, st in STATUSES.items() if "error" in st.lower()]
        if not errs:
            return "No streams currently reporting errors. All systems look stable."
        # show top 3 errors and general reason
        top = errs[:6]
        return (
            "Streams showing errors: " + ", ".join(top) +
            ". Common causes: API key expire / rate limit / temporary network issue. I can run diagnostics if you ask 'run diagnostics'."
        )

    # Earnings / progress
    if any(w in txt
           for w in ["earn", "revenue", "income", "progress", "target"]):
        pct = min(100, math.floor(
            (CURRENT_EARNINGS_INR / MISSION_TARGET) * 100))
        return (
            f"Earnings: ₹{CURRENT_EARNINGS_INR:,} / Target: ₹{MISSION_TARGET:,} ({pct}%). "
            f"USD: ${CURRENT_EARNINGS_USD:,}. Distance to target: ₹{MISSION_TARGET - CURRENT_EARNINGS_INR:,}."
        )

    # Commands
    if txt.startswith(
        ("run ", "start ", "stop ", "deploy ", "restart ", "reboot ")):
        return f"Command received: '{user_text}'. I will queue the job and report back when it's done."

    # Short casual replies
    if txt in ("hi", "hello", "hey", "how are you", "how's it going"):
        return "JRAVIS here — systems nominal and running 24×7. How can I assist, Boss?"

    # Default helpful status
    running = sum(1 for s in STATUSES.values() if "running" in s.lower())
    errors = sum(1 for s in STATUSES.values() if "error" in s.lower())
    idle = sum(1 for s in STATUSES.values() if "idle" in s.lower())
    return (
        f"Passive streams: {running} running, {idle} idle, {errors} error. "
        "Ask 'why <stream>' or 'earnings' for quick reports.")


# ----------------- Routes -----------------
# Login (code-lock)
LOGIN_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>JRAVIS Login</title>
<style>body{font-family:system-ui;display:flex;height:100vh;align-items:center;justify-content:center;background:#0b1220;color:#fff}
form{background:#0f1724;padding:28px;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.5);width:320px;text-align:center}
input{width:100%;padding:10px;margin-top:12px;border-radius:7px;border:none;background:#08121c;color:#fff}
button{margin-top:12px;padding:10px 18px;border-radius:8px;border:none;background:#10b981;color:#031018;font-weight:700;cursor:pointer}
.hint{color:#9aa6b2;font-size:13px;margin-top:8px}</style></head><body>
<form method="post"><h2>🔐 JRAVIS Access</h2><p>Enter your lock code</p>
<input name="code" type="password" placeholder="lock code" required>
<button>Unlock</button>{% if error %}<div style="color:#ff6b6b;margin-top:10px">{{error}}</div>{% endif %}
<div class="hint">Locked access — I will not display the lock code here again.</div></form></body></html>"""

MAIN_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>JRAVIS — Mission 2040</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#071023;--card:#0f1724;--muted:#9aa6b2;--accent:#10b981}
body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto;background:var(--bg);color:#e6eef6;margin:0}
.header{display:flex;justify-content:space-between;align-items:center;padding:22px 28px}
.title{font-size:20px;font-weight:700}
.container{display:flex;gap:18px;padding:0 28px 28px}
.left{flex:1.2}
.right{width:420px}
.card{background:var(--card);border-radius:12px;padding:18px;margin-bottom:14px;box-shadow:0 8px 30px rgba(2,6,23,.6)}
.progress{background:#071827;height:12px;border-radius:999px;overflow:hidden}
.progress > i{display:block;height:100%;background:linear-gradient(90deg,#10b981,#34d399)}
.row{display:flex;gap:12px;align-items:center;justify-content:space-between}
.small{color:var(--muted);font-size:13px}
.phase-table{width:100%;border-collapse:collapse;margin-top:8px}
.phase-table tr td{padding:10px 6px;border-bottom:1px solid rgba(255,255,255,0.02)}
.phase-click{cursor:pointer}
.stream-list{margin-top:10px}
.stream{display:flex;justify-content:space-between;padding:10px;border-radius:8px;background:#071827;margin-bottom:8px}
.chat-wrap{height:60vh;display:flex;flex-direction:column}
.chat-box{flex:1;padding:12px;overflow:auto;border-radius:8px;background:#081425}
.input{display:flex;padding:8px;margin-top:8px}
.input input{flex:1;padding:10px;border-radius:8px;border:none;background:#071827;color:#fff}
.input button{margin-left:8px;padding:10px 12px;border-radius:8px;border:none;background:#3b82f6;color:#fff}
.msg{margin-bottom:8px;padding:8px;border-radius:8px}
.msg.user{text-align:right;color:#c7d2fe}
.msg.jravis{text-align:left;color:#bbf7d0}
.earn-large{font-size:28px;font-weight:700}
</style>
</head><body>
<div class="header">
  <div>
    <div class="title">Jarvis Brain — Mission 2040 Dashboard</div>
    <div class="small">Control center · Live</div>
  </div>
  <div style="text-align:right">
    <div class="small">Earnings</div>
    <div class="earn-large">₹ {{earn_inr:,}} &nbsp; <small style="font-size:16px">|</small> &nbsp; $ {{earn_usd}}</div>
  </div>
</div>

<div class="container">
  <div class="left">
    <div class="card">
      <div class="row"><div><strong>Mission 2040 Progress</strong><div class="small">Distance to target & timeline</div></div><div><strong>{{progress_percent}}%</strong></div></div>
      <div style="height:12px;margin-top:10px" class="progress"><i style="width:{{progress_percent}}%"></i></div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>Phase Status</strong><div class="small">Click a phase to expand streams</div></div>
      </div>
      <table class="phase-table">
        {% for pname, pdata in phases.items() %}
        <tr class="phase-click" onclick="togglePhase('{{pname}}')">
          <td style="width:180px"><strong>{{pname}}</strong><div class="small">{{pdata.status}}</div></td>
          <td style="text-align:left">{{pdata.target}}</td>
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
      <div style="display:flex;justify-content:space-between">
        <div><strong>Today</strong><div class="small">Tasks & quick actions</div></div>
        <div class="small">Status</div>
      </div>
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
const PHASES = {{ phases_json|safe }};
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

// load a few welcome lines from server-side history
(async function(){ 
  const h = await fetch('/chat/history');
  const j = await h.json();
  j.forEach(item => appendMsg(item.who, item.msg));
})();
</script>
</body></html>
"""


@app.route("/", methods=["GET", "POST"])
def login():
    # login page – do not echo the lock code
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if not code:
            return render_template_string(LOGIN_HTML, error="Enter lock code")
        if code == os.environ.get("LOCK_CODE_VALUE", PASSCODE):
            session["auth"] = True
            return redirect(url_for("main"))
        return render_template_string(LOGIN_HTML, error="Incorrect lock code")
    return render_template_string(LOGIN_HTML)


@app.route("/main")
def main():
    if not session.get("auth"):
        return redirect(url_for("login"))
    # compute progress %
    progress_percent = min(100,
                           int((CURRENT_EARNINGS_INR / MISSION_TARGET) * 100))
    return render_template_string(MAIN_HTML,
                                  earn_inr=CURRENT_EARNINGS_INR,
                                  earn_usd=CURRENT_EARNINGS_USD,
                                  progress_percent=progress_percent,
                                  phases=PHASES,
                                  phases_json={
                                      k: v
                                      for k, v in PHASES.items()
                                  })


# API: streams for a phase
@app.route("/api/streams")
def api_streams():
    phase = request.args.get("phase", "")
    if phase not in PHASES:
        return jsonify({"error": "invalid phase"}), 400
    out = []
    for s in PHASES[phase]["streams"]:
        out.append({"name": s, "status": STATUSES.get(s, "Unknown")})
    return jsonify({"streams": out})


# Chat endpoint
@app.route("/ask", methods=["POST"])
def ask():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"response": "Say something, Boss"}), 400
    # store user
    CHAT_HISTORY.append({
        "who": "user",
        "msg": msg,
        "time": datetime.datetime.now().isoformat()
    })
    # get answer
    resp = jravis_answer(msg)
    # store jravis reply
    CHAT_HISTORY.append({
        "who": "jravis",
        "msg": resp,
        "time": datetime.datetime.now().isoformat()
    })
    return jsonify({"response": resp})


# Chat history (initial load)
@app.route("/chat/history")
def chat_history():
    # return last 20 messages formatted for client
    out = []
    for item in CHAT_HISTORY[-40:]:
        who = 'user' if item["who"] == "user" else 'jravis'
        out.append({"who": who, "msg": item["msg"]})
    # if empty add a greeting
    if not out:
        out = [{
            "who":
            "jravis",
            "msg":
            "JRAVIS online — ask about streams, earnings, or run commands."
        }]
    return jsonify(out)


# Health
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.datetime.now().isoformat()
    })


# ------------------ Run ------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"⚙️  Starting JRAVIS Mission2040 dashboard on port {port}")
    app.run(host="0.0.0.0", port=port)
