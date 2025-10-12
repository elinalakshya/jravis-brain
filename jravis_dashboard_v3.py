#!/usr/bin/env python3
"""
jravis_dashboard_v3.py
- Dark glass UI, lock-protected
- Auto-refresh every 30s (streams + summary)
- Securely calls VA Bot via VABOT_URL and VABOT_API_KEY
- Chat endpoint: local Dhruvayu-style replies; uses OpenAI if OPENAI_API_KEY provided
Save/overwrite your existing jravis_dashboard_v3.py with this file.
"""

from flask import (Flask, request, render_template_string, jsonify, redirect,
                   url_for, session)
import os, requests, datetime, json, time, random

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "jravis_secret_key_fallback")

# Config (from env)
LOCK_CODE = os.environ.get("LOCK_CODE", "2040")
VABOT_URL = os.environ.get("VABOT_URL", "").rstrip(
    "/")  # e.g. https://vabot-dashboard.onrender.com
VABOT_API_KEY = os.environ.get("VABOT_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)

# Basic mission values (can be real values from VA Bot summary endpoint)
MISSION_TARGET = int(os.environ.get("MISSION_TARGET", "4000000"))
# default demo numbers — dashboard will request live from VA Bot if available
DEFAULT_EARNINGS_INR = int(os.environ.get("DEFAULT_EARNINGS_INR", "624000"))
DEFAULT_EARNINGS_USD = int(os.environ.get("DEFAULT_EARNINGS_USD", "8250"))

# Basic phase structure (used as fallback if VA Bot not reachable)
PHASES = {
    "Phase 1": {
        "label":
        "Phase 1 — Fast Kickstart",
        "target_tag":
        "Clear short term debt",
        "streams": [
            "ElinaInstagramReels", "Printify", "MeshyAI", "CadCrowd", "Fiverr",
            "YouTube", "StockImageVideo", "AIBookPublishingKDP",
            "ShopifyDigitalProducts", "StationeryExport"
        ],
    },
    "Phase 2": {
        "label": "Phase 2 — Scale & Systems",
        "target_tag": "Scale revenue & automation",
        "streams": ["Phase2_StreamA", "Phase2_StreamB", "Phase2_StreamC"]
    },
    "Phase 3": {
        "label": "Phase 3 — Robo Mode",
        "target_tag": "Global automation rollout",
        "streams": ["Phase3_StreamA", "Phase3_StreamB"]
    }
}

# local in-memory statuses fallback (used if VABOT unavailable)
_LOCAL_STATUSES = {}
_status_choices = ["Running ✅", "Idle ⏳", "Error ⚠️", "Syncing 🔁"]
for ph in PHASES.values():
    for s in ph["streams"]:
        _LOCAL_STATUSES[s] = random.choice(_status_choices)

CHAT_HISTORY = [{
    "who": "jravis",
    "msg": "JRAVIS online — ask about streams, earnings, or run commands.",
    "ts": time.time()
}]


# ---------------------------
# Helper: VA Bot API wrappers
# ---------------------------
def _vabot_headers():
    h = {}
    if VABOT_API_KEY:
        h["Authorization"] = f"Bearer {VABOT_API_KEY}"
    return h


def vabot_get(path, params=None):
    """GET VABOT_URL + path (path must start with /). Returns dict or {'error':msg}"""
    if not VABOT_URL:
        return {"error": "VABOT_URL not configured"}
    try:
        url = f"{VABOT_URL}{path}"
        r = requests.get(url,
                         headers=_vabot_headers(),
                         params=params,
                         timeout=8)
        if r.status_code >= 400:
            return {"error": f"status {r.status_code}", "details": r.text}
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def vabot_post(path, payload=None):
    if not VABOT_URL:
        return {"error": "VABOT_URL not configured"}
    try:
        url = f"{VABOT_URL}{path}"
        r = requests.post(url,
                          headers=_vabot_headers(),
                          json=payload or {},
                          timeout=12)
        if r.status_code >= 400:
            return {"error": f"status {r.status_code}", "details": r.text}
        # accept json or text
        try:
            return r.json()
        except:
            return {"ok": True, "text": r.text}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------
# Chat: local Dhruvayu-style layer (fallback) and optional OpenAI
# ---------------------------
def dhruvayu_local_reply(user_msg):
    u = user_msg.strip().lower()
    # simple parsing
    if not u:
        return "Say something, Boss — I'm listening."
    if u in ("hi", "hello", "hey"):
        return "Hey Boss! Systems nominal — what's the plan?"
    if "how are you" in u or "status" == u:
        return "All systems go — streams stable. Ask about a stream or say 'report'."
    if "earn" in u or "revenue" in u or "income" in u:
        inr = DEFAULT_EARNINGS_INR
        usd = DEFAULT_EARNINGS_USD
        pct = int((inr / max(1, MISSION_TARGET)) * 100)
        return f"Earnings: ₹{inr:,} INR | ${usd:,} USD — progress {pct}% toward target."
    if "phase" in u:
        return "Phases: click a phase to expand streams. Say 'phase 1 report' for details."
    # ask about a particular stream
    for s in _LOCAL_STATUSES:
        if s.lower() in u:
            st = _LOCAL_STATUSES.get(s, "Unknown")
            if "error" in st.lower():
                return f"{s}: {st} — Suggestion: check the API key, re-run the job, and review logs."
            return f"{s}: {st}"
    # default
    running = sum(1 for v in _LOCAL_STATUSES.values()
                  if "running" in v.lower())
    errors = sum(1 for v in _LOCAL_STATUSES.values() if "error" in v.lower())
    idle = sum(1 for v in _LOCAL_STATUSES.values() if "idle" in v.lower())
    return f"Streams summary — {running} running, {idle} idle, {errors} errors."


# Optional OpenAI usage (if key provided)
def openai_reply(user_msg):
    if not OPENAI_API_KEY:
        return None
    try:
        # use requests to OpenAI chat completions (compatible with older keys)
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model":
            "gpt-4o-mini",  # safe default; adjust if you have different model access
            "messages": [{
                "role":
                "system",
                "content":
                "You are JRAVIS. Answer concisely and respectfully, call the user 'Boss'."
            }, {
                "role": "user",
                "content": user_msg
            }],
            "temperature":
            0.7,
            "max_tokens":
            250
        }
        resp = requests.post("https://api.openai.com/v1/chat/completions",
                             headers=headers,
                             json=payload,
                             timeout=12)
        if resp.status_code != 200:
            return None
        js = resp.json()
        txt = js.get("choices", [{}])[0].get("message", {}).get("content",
                                                                "").strip()
        if txt:
            return txt
        return None
    except Exception:
        return None


