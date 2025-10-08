#!/usr/bin/env python3
"""
JRAVIS Mission 2040 — Integrated Dashboard v3
Phase-based automation + VA Bot API integration
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import os, requests, datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secure-key")

# 🔐 Security and VA Bot integration
LOCK_CODE = os.environ.get("LOCK_CODE", "2040")
VABOT_URL = os.environ.get("VABOT_URL", "").rstrip("/")
VABOT_API_KEY = os.environ.get("VABOT_API_KEY", "")

# Example phase data (simplified)
PHASES = {
    "Phase 1": {
        "streams":
        ["ElinaInstagramReels", "MeshyAI", "Printify", "StationeryExport"],
        "target":
        500000
    },
    "Phase 2": {
        "streams": ["YouTube", "Fiverr", "CadCrowd", "StockImages"],
        "target": 2000000
    },
    "Phase 3": {
        "streams":
        ["RealEstateAutomation", "LakshyaGlobal", "PassiveInvestmentSystem"],
        "target":
        10000000
    },
}

CURRENT_EARNINGS_INR = 125000
CURRENT_EARNINGS_USD = 1500
MISSION_TARGET = 12000000


# --- Utility: Secure VA Bot API calls ---
def vabot_request(path, method="GET", payload=None):
    if not VABOT_URL:
        return {"error": "VABOT_URL not configured"}
    headers = {"Authorization": f"Bearer {VABOT_API_KEY}"}
    try:
        if method == "POST":
            r = requests.post(f"{VABOT_URL}{path}",
                              json=payload or {},
                              headers=headers,
                              timeout=10)
        else:
            r = requests.get(f"{VABOT_URL}{path}", headers=headers, timeout=10)
        if r.status_code in (200, 201):
            return r.json()
        return {
            "error": f"VA Bot responded with {r.status_code}",
            "details": r.text
        }
    except Exception as e:
        return {"error": str(e)}


# --- HTML Templates ---
LOGIN_HTML = """
<!doctype html>
<title>JRAVIS Lock</title>
<style>
body {font-family:system-ui;background:#111;color:#eee;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;}
input{padding:12px 18px;border:none;border-radius:6px;margin-top:12px;font-size:18px;text-align:center;}
button{padding:12px 18px;margin-top:12px;font-size:16px;border:none;border-radius:6px;background:#00bcd4;color:#fff;cursor:pointer;}
</style>
<h1>🔐 JRAVIS Access</h1>
<form method="post">
<input type="password" name="code" placeholder="Enter Lock Code" autofocus>
<br><button type="submit">Unlock</button>
</form>
"""

DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
<title>JRAVIS Mission 2040</title>
<style>
body {font-family:system-ui;background:#f7f9fb;margin:0;padding:0;color:#222;}
header{background:#111;color:#fff;padding:20px;text-align:center;}
main{padding:20px;}
h2{margin-top:30px;}
.phase{background:#fff;padding:16px;margin:12px 0;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,.1);}
ul{list-style:none;padding:0;}
li{margin:6px 0;}
.chat-box{position:fixed;bottom:0;right:0;width:340px;background:#fff;border-top-left-radius:12px;border-top-right-radius:12px;
box-shadow:0 -2px 10px rgba(0,0,0,0.1);}
.chat-header{background:#00bcd4;color:#fff;padding:10px;border-top-left-radius:12px;border-top-right-radius:12px;font-weight:bold;}
.chat-body{height:240px;overflow-y:auto;padding:10px;font-size:14px;}
.chat-input{display:flex;border-top:1px solid #ddd;}
.chat-input input{flex:1;border:none;padding:10px;font-size:14px;}
.chat-input button{border:none;background:#00bcd4;color:#fff;padding:10px 16px;cursor:pointer;}
.progress{height:8px;background:#ddd;border-radius:5px;margin-top:8px;}
.bar{height:8px;background:#4caf50;border-radius:5px;}
</style>
</head>
<body>
<header>
<h1>JRAVIS — Mission 2040 Dashboard</h1>
<div>💰 INR ₹{{ "{:,}".format(earn_inr) }} | 💵 USD ${{ "{:,}".format(earn_usd) }}</div>
<div>🎯 Target: ₹{{ "{:,}".format(target) }} | Progress: {{ progress }}%</div>
<div class="progress"><div class="bar" style="width:{{ progress }}%"></div></div>
</header>

<main>
{% for name, data in phases.items() %}
<div class="phase">
  <h2 onclick="loadPhase('{{ name }}')">▶ {{ name }}</h2>
  <ul id="{{ name|replace(' ','_') }}_list"></ul>
</div>
{% endfor %}
</main>

<div class="chat-box">
<div class="chat-header">🤖 JRAVIS Chat</div>
<div class="chat-body" id="chat-body">
<div>🧠 JRAVIS online — ask about streams, earnings, or run commands.</div>
</div>
<div class="chat-input">
<input id="chat-input" placeholder="Type your message..." onkeydown="if(event.key==='Enter')sendChat()">
<button onclick="sendChat()">Send</button>
</div>
</div>

<script>
async function loadPhase(phase){
  const ul=document.getElementById(phase.replaceAll(' ','_')+'_list');
  ul.innerHTML='<li>Loading...</li>';
  const r=await fetch('/api/streams?phase='+phase);
  const j=await r.json();
  ul.innerHTML='';
  j.streams.forEach(s=>{
    const li=document.createElement('li');
    li.textContent=`${s.name} — ${s.status}`;
    ul.appendChild(li);
  });
}
async function sendChat(){
  const input=document.getElementById('chat-input');
  const body=document.getElementById('chat-body');
  const msg=input.value.trim(); if(!msg)return;
  body.innerHTML+=`<div>🧑‍💼 ${msg}</div>`;
  input.value='';
  const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg})});
  const j=await r.json();
  body.innerHTML+=`<div>🤖 ${j.reply}</div>`;
  body.scrollTop=body.scrollHeight;
}
</script>
</body>
</html>
"""


# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("code") == LOCK_CODE:
            session["auth"] = True
            return redirect(url_for("main"))
    if session.get("auth"):
        return redirect(url_for("main"))
    return render_template_string(LOGIN_HTML)


@app.route("/main")
def main():
    if not session.get("auth"):
        return redirect("/")
    progress = round((CURRENT_EARNINGS_INR / MISSION_TARGET) * 100, 2)
    return render_template_string(
        DASHBOARD_HTML,
        earn_inr=CURRENT_EARNINGS_INR,
        earn_usd=CURRENT_EARNINGS_USD,
        target=MISSION_TARGET,
        progress=progress,
        phases=PHASES,
    )


@app.route("/api/streams")
def api_streams():
    phase = request.args.get("phase", "")
    if not phase:
        return jsonify({"error": "No phase"}), 400
    resp = vabot_request(f"/api/status?phase={phase}")
    if "error" in resp:
        # fallback dummy data
        data = [{
            "name": s,
            "status": "Unknown"
        } for s in PHASES.get(phase, {}).get("streams", [])]
        return jsonify({"streams": data, "error": resp["error"]})
    return jsonify(resp)


@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("msg", "").lower()
    if "earn" in msg:
        return jsonify({
            "reply":
            f"Total earnings: ₹{CURRENT_EARNINGS_INR:,} (Target ₹{MISSION_TARGET:,})"
        })
    elif "phase" in msg:
        return jsonify({
            "reply":
            f"Phase 1 active: {len(PHASES['Phase 1']['streams'])} streams. Others in queue."
        })
    elif "error" in msg:
        resp = vabot_request("/api/status")
        return jsonify({"reply": f"Checked VA Bot — found: {resp}"})
    else:
        return jsonify({"reply": "All systems nominal, Boss ⚡"})


@app.route("/health")
def health():
    return jsonify({
        "status": "JRAVIS online",
        "time": datetime.datetime.now().isoformat()
    })


# --- Run ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"⚙️  JRAVIS Mission 2040 v3 running on port {port}")
    app.run(host="0.0.0.0", port=port)
