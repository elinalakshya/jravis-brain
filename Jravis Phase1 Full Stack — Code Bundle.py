# JRAVIS PHASE1 FULL STACK
# This single file contains all components as separate sections. Copy each section into its own file
# before deploying to Render.

# -----------------------------------------------------------------------------
# FILE: streams_config.json
# (Save as streams_config.json)
# -----------------------------------------------------------------------------
# {
#   "phase1": [
#     {"id":1, "name":"Elina Instagram Reels", "target":"₹15K–₹50K"},
#     {"id":2, "name":"Printify POD Store", "target":"₹20K–₹2L+"},
#     {"id":3, "name":"Meshy AI Store", "target":"₹10K–₹75K"},
#     {"id":4, "name":"Cad Crowd Auto Work", "target":"₹30K–₹1.2L"},
#     {"id":5, "name":"Fiverr AI Gig Automation", "target":"₹25K–₹1.5L"},
#     {"id":6, "name":"YouTube Automation", "target":"₹50K–₹2L+"},
#     {"id":7, "name":"Stock Image/Video Sales", "target":"₹20K–₹80K"},
#     {"id":8, "name":"AI Book Publishing (KDP)", "target":"₹30K–₹1.5L"},
#     {"id":9, "name":"Shopify Digital Products", "target":"₹50K–₹2.5L"},
#     {"id":10, "name":"Stationery Export", "target":"₹50K–₹2L"}
#   ],
#   "phase2": [
#     {"id":11, "name":"Template/Theme Marketplace", "target":"₹40K–₹2L"},
#     {"id":12, "name":"Course Resell Automation", "target":"₹50K–₹2L"},
#     {"id":13, "name":"Printables Store", "target":"₹25K–₹80K"},
#     {"id":14, "name":"Affiliate Marketing Automation", "target":"₹50K–₹2.5L"},
#     {"id":15, "name":"AI SaaS Micro-Tools", "target":"₹50K–₹3L"},
#     {"id":16, "name":"Newsletter + Ads Automation", "target":"₹30K–₹1L"},
#     {"id":17, "name":"Subscription Box", "target":"₹40K–₹1.5L"},
#     {"id":18, "name":"Gaming Assets Store", "target":"₹30K–₹1.2L"},
#     {"id":19, "name":"Webflow Template Sales", "target":"₹25K–₹75K"},
#     {"id":20, "name":"Skillshare Course Automation", "target":"₹25K–₹80K"}
#   ],
#   "phase3": [
#     {"id":21, "name":"SaaS Reseller Bots", "target":"₹75K–₹3L"},
#     {"id":22, "name":"Voiceover/AI Dubbing Automation", "target":"₹30K–₹1L"},
#     {"id":23, "name":"Music/Beats Licensing", "target":"₹30K–₹1L"},
#     {"id":24, "name":"Web Automation Scripts Marketplace", "target":"₹40K–₹1.5L"},
#     {"id":25, "name":"AI Plugin/Extension Sales", "target":"₹50K–₹2.5L"},
#     {"id":26, "name":"Educational Worksheets Store", "target":"₹25K–₹1L"},
#     {"id":27, "name":"Digital/Virtual Events Automation", "target":"₹50K–₹2L"},
#     {"id":28, "name":"AI Resume/CV Automation", "target":"₹25K–₹1L"},
#     {"id":29, "name":"Crypto Microtask Automation", "target":"₹20K–₹80K"},
#     {"id":30, "name":"Global API Marketplace", "target":"₹75K–₹3L"}
#   ]
# }

# -----------------------------------------------------------------------------
# FILE: mission_bridge.py
# Simple Flask bridge that stores shared state in-memory (can be replaced with DB)
# -----------------------------------------------------------------------------
from flask import Flask, request, jsonify
import os, threading, time

app = Flask(__name__)
SHARED_KEY = os.getenv('SHARED_KEY', 'JRAVIS_MASTER_KEY')