# ---------------------------
# Templates (dark glass UI)
# ---------------------------
MAIN_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>JRAVIS — Mission 2040</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#06080b; --panel:rgba(255,255,255,0.04); --muted:#9aa6b2; --accent:#06b6d4;
  --glass:rgba(255,255,255,0.03);
}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,system-ui;background:linear-gradient(180deg,#03060a 0%, #071023 100%);color:#e8eef6}
.header{display:flex;justify-content:space-between;align-items:center;padding:22px 28px;border-bottom:1px solid rgba(255,255,255,0.03)}
.brand{display:flex;flex-direction:column}
.brand h1{margin:0;font-size:20px;letter-spacing:0.3px}
.brand small{color:var(--muted);font-size:12px}
.container{display:flex;gap:18px;padding:20px}
.left{flex:1.6}
.right{width:420px}
.card{background:var(--panel);border-radius:14px;padding:16px;box-shadow:0 8px 30px rgba(3,6,10,0.6);border:1px solid rgba(255,255,255,0.02);margin-bottom:14px}
.big-earn{font-size:26px;font-weight:700}
.progress{height:10px;background:rgba(255,255,255,0.03);border-radius:999px;overflow:hidden;margin-top:8px}
.progress > i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),#34d399);transition:width .6s ease}
.phase-row{display:flex;justify-content:space-between;align-items:center;padding:10px;border-radius:10px;cursor:pointer}
.phase-row:hover{background:rgba(255,255,255,0.02)}
.stream-list{margin-top:10px}
.stream{display:flex;justify-content:space-between;padding:10px;border-radius:8px;background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.005));margin-bottom:8px}
.small{color:var(--muted);font-size:13px}
.chat-box{position:fixed;right:24px;bottom:24px;width:360px;max-height:70vh;border-radius:12px;overflow:hidden}
.chat-header{background:linear-gradient(90deg,var(--accent),#3b82f6);padding:12px;color:#021;display:flex;justify-content:space-between;align-items:center;font-weight:700}
.chat-body{background:#041426;padding:12px;height:360px;overflow:auto;color:#d7eaf6}
.chat-input{display:flex;background:#031122;padding:10px}
.chat-input input{flex:1;padding:10px;border-radius:8px;border:none;background:transparent;color:#fff}
.chat-input button{margin-left:8px;padding:10px 12px;border-radius:8px;border:none;background:linear-gradient(90deg,#3b82f6,#06b6d4);color:#fff}
.tag{background:rgba(255,255,255,0.03);padding:6px 8px;border-radius:999px;font-weight:600}
.footer{padding:18px;color:var(--muted);font-size:13px;text-align:center}
@media (max-width:980px){.container{flex-direction:column}.right{width:auto}}
</style>
</head>
<body>
<header class="header">
  <div class="brand">
    <h1>JRAVIS — Mission 2040</h1>
    <small class="small">Control center · Auto-sync every 30s · Dark mode</small>
  </div>
  <div style="text-align:right">
    <div class="small">Earnings</div>
    <div class="big-earn">₹ {{ earn_inr_fmt }} &nbsp; <span class="small">|</span> &nbsp; $ {{ earn_usd_fmt }}</div>
  </div>
</header>

<div class="container">
  <div class="left">
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>Mission Progress</strong><div class="small">Target & timeline</div></div>
        <div class="tag">{{ progress_percent }}%</div>
      </div>
      <div class="progress"><i style="width:{{ progress_percent }}%"></i></div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div><strong>Phases (click to expand)</strong><div class="small">Phase targets and streams</div></div>
        <div class="small">Auto-sync every 30s</div>
      </div>

      {% for pname, pdata in phases.items() %}
        <div>
          <div class="phase-row" onclick="togglePhase('{{pname}}')">
            <div>
              <div style="font-weight:700">{{ pname }}</div>
              <div class="small">{{ pdata.label }} • {{ pdata.target_tag }}</div>
            </div>
            <div class="small">▶</div>
          </div>
          <div id="phase-{{ loop.index0 }}" style="display:none;padding-top:10px">
            <div class="stream-list" id="list-{{ loop.index0 }}">
              <div class="small">Click to load streams</div>
            </div>
          </div>
        </div>
      {% endfor %}
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>Quick Actions</strong><div class="small">Run selected stream / Sync now</div></div>
        <div><button onclick="syncNow()" style="padding:8px 10px;border-radius:8px;border:none;background:linear-gradient(90deg,#3b82f6,#06b6d4);color:#fff">Sync Now</button></div>
      </div>
      <div style="margin-top:12px" class="small">You can ask JRAVIS in chat to run streams, or press Sync Now to refresh statuses immediately.</div>
    </div>

  </div>

  <div class="right">
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>Today</strong><div class="small">Recent actions</div></div>
        <div class="small">—</div>
      </div>
      <div style="margin-top:12px" class="small">No recent critical alerts.</div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>Debt & Goals</strong><div class="small">Tracker</div></div>
        <div class="small">—</div>
      </div>
      <div style="margin-top:8px" class="small">Target: ₹ {{ target_fmt }}</div>
    </div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>JRAVIS Chat</strong><div class="small">Talk to JRAVIS (Dhruvayu-style)</div></div>
      </div>
      <div id="chat-area" style="margin-top:8px;height:220px;overflow:auto;background:#041426;padding:10px;border-radius:8px;color:#d7eaf6"></div>
      <div style="margin-top:8px;display:flex;gap:8px">
        <input id="chat-input" placeholder="Ask JRAVIS..." style="flex:1;padding:10px;border-radius:8px;border:none;background:#021428;color:#fff" onkeydown="if(event.key==='Enter')sendChat()">
        <button onclick="sendChat()" style="padding:10px 12px;border-radius:8px;border:none;background:linear-gradient(90deg,#3b82f6,#06b6d4);color:#fff">Send</button>
      </div>
    </div>

  </div>
</div>

<div class="footer">© JRAVIS · Mission 2040</div>

<script>
const PHASES = {{ phases_json|tojson }};
const AUTO_REFRESH_SECONDS = 30;

function togglePhase(name) {
  // map name -> index
  const keys = Object.keys(PHASES);
  const idx = keys.indexOf(name);
  if (idx < 0) return;
  const el = document.getElementById('phase-'+idx);
  if (el.style.display === 'none' || el.style.display === '') {
    el.style.display = 'block';
    loadPhaseStreams(idx, name);
  } else {
    el.style.display = 'none';
  }
}

async function loadPhaseStreams(idx, name) {
  const container = document.getElementById('list-'+idx);
  container.innerHTML = '<div class="small">Loading…</div>';
  try {
    const res = await fetch('/api/streams?phase=' + encodeURIComponent(name));
    const j = await res.json();
    container.innerHTML = '';
    if (j.streams && j.streams.length) {
      j.streams.forEach(s => {
        const div = document.createElement('div');
        div.className = 'stream';
        div.innerHTML = `<div>${s.name}</div><div class="small">${s.status}</div>`;
        container.appendChild(div);
      });
    } else {
      container.innerHTML = '<div class="small">No streams or error: ' + (j.error||'') + '</div>';
    }
  } catch (e) {
    container.innerHTML = '<div class="small">Error loading streams</div>';
  }
}

async function syncNow(){
  appendChat('jravis', 'Syncing now — contacting VA Bot...');
  await refreshAll();
  appendChat('jravis', 'Sync complete.');
}

async function refreshAll(){
  // refresh summary and any open phases
  await fetch('/api/summary').then(r=>r.json()).then(j=>{
    // update earnings display quickly
    document.querySelector('.big-earn').innerText = '₹ ' + j.earn_inr_fmt + '  |  $ ' + j.earn_usd_fmt;
    document.querySelector('.tag').innerText = j.progress_percent + '%';
    document.querySelector('.progress > i').style.width = j.progress_percent + '%';
  }).catch(()=>{});
  // refresh any open phase containers
  Object.keys(PHASES).forEach(async (name, idx) => {
    const el = document.getElementById('phase-'+idx);
    if (el && el.style.display === 'block') {
      await loadPhaseStreams(idx, name);
    }
  });
}

// Chat helpers
function appendChat(who, text){
  const area = document.getElementById('chat-area');
  const b = document.createElement('div');
  b.style.padding = '6px 8px';
  b.style.marginBottom = '8px';
  b.style.borderRadius = '8px';
  if (who === 'user') {
    b.style.textAlign = 'right';
    b.style.background = 'linear-gradient(90deg, rgba(59,130,246,0.12), rgba(6,182,212,0.08))';
    b.innerText = '🧑‍💼 ' + text;
  } else {
    b.style.textAlign = 'left';
    b.style.background = '#021827';
    b.innerText = '🤖 ' + text;
  }
  area.appendChild(b);
  area.scrollTop = area.scrollHeight;
}

async function sendChat(){
  const input = document.getElementById('chat-input');
  const txt = input.value.trim();
  if (!txt) return;
  appendChat('user', txt);
  input.value = '';
  try {
    const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: txt})});
    const j = await res.json();
    appendChat('jravis', j.reply);
  } catch (e) {
    appendChat('jravis', 'Error contacting JRAVIS.');
  }
}

// initial chat history load
(async function(){
  const r = await fetch('/chat/history');
  const h = await r.json();
  h.forEach(i => appendChat(i.who === 'user' ? 'user' : 'jravis', i.msg));
})();

// auto refresh schedule
setInterval(refreshAll, AUTO_REFRESH_SECONDS * 1000);
</script>
</body>
</html>
"""


# ---------------------------
# Routes
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if code == LOCK_CODE:
            session["auth"] = True
            return redirect(url_for("main"))
        else:
            return render_template_string(
                "<h3 style='color:#fee'>Incorrect lock code</h3><a href='/'>Back</a>"
            )
    if session.get("auth"):
        return redirect(url_for("main"))
    return render_template_string("""
    <!doctype html><html><head><meta charset="utf-8"><title>JRAVIS Access</title>
    <style>body{background:#071023;color:#e8eef6;font-family:Inter,system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
    .card{background:rgba(255,255,255,0.03);padding:24px;border-radius:12px;border:1px solid rgba(255,255,255,0.02)}
    input{padding:12px;border-radius:8px;border:none;width:260px;background:transparent;color:#fff}
    button{padding:10px 12px;margin-left:8px;border-radius:8px;border:none;background:linear-gradient(90deg,#3b82f6,#06b6d4);color:#fff}
    </style></head><body>
    <form method="post" class="card"><div style="font-weight:700;font-size:18px;margin-bottom:8px">JRAVIS — Enter Lock Code</div>
    <input name="code" type="password" placeholder="Lock code" autofocus><button>Unlock</button></form></body></html>
    """)


@app.route("/main")
def main():
    if not session.get("auth"):
        return redirect(url_for("login"))
    # attempt to get summary from VA Bot
    summary = vabot_get("/api/summary") if VABOT_URL else {
        "error": "not configured"
    }
    if summary and "error" not in summary:
        earn_inr = int(summary.get("earn_inr", DEFAULT_EARNINGS_INR))
        earn_usd = int(summary.get("earn_usd", DEFAULT_EARNINGS_USD))
    else:
        earn_inr = DEFAULT_EARNINGS_INR
        earn_usd = DEFAULT_EARNINGS_USD

    progress_percent = min(100, int((earn_inr / max(1, MISSION_TARGET)) * 100))
    return render_template_string(MAIN_HTML,
                                  earn_inr_fmt=f"{earn_inr:,}",
                                  earn_usd_fmt=f"{earn_usd:,}",
                                  progress_percent=progress_percent,
                                  target_fmt=f"{MISSION_TARGET:,}",
                                  phases=PHASES,
                                  phases_json=PHASES)


@app.route("/api/streams")
def api_streams():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    phase = request.args.get("phase", "")
    if not phase:
        return jsonify({"error": "no phase"}), 400
    # call VA Bot for streams in phase
    if VABOT_URL:
        resp = vabot_get(f"/api/status?phase={phase}")
        if "error" not in resp and isinstance(resp.get("streams", None), list):
            return jsonify(resp)
        # fallback to local statuses if VA Bot returns error
    streams = [{
        "name": s,
        "status": _LOCAL_STATUSES.get(s, "Unknown")
    } for s in PHASES.get(phase, {}).get("streams", [])]
    return jsonify({"streams": streams})


@app.route("/api/summary")
def api_summary():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    if VABOT_URL:
        resp = vabot_get("/api/summary")
        if "error" not in resp:
            earn = int(resp.get("earn_inr", DEFAULT_EARNINGS_INR))
            usd = int(resp.get("earn_usd", DEFAULT_EARNINGS_USD))
            progress_pct = min(100, int((earn / max(1, MISSION_TARGET)) * 100))
            return jsonify({
                "earn_inr": earn,
                "earn_usd": usd,
                "earn_inr_fmt": f"{earn:,}",
                "earn_usd_fmt": f"{usd:,}",
                "progress_percent": progress_pct
            })
        # fallback
    earn = DEFAULT_EARNINGS_INR
    usd = DEFAULT_EARNINGS_USD
    return jsonify({
        "earn_inr":
        earn,
        "earn_usd":
        usd,
        "earn_inr_fmt":
        f"{earn:,}",
        "earn_usd_fmt":
        f"{usd:,}",
        "progress_percent":
        min(100, int((earn / max(1, MISSION_TARGET)) * 100))
    })


@app.route("/chat", methods=["POST"])
def chat():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json() or {}
    user_msg = data.get("message") or data.get("msg") or ""
    user_msg = user_msg.strip()
    if not user_msg:
        return jsonify({"reply": "Say something, Boss."})

    # Append to history
    CHAT_HISTORY.append({"who": "user", "msg": user_msg, "ts": time.time()})

    # First attempt: if VA Bot provides chat brain endpoint, forward
    if VABOT_URL:
        try:
            # pass through to VA Bot brain if it has /api/chat
            resp = vabot_post("/api/chat", {"message": user_msg})
            if isinstance(resp, dict) and "reply" in resp:
                reply_text = resp.get("reply")
                CHAT_HISTORY.append({
                    "who": "jravis",
                    "msg": reply_text,
                    "ts": time.time()
                })
                return jsonify({"reply": reply_text})
        except Exception:
            pass

    # Second attempt: use OpenAI if configured
    ai_text = openai_reply(user_msg)
    if ai_text:
        reply = ai_text
    else:
        # fallback local Dhruvayu-style reply
        reply = dhruvayu_local_reply(user_msg)

    CHAT_HISTORY.append({"who": "jravis", "msg": reply, "ts": time.time()})
    return jsonify({"reply": reply})


@app.route("/chat/history")
def chat_history():
    if not session.get("auth"):
        return jsonify([])
    # return last 40 items
    out = []
    for x in CHAT_HISTORY[-40:]:
        out.append({"who": x["who"], "msg": x["msg"]})
    return jsonify(out)


@app.route("/health")
def health():
    return jsonify({
        "status": "JRAVIS online",
        "time": datetime.datetime.now().isoformat()
    })


# ---------------------------
# Run
# ---------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
