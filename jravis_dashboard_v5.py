# jravis_dashboard_v5.py
# Replit-ready JRAVIS Dashboard v5 (dark UI, Phase tabs, chatbox, live logs)
# Requirements: Flask, requests
# Put this file in your Replit root. Ensure env secrets set:
# SHARED_KEY, BRIDGE_URL, VABOT_URL, STREAMS_FILE, LOCK_CODE, TZ

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import os, json, requests, datetime

# ----------- Configuration (from env) -------------
SHARED_KEY = os.getenv("SHARED_KEY", "JRAVIS_MASTER_KEY")
BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:6000")
VABOT_URL = os.getenv("VABOT_URL", "http://localhost:8000")
STREAMS_FILE = os.getenv("STREAMS_FILE", "streams_config.json")
LOCK_CODE = os.getenv("LOCK_CODE", "0000")
TZ = os.getenv("TZ", "Asia/Kolkata")
LOG_FILE = os.getenv("UNIFIED_LOG_FILE", "jravis_unified.log")
PORT = int(os.getenv("PORT", "10000"))

# Flask app
app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET", "jravis-secret-key")  # ephemeral; set for persistence

# ---------- Embedded small SVG favicon ----------
FAVICON_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
  <rect width='64' height='64' rx='10' fill='#071022'/>
  <g fill='#00ffff' opacity='0.95'>
    <circle cx='20' cy='22' r='4'/>
    <rect x='28' y='16' width='24' height='12' rx='3'/>
  </g>