# Simple in-memory store
_store = {
    'streams': {},  # stream_id -> last_run/status/result
    'income': {
        'total_income': 0,
        'progress_percent': 0,
        'target': 40000000,
        'next_report_time': 'Daily 10:00 AM IST'
    }
}


# helper auth
def _auth_ok(req):
    auth = req.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth.split(' ', 1)[1] == SHARED_KEY
    return False


@app.route('/api/status')
def status():
    return jsonify({'ok': True, 'service': 'mission-bridge'})


@app.route('/api/streams', methods=['GET', 'POST'])
def streams():
    if not _auth_ok(request):
        return ('Unauthorized', 401)
    if request.method == 'GET':
        return jsonify(_store['streams'])
    else:
        data = request.json or {}
        sid = data.get('id')
        if sid is None:
            return ('Bad Request', 400)
        _store['streams'][sid] = data
        return jsonify({'ok': True})


@app.route('/api/income', methods=['GET', 'POST'])
def income():
    if not _auth_ok(request):
        return ('Unauthorized', 401)
    if request.method == 'GET':
        return jsonify(_store['income'])
    else:
        _store['income'].update(request.json or {})
        return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6000')))

# -----------------------------------------------------------------------------
# FILE: jravis_core_v1.py
# Brain: reads streams_config, triggers decisions and posts to mission-bridge
# -----------------------------------------------------------------------------
from flask import Flask, request, jsonify
import os, json, time, threading, requests
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
SHARED_KEY = os.getenv('SHARED_KEY', 'JRAVIS_MASTER_KEY')
BRIDGE = os.getenv('BRIDGE_URL', 'http://localhost:6000')
STREAMS_FILE = os.getenv('STREAMS_FILE', 'streams_config.json')

# load streams
with open(STREAMS_FILE, 'r', encoding='utf-8') as f:
    STREAMS_CFG = json.load(f)


# auth helper
def headers():
    return {
        'Authorization': f'Bearer {SHARED_KEY}',
        'Content-Type': 'application/json'
    }


@app.route('/api/status')
def api_status():
    return jsonify({'service': 'jravis-core', 'ok': True})


@app.route('/api/phase/<int:phase_id>')
def api_phase(phase_id):
    key = f'phase{phase_id}'
    return jsonify(STREAMS_CFG.get(key, []))


def run_loop_once():
    # simplistic loop: for phase1 only, post a small test earning
    streams = STREAMS_CFG.get('phase1', [])
    for s in streams:
        payload = {
            'id': s['id'],
            'name': s['name'],
            'last_run': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'OK',
            'result': 0
        }
        try:
            requests.post(f"{BRIDGE}/api/streams",
                          json=payload,
                          headers=headers(),
                          timeout=10)
        except Exception as e:
            print('bridge write error', e)


@app.route('/api/trigger_all', methods=['POST'])
def trigger_all():
    if request.headers.get('Authorization', '').split(' ')[-1] != SHARED_KEY:
        return ('Unauthorized', 401)
    threading.Thread(target=run_loop_once).start()
    return jsonify({'ok': True})


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_loop_once, 'interval', minutes=30)
    scheduler.start()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '7000')))

# -----------------------------------------------------------------------------
# FILE: vabot_core_v1.py
# Executor: simple endpoints to accept commands and simulate work
# -----------------------------------------------------------------------------
from flask import Flask, request, jsonify
import os, time, threading, requests

app = Flask(__name__)
SHARED_KEY = os.getenv('SHARED_KEY', 'JRAVIS_MASTER_KEY')
BRIDGE = os.getenv('BRIDGE_URL', 'http://localhost:6000')


# auth helper
def headers():
    return {
        'Authorization': f'Bearer {SHARED_KEY}',
        'Content-Type': 'application/json'
    }


@app.route('/api/status')
def status():
    return jsonify({'service': 'vabot-core', 'ok': True})


