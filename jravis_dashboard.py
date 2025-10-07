#!/usr/bin/env python3
"""
JRAVIS Web Dashboard (Single-File Version)
Chat + Status + Code Lock ('MY OG')
Deploy directly on Render (PORT=10000)
"""

from flask import Flask, request, jsonify, session, redirect
from flask import render_template_string, url_for
import os, datetime, random

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "JRAVIS_SECRET")
PASSCODE = "MY OG"

# Simulated stream status for Phase 1
STREAMS = [
    "ElinaInstagramReels", "Printify", "MeshyAI", "CadCrowd", "Fiverr",
    "YouTube", "StockImageVideo", "AIBookPublishingKDP",
    "ShopifyDigitalProducts", "StationeryExport"
]
STREAM_STATUS = {
    s: random.choice(["Running ✅", "Idle ⏳", "Error ⚠️"])
    for s in STREAMS
}

# ---------------------- Templates ----------------------
LOGIN_HTML = """
<!doctype html>
<html>
<head>
  <title>JRAVIS Login</title>
  <style>
    body { font-family: system-ui; display:flex; align-items:center; justify-content:center; height:100vh; background:#0f172a; color:white; }
    form { background:#1e293b; padding:40px; border-radius:12px; text-align:center; box-shadow:0 0 20px rgba(0,0,0,0.5); }
    input { padding:10px; border:none; border-radius:6px; margin-top:12px; width:200px; text-align:center; }
    button { margin-top:12px; padding:10px 20px; border:none; border-radius:6px; background:#3b82f6; color:white; font-weight:bold; cursor:pointer; }
  </style>
</head>
<body>
  <form method="post">
    <h2>🔐 JRAVIS Access</h2>
    <p>Enter your passcode</p>
    <input type="password" name="code" placeholder="Enter code" required>
    <br>
    <button type="submit">Login</button>
    {% if error %}<p style="color:red">{{error}}</p>{% endif %}
  </form>
</body>
</html>
"""

DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
  <title>JRAVIS Control Center</title>
  <style>
    body { font-family: system-ui; margin:0; display:flex; height:100vh; background:#0f172a; color:white; }
    #left { flex:2; display:flex; flex-direction:column; border-right:2px solid #1e293b; }
    #right { flex:1.2; padding:20px; background:#1e293b; overflow-y:auto; }
    .chat { flex:1; padding:20px; overflow-y:auto; }
    .input-area { display:flex; padding:10px; background:#1e293b; }
    input { flex:1; padding:10px; border:none; border-radius:6px; }
    button { margin-left:8px; padding:10px 16px; border:none; border-radius:6px; background:#3b82f6; color:white; cursor:pointer; font-weight:bold; }
    .msg { margin-bottom:10px; }
    .user { text-align:right; color:#a5b4fc; }
    .jravis { text-align:left; color:#34d399; }
    .stream { background:#334155; padding:10px; border-radius:8px; margin-bottom:8px; }
  </style>
</head>
<body>
  <div id="left">
    <div class="chat" id="chat"></div>
    <div class="input-area">
      <input id="msg" placeholder="Talk to JRAVIS..." onkeydown="if(event.key==='Enter')sendMsg()">
      <button onclick="sendMsg()">Send</button>
    </div>
  </div>
  <div id="right">
    <h3>⚙️ System Status</h3>
    <div id="streams">
      {% for name, status in streams.items() %}
      <div class="stream"><strong>{{name}}</strong><br>{{status}}</div>
      {% endfor %}
    </div>
  </div>

  <script>
    async function sendMsg(){
      const msgBox=document.getElementById('msg');
      const chat=document.getElementById('chat');
      const text=msgBox.value.trim();
      if(!text)return;
      chat.innerHTML+=`<div class='msg user'>🧑‍💼 ${text}</div>`;
      msgBox.value='';
      const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
      const j=await r.json();
      chat.innerHTML+=`<div class='msg jravis'>🤖 ${j.response}</div>`;
      chat.scrollTop=chat.scrollHeight;
    }
  </script>
</body>
</html>
"""


# ---------------------- Routes ----------------------
@app.route("/", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    code = request.form.get("code", "").strip()
    if code == PASSCODE:
      session["auth"] = True
      return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_HTML,
                                  error="Incorrect code. Try again.")
  return render_template_string(LOGIN_HTML)


@app.route("/dashboard")
def dashboard():
  if not session.get("auth"):
    return redirect(url_for("login"))
  return render_template_string(DASHBOARD_HTML, streams=STREAM_STATUS)


@app.route("/ask", methods=["POST"])
def ask():
  if not session.get("auth"):
    return jsonify({"error": "Unauthorized"}), 403
  user_msg = request.json.get("message", "")
  if not user_msg:
    return jsonify({"response": "Please type something, Boss ⚡"})
  reply = random.choice([
      "All systems nominal, Boss ⚡",
      "JRAVIS here — executing Phase 1 routines now!",
      f"Received your command: '{user_msg}'. Processing...",
      "Passive streams stable. Earnings growth projection: +4.3%.",
      "Everything’s running 24×7 — you can relax, Boss 👑"
  ])
  return jsonify({
      "response": reply,
      "time": datetime.datetime.now().isoformat()
  })


@app.route("/health")
def health():
  return jsonify({
      "status": "JRAVIS dashboard live ✅",
      "time": datetime.datetime.now().isoformat()
  })


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  print(f"⚙️  Starting JRAVIS Dashboard on port {port}")
  app.run(host="0.0.0.0", port=port)