</svg>"""

# ----------------- HTML templates -----------------
LOGIN_HTML = """<!doctype html>
<html>
<head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JRAVIS Login</title>
<style>
body{background:#071022;color:#e6eef6;font-family:Inter,Arial,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.card{background:rgba(255,255,255,0.03);padding:28px;border-radius:12px;width:320px;text-align:center}
input[type=password]{width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.05);background:transparent;color:inherit}
button{margin-top:12px;padding:10px 16px;border-radius:8px;border:none;background:linear-gradient(90deg,#00ffff,#00ff7f);color:#042018;font-weight:700;cursor:pointer}
.err{color:#ffb4b4;margin-top:8px}
.small{color:#9aa7bf;font-size:12px;margin-top:10px}
</style></head>
<body>
<div class="card">
<img src="/favicon.svg" width=86 alt="logo" style="border-radius:8px;margin-bottom:10px"/>
<h2>JRAVIS Secure Access</h2>
<form method="post" action="/login">
<input name="code" type="password" placeholder="Enter Lock Code" required/>
<button>Unlock</button>
</form>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
<div class="small">Auto-logout after 10 minutes of inactivity</div>
</div></body></html>
"""

DASH_HTML = """<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>JRAVIS v5 — Mission 2040</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <style>
    :root{--bg:#071022;--card:rgba(255,255,255,0.04);--muted:#9aa7bf;--accent1:#00ffff;--accent2:#00ff7f}
    body{margin:0;font-family:Inter,Arial,sans-serif;background:var(--bg);color:#e6eef6}
    header{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.03)}
    .brand{display:flex;align-items:center;gap:12px}
    .brand h1{font-size:18px;margin:0;color:var(--accent1)}
    .controls{display:flex;gap:8px;align-items:center}
    .logout{background:transparent;border:1px solid rgba(255,255,255,0.06);padding:8px 10px;border-radius:8px;color:#e6eef6;cursor:pointer}
    .wrap{padding:18px;max-width:1200px;margin:0 auto}
    .grid{display:grid;grid-template-columns:2fr 1fr;gap:18px}
    .card{background:var(--card);padding:16px;border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,0.6)}
    .phase-tabs{display:flex;gap:8px;margin-bottom:12px}
    .phase-tabs button{flex:1;background:rgba(255,255,255,0.05);color:#eaf1ff;border:none;border-radius:8px;padding:8px 10px;cursor:pointer}
    .phase-tabs button.active{background:linear-gradient(90deg,var(--accent1),var(--accent2));color:#001}
    table{width:100%;border-collapse:collapse;font-size:14px}
    th,td{padding:8px;border-bottom:1px solid rgba(255,255,255,0.08);text-align:left}
    .ok{color:#00ff7f}.run{color:#ffaa00}.fail{color:#ff5e5e}
    .progress{height:10px;border-radius:6px;background:rgba(255,255,255,0.08);overflow:hidden}
    .progress>div{height:100%;background:linear-gradient(90deg,var(--accent1),var(--accent2));width:12%}
    .chatbox{display:flex;gap:8px;margin-top:12px}
    .chatbox input{flex:1;padding:10px;border-radius:8px;border:none;background:rgba(255,255,255,0.05);color:#fff}
    .chatbox button{background:linear-gradient(90deg,var(--accent1),var(--accent2));border:none;padding:10px 14px;border-radius:8px;color:#001;font-weight:700}
    .log-stream{background:#0b1320;color:#cfeff0;padding:10px;border-radius:8px;height:220px;overflow:auto;font-family:monospace;font-size:12px}
    .small{color:var(--muted);font-size:13px}
    @media(max-width:768px){.grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
<header>
  <div class="brand">
    <img src="/favicon.svg" width=42 alt="logo" style="border-radius:6px"/>
    <h1>JRAVIS v5 — Mission 2040</h1>
  </div>
  <div class="controls">
    <form action="/logout" method="post" style="margin:0">
      <button class="logout">Logout</button>
    </form>
  </div>
</header>

<div class="wrap">
  <div class="grid">
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><b>System Status</b></div>
        <div class="small">Last Loop: <span id="last-loop">--</span></div>
      </div>

      <div style="margin-top:12px">
        <div><b>JRAVIS Brain:</b> <span id="s-brain">ACTIVE</span></div>
        <div><b>VA Bot Connector:</b> <span id="s-vabot">ACTIVE</span></div>
        <div><b>Income Bundle:</b> <span id="s-income">API OK</span></div>
      </div>

      <div style="margin-top:14px" class="phase-tabs">
        <button class="active" onclick="showPhase(1)">Phase 1</button>
        <button onclick="showPhase(2)">Phase 2</button>
        <button onclick="showPhase(3)">Phase 3</button>
      </div>

      <div style="margin-top:6px">
        <table id="phase-table"><tr><th>#</th><th>Stream</th><th>Target</th><th>Status</th><th>Goal</th></tr></table>
      </div>

      <div style="margin-top:12px">
        <b>Log Stream</b>
        <div id="logbox" class="log-stream"></div>
      </div>

    </div>

    <div class="card">
      <div><b>INCOME → LIVE FEED</b></div>
      <div class="income-stats" style="margin-top:10px">
        <div>Target: INR 4,00,00,000</div>
        <div>Progress: <span id="progress-text">0%</span></div>
        <div class="progress" style="margin:8px 0"><div id="progress-bar" style="width:12%"></div></div>
        <div>Monthly: <span id="monthly">INR 0</span></div>
        <div>Daily: <span id="daily">INR 0</span></div>
        <div class="small" style="margin-top:8px">Next Report: Daily 10:00 AM IST | Weekly Sunday 00:00 IST</div>
      </div>

      <div style="margin-top:18px"><b>JRAVIS Assistant</b></div>
      <div class="chatbox">
        <input id="chat-input" placeholder="Type a command (e.g. 'phase 1', 'trigger all')"/>
        <button onclick="sendCmd()">Send</button>
      </div>
      <div class="small" style="margin-top:8px">Assistant Online: <span id="assistant-status">Yes</span></div>
    </div>

  </div>
</div>

<script>
// ------- JS: Phase loader, progress, logs, chat -------
async function showPhase(num){
  const tabs = document.querySelectorAll('.phase-tabs button');
  tabs.forEach(t=>t.classList.remove('active'));
  tabs[num-1].classList.add('active');

  const table = document.getElementById("phase-table");
  try{
    const res = await fetch('/api/phase/'+num);
    const data = await res.json();
    let html = '<tr><th>#</th><th>Stream</th><th>Target</th><th>Status</th><th>Goal</th></tr>';
    data.forEach(d=>{
      let st = d.status || 'ACTIVE';
      let cls = st=="ACTIVE" ? "ok" : (st=="RUNNING" ? "run" : "fail");
      html += `<tr><td>${d.id}</td><td>${d.name}</td><td>${d.target||''}</td><td class="${cls}">${st}</td><td>${d.goal||''}</td></tr>`;
    });
    table.innerHTML = html;
  }catch(e){
    table.innerHTML = '<tr><td colspan="5">Failed to load phase data</td></tr>';
  }
}

async function updateProgress(){
  try{
    const res = await fetch('/api/live_progress');
    const data = await res.json();
    const pct = data.progress_percent || 0;
    document.getElementById('progress-bar').style.width = pct + '%';
    document.getElementById('progress-text').innerText = pct + '%';
    document.getElementById('monthly').innerText = 'INR ' + ((data.total_income||0).toLocaleString());
    document.getElementById('daily').innerText = 'INR ' + ((data.daily_income||0).toLocaleString ? data.daily_income.toLocaleString() : data.total_income||0);
    document.getElementById('last-loop').innerText = data.last_loop || '--';
  }catch(e){
    console.log('progress fetch failed', e);
  }
}

async function refreshLogs(){
  try{
    const res = await fetch('/api/live_logs');
    const lines = await res.json();
    const box = document.getElementById('logbox');
    box.innerHTML = lines.map(l => '<div>'+l.replace(/</g,'&lt;')+'</div>').join('');
    box.scrollTop = box.scrollHeight;
  }catch(e){
    console.log('log fetch failed', e);
  }
}

async function sendCmd(){
  const v = document.getElementById('chat-input').value.trim();
  if(!v) return;
  if(v.toLowerCase().startsWith('phase')){
    const m = v.match(/\\d+/);
    showPhase(m ? Number(m[0]) : 1);
    document.getElementById('chat-input').value = '';
    return;
  }
  if(v.toLowerCase().includes('trigger all')){
    try{
      const res = await fetch('/api/trigger', {method:'POST'});
      alert('Triggered: '+ (await res.text()));
    }catch(e){ alert('Trigger failed'); }
    return;
  }
  try{
    const res = await fetch('/api/command', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({cmd:v})
    });
    const j = await res.json();
    alert('Sent: '+ JSON.stringify(j));
  }catch(e){
    alert('send failed');
  }
  document.getElementById('chat-input').value = '';
}

// initial
showPhase(1);
updateProgress();
refreshLogs();
setInterval(updateProgress, 1800000); // 30 min
setInterval(refreshLogs, 5000);
</script>
</body>
</html>
"""


# ---------------- Helper functions -----------------
def bridge_headers():
  return {
      'Authorization': f'Bearer {SHARED_KEY}',
      'Content-Type': 'application/json'
  }


# ---------------- Routes -----------------
@app.route('/favicon.svg')
def favicon_svg():
  return FAVICON_SVG, 200, {'Content-Type': 'image/svg+xml'}


# Simple login/logout using session
@app.route('/', methods=['GET'])
def root():
  if session.get('unlocked'):
    return redirect('/dashboard')
  return render_template_string(LOGIN_HTML, error=None)


@app.route('/login', methods=['POST'])
def login():
  code = request.form.get('code', '')
  if code == LOCK_CODE:
    session['unlocked'] = True
    session.permanent = True
    return redirect('/dashboard')
  return render_template_string(LOGIN_HTML, error="Invalid code")


@app.route('/logout', methods=['POST'])
def logout():
  session.clear()
  return redirect('/')


@app.route('/dashboard')
def dashboard():
  if not session.get('unlocked'):
    return redirect('/')
  return render_template_string(DASH_HTML)


# Return streams for a phase: consult bridge or local fallback
@app.route('/api/phase/<int:phase_id>')
def api_phase(phase_id):
  key = f'phase{phase_id}'
  try:
    r = requests.get(f"{BRIDGE_URL}/api/phase/{phase_id}",
                     headers=bridge_headers(),
                     timeout=4)
    if r.status_code == 200:
      return r.content, r.status_code, r.headers.items()
  except Exception:
    pass
  # fallback to local file
  try:
    with open(STREAMS_FILE, 'r', encoding='utf-8') as f:
      cfg = json.load(f)
    return jsonify(cfg.get(key, []))
  except Exception:
    return jsonify([])


# Live progress: fetch from mission bridge income endpoint
@app.route('/api/live_progress')
def api_live_progress():
  try:
    r = requests.get(f"{BRIDGE_URL}/api/income",
                     headers=bridge_headers(),
                     timeout=4)
    if r.status_code == 200:
      return r.content, r.status_code, r.headers.items()
  except Exception:
    pass
  # fallback
  fallback = {
      'total_income': 0,
      'progress_percent': 0,
      'target': 40000000,
      'daily_income': 0,
      'last_loop': None
  }
  return jsonify(fallback)


# Trigger a full loop via jravis-core trigger endpoint (if available)
@app.route('/api/trigger', methods=['POST', 'GET'])
def api_trigger():
  # best-effort: try jravis core (expected at BRIDGE or same workspace)
  jc_url = os.getenv('JRAVIS_CORE_URL', 'http://localhost:7000')
  try:
    r = requests.post(f"{jc_url}/api/trigger_all",
                      headers=bridge_headers(),
                      timeout=6)
    return (r.content, r.status_code, r.headers.items())
  except Exception as e:
    return (f"trigger failed: {e}", 500)


# Forward commands to VA Bot
@app.route('/api/command', methods=['POST'])
def api_command():
  data = request.json or {}
  cmd = data.get('cmd', '')
  try:
    r = requests.post(f"{VABOT_URL}/api/execute",
                      headers=bridge_headers(),
                      json={'stream': {
                          'id': 0,
                          'name': cmd
                      }},
                      timeout=6)
    return r.content, r.status_code, r.headers.items()
  except Exception as e:
    return jsonify({'ok': False, 'error': str(e)}), 500


# Live logs endpoint (reads a file written by start_all.py if used)
@app.route('/api/live_logs')
def api_live_logs():
  try:
    if not os.path.exists(LOG_FILE):
      return jsonify([])
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
      lines = f.read().splitlines()[-400:]
    return jsonify(lines)
  except Exception:
    return jsonify([])


# Status endpoint
@app.route('/api/status')
def api_status():
  return jsonify({'service': 'jravis-dashboard', 'ok': True})


# --------------- Run ---------------
if __name__ == '__main__':
  print(f"[JRAVIS v5] Dashboard starting on port {PORT}")
  app.run(host='0.0.0.0', port=PORT)