@app.route('/api/execute', methods=['POST'])
def execute():
    if request.headers.get('Authorization', '').split(' ')[-1] != SHARED_KEY:
        return ('Unauthorized', 401)
    data = request.json or {}
    stream = data.get('stream')

    # simulate async execution
    def work():
        time.sleep(2)
        payload = {
            'id': stream.get('id'),
            'name': stream.get('name'),
            'last_run': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'OK',
            'result': 100
        }
        try:
            requests.post(f"{BRIDGE}/api/streams",
                          json=payload,
                          headers=headers(),
                          timeout=10)
        except Exception as e:
            print('bridge write error', e)

    threading.Thread(target=work).start()
    return jsonify({'ok': True, 'message': 'execution started'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8000')))

# -----------------------------------------------------------------------------
# FILE: jravis_dashboard_v5.py
# Dashboard: simplified dark UI, phase tabs, live progress from bridge
# -----------------------------------------------------------------------------
from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os, requests, json

app = Flask(__name__)
SHARED_KEY = os.getenv('SHARED_KEY', 'JRAVIS_MASTER_KEY')
BRIDGE = os.getenv('BRIDGE_URL', 'http://localhost:6000')

LOGIN_HTML = """<!doctype html><html><head><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>JRAVIS Login</title><style>body{background:#071022;color:#e6eef6;font-family:Inter,Arial,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}.card{background:rgba(255,255,255,0.03);padding:28px;border-radius:12px;width:320px;text-align:center}input[type=password]{width:100%;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.05);background:transparent;color:inherit}button{margin-top:12px;padding:10px 16px;border-radius:8px;border:none;background:linear-gradient(90deg,#00ffff,#00ff7f);color:#042018;font-weight:700;cursor:pointer}.err{color:#ffb4b4;margin-top:8px}.small{color:#9aa7bf;font-size:12px;margin-top:10px}</style></head><body><div class=\"card\"><h2>JRAVIS Secure Access</h2><form method=\"post\" action=\"/login\"><input name=\"code\" type=\"password\" placeholder=\"Enter Lock Code\" required/><button>Unlock</button></form></div></body></html>"""

DASH_HTML = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>JRAVIS v5 — Mission 2040</title>
  <style>
    :root{--bg:#071022;--card:rgba(255,255,255,0.04);--muted:#9aa7bf;--accent1:#00ffff;--accent2:#00ff7f}
    body{margin:0;font-family:Inter,Arial,sans-serif;background:var(--bg);color:#e6eef6}
    header{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.03)}
    .brand{display:flex;align-items:center;gap:12px}
    .brand h1{font-size:18px;margin:0;color:var(--accent1)}
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
    @media(max-width:768px){.grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
<header><div class="brand"><h1>JRAVIS v5 — Mission 2040</h1></div><div><form action="/logout" method="post"><button style="background:transparent;border:1px solid rgba(255,255,255,0.06);padding:8px 10px;border-radius:8px;color:#e6eef6">Logout</button></form></div></header>
<div class="wrap"><div class="grid"><div class="card"><div class="section-title">SYSTEM STATUS</div><div><b>JRAVIS Brain:</b> ACTIVE 🧠</div><div><b>VA Bot Connector:</b> ACTIVE 🤖</div><div><b>Income Bundle:</b> API OK 💰</div><div style="margin-top:10px;">Last Loop: <b>--</b></div><div class="phase-tabs"><button class="active" onclick="showPhase(1)">Phase 1</button><button onclick="showPhase(2)">Phase 2</button><button onclick="showPhase(3)">Phase 3</button></div><table id="phase-table"><tr><th>#</th><th>Stream</th><th>Target</th><th>Status</th><th>Goal</th></tr></table></div><div class="card"><div class="section-title">INCOME → LIVE FEED</div><div class="income-stats"><div>Target: ₹4 Cr</div><div>Progress: 0%</div><div class="progress"><div></div></div><div>Monthly: ₹0</div><div>Daily: ₹0</div><div>Next Report: 10:00 AM Daily | Sunday 12:00 AM Weekly</div></div><div class="section-title" style="margin-top:20px">JRAVIS Assistant</div><div class="chatbox"><input id="chat-input" placeholder="Type a command..."/><button onclick="sendCmd()">Send</button></div></div></div></div>
<script>
async function showPhase(num){
  const tabs = document.querySelectorAll('.phase-tabs button');
  tabs.forEach(t=>t.classList.remove('active'));
  tabs[num-1].classList.add('active');
  const table = document.getElementById('phase-table');
  const res = await fetch('/api/phase/'+num);
  const data = await res.json();
  let html = '<tr><th>#</th><th>Stream</th><th>Target</th><th>Status</th><th>Goal</th></tr>';
  data.forEach(d=>{
    let cls = d.get('status','ACTIVE')=='ACTIVE'?'ok':(d.get('status')=='RUNNING'?'run':'fail');
    html += `<tr><td>${d.id}</td><td>${d.name}</td><td>${d.target}</td><td class="${cls}">${d.get('status','ACTIVE')}</td><td>${d.get('goal','')}</td></tr>`;
  });
  table.innerHTML = html;
}

async function updateProgress(){
  try{
    const res = await fetch('/api/live_progress');
    const data = await res.json();
    document.querySelector('.progress>div').style.width = (data.progress_percent||0)+'%';
    document.querySelector('.income-stats').children[1].innerText = 'Progress: '+(data.progress_percent||0)+'%';
    document.querySelector('.income-stats').children[3].innerText = 'Monthly: ₹'+((data.total_income||0).toLocaleString());
    document.querySelector('.income-stats').children[4].innerText = 'Daily: ₹'+((data.total_income||0).toLocaleString());
  }catch(e){console.log('progress error',e)}
}

async function sendCmd(){
  const v = document.getElementById('chat-input').value.trim();
  if(!v) return;
  // simple local commands
  if(v.toLowerCase().includes('phase')){
    const p = v.match(/\d/)?v.match(/\d/)[0]:1; showPhase(Number(p)); return;
  }
  // send to VA bot
  try{
    const res = await fetch('/api/command', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:v})});
    const j = await res.json(); alert('Sent: '+JSON.stringify(j));
  }catch(e){alert('send failed')}
}

updateProgress(); setInterval(updateProgress,1800000);
showPhase(1);
</script>
</body>
</html>
"""


# Flask routes
@app.route('/')
def root():
    return LOGIN_HTML


@app.route('/dashboard')
def dashboard():
    return render_template_string(DASH_HTML)


@app.route('/api/phase/<int:phase_id>')
def api_phase(phase_id):
    try:
        r = requests.get(f"{BRIDGE}/api/phase/{phase_id}",
                         headers={'Authorization': f'Bearer {SHARED_KEY}'},
                         timeout=5)
        return (r.content, r.status_code, r.headers.items())
    except Exception as e:
        # fallback to local streams file
        with open('streams_config.json', 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return jsonify(cfg.get(f'phase{phase_id}', []))


@app.route('/api/live_progress')
def api_live_progress():
    try:
        r = requests.get(f"{BRIDGE}/api/income",
                         headers={'Authorization': f'Bearer {SHARED_KEY}'},
                         timeout=5)
        return (r.content, r.status_code, r.headers.items())
    except Exception as e:
        return jsonify({
            'total_income': 0,
            'progress_percent': 0,
            'target': 40000000
        })


@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.json or {}
    cmd = data.get('cmd', '')
    # forward to VA bot
    try:
        r = requests.post(os.getenv('VABOT_URL', 'http://localhost:8000') +
                          '/api/execute',
                          headers={'Authorization': f'Bearer {SHARED_KEY}'},
                          json={'stream': {
                              'id': 0,
                              'name': cmd
                          }},
                          timeout=5)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '10000')))
