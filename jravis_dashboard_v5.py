"""
JRAVIS Dashboard v5 — Unified Deploy File
This single file supports two deployment modes controlled by the environment variable
  DEPLOY_TARGET = 'replit' | 'production'

- Replit mode: friendly to Replit/Nix quirks (prints pip-downgrade hint). Uses local storage (reports/, static/)
- Production mode: tuned for running behind Gunicorn (cleaner logs)

Features:
- Login (user: Boss) + hidden password via JRAVIS_PASSWORD env var
- Auto-logout after 10 minutes inactivity
- Phase tabs (editable), streams, progress bars
- Dhruvayu chat with optional OpenAI fallback (OPENAI_API_KEY)
- Daily (10:00 IST) & Weekly (Sun 00:00 UTC) reports; optional PDF (reportlab) and optional SMTP email
- Chart.js + Leaflet map + static/logo.png

How to run (Replit):
  1) In Replit shell: pip install --upgrade pip==24.2
  2) pip install flask python-dotenv reportlab openai
  3) Set envs in Replit: JRAVIS_PASSWORD, SECRET_KEY, optionally OPENAI_API_KEY, SMTP_*
  4) Run: python jravis_dashboard_v5.py

How to run (Production):
  pip install -r requirements.txt  # flask, python-dotenv, reportlab(optional), openai(optional)
  export DEPLOY_TARGET=production
  gunicorn jravis_dashboard_v5:app --bind 0.0.0.0:$PORT

Put logo at static/logo.png
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string, session, redirect, url_for, flash
import os
import json
import threading
import time
from datetime import datetime, timedelta, timezone
import uuid
import smtplib
from email.message import EmailMessage
from zoneinfo import ZoneInfo
import atexit

# Optional libraries
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

OPENAI_AVAILABLE = False
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if OPENAI_API_KEY:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        OPENAI_AVAILABLE = True
    except Exception:
        OPENAI_AVAILABLE = False

# Config
APP_DIR = os.path.dirname(__file__)
REPORTS_DIR = os.path.join(APP_DIR, 'reports')
STATIC_DIR = os.path.join(APP_DIR, 'static')
for d in (REPORTS_DIR, STATIC_DIR):
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

DEPLOY_TARGET = os.environ.get('DEPLOY_TARGET', 'replit')  # 'replit' or 'production'
JRAVIS_PASSWORD = os.environ.get('JRAVIS_PASSWORD', 'bosspass')
USERNAME = 'Boss'
SECRET_KEY = os.environ.get('SECRET_KEY', 'change_me')
REPORT_EMAIL = os.environ.get('REPORT_EMAIL')

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.secret_key = SECRET_KEY

# State
STATE_FILE = os.path.join(APP_DIR, 'jravis_state.json')
state_lock = threading.Lock()

def default_state():
    return {
        'phases': {
            '1': {
                'name': 'Phase 1 (Fast Kickstart)',
                'streams': [
                    {'name': 'Elina Instagram Reels', 'last_run': '', 'status': 'OK', 'amount_today': 0},
                    {'name': 'Printify POD Store', 'last_run': '', 'status': 'OK', 'amount_today': 0},
                    {'name': 'Messty AI Store', 'last_run': '', 'status': 'RUNNING', 'amount_today': 0}
                ],
                'notes': 'Activate 3 fastest streams and monitor daily.'
            },
            '2': {'name': 'Phase 2 (Scale & Automate)', 'streams': [], 'notes': 'Automate operational flows.'},
            '3': {'name': 'Phase 3 (Passive Systems)', 'streams': [], 'notes': 'Fully passive, legal, and automated.'}
        },
        'chat_history': [],
        'reports': [],
        'target_monthly': 150000,
        'monthly_earned': 0,
        'daily_earned': 0,
        'status': {'brain': 'ACTIVE', 'last_loop': '', 'api_ok': True}
    }


def load_state():
    try:
        with state_lock:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
    except Exception:
        pass
    return default_state()


def save_state(s=None):
    try:
        with state_lock:
            if s is None:
                s = app_state
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(s, f, indent=2, ensure_ascii=False)
    except Exception as e:
        app.logger.exception('Failed saving state: %s', e)

app_state = load_state()

# Timezones
IST = ZoneInfo('Asia/Kolkata')
UTC = timezone.utc

# Report scheduler settings
REPORT_CHECK_INTERVAL = 30  # seconds between checks

# Authentication helpers
@app.before_request
def auto_logout_check():
    # Allow static and login endpoints
    if request.endpoint in ('static', 'login', 'do_login'):
        return
    last = session.get('last_active')
    now_ts = datetime.now(UTC).timestamp()
    if last and (now_ts - float(last) > 10 * 60):
        session.clear()
        flash('Logged out due to inactivity', 'info')
        return redirect(url_for('login'))
    if 'user' in session:
        session['last_active'] = str(now_ts)

def require_login(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*a, **kw):
        if 'user' not in session:
            return redirect(url_for('login'))
        return func(*a, **kw)
    return wrapper

# Login routes
@app.route('/login', methods=['GET'])
def login():
    html = r"""
<!doctype html>
<html>
<head><meta name="viewport" content="width=device-width,initial-scale=1"><title>JRAVIS Login</title>
<style>body{font-family:Inter,Arial;background:#071021;color:#e6f0fb;display:flex;align-items:center;justify-content:center;height:100vh}
.box{background:rgba(255,255,255,0.03);padding:28px;border-radius:12px;backdrop-filter:blur(6px);width:360px}
input{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:#fff}
button{width:100%;padding:10px;border-radius:8px;border:none;background:#0b72ff;color:white}
.logo{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.logo img{height:44px}
</style></head>
<body>
<div class="box">
  <div class="logo"><img src="/static/logo.png" alt="logo" onerror="this.style.display='none'"><div><strong>JRAVIS</strong><div style="font-size:12px;color:#9fb3d9">Mission 2040</div></div></div>
  <form method="post" action="/do_login">
    <input name="username" value="Boss" readonly />
    <input name="password" type="password" placeholder="Password" />
    <button type="submit">Login</button>
  </form>
</div>
</body>
</html>
    """
    return render_template_string(html)

@app.route('/do_login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == USERNAME and password == JRAVIS_PASSWORD:
        session['user'] = username
        session['last_active'] = str(datetime.now(UTC).timestamp())
        return redirect(url_for('index'))
    flash('Invalid credentials', 'error')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Reporting & email

def make_text_report(now, trigger_reason='scheduled'):
    filename = now.strftime('%Y-%m-%d_%H-%M-%S_summary.txt')
    filepath = os.path.join(REPORTS_DIR, filename)
    with state_lock:
        phases = app_state.get('phases', {})
        chat_history = app_state.get('chat_history', [])[-50:]
        monthly = app_state.get('monthly_earned', 0)
        daily = app_state.get('daily_earned', 0)

    lines = []
    lines.append('JRAVIS Summary Report')
    lines.append('Generated: ' + now.isoformat())
    lines.append('Trigger: ' + trigger_reason)
    lines.append('
--- Phases ---')
    for pid, pdata in phases.items():
        lines.append(f"Phase {pid}: {pdata.get('name')}")
        for s in pdata.get('streams', []):
            lines.append(f"  - {s.get('name')} | last: {s.get('last_run')} | status: {s.get('status')} | amount: {s.get('amount_today')}")
    lines.append('
--- Totals ---')
    lines.append(f'Monthly earned: {monthly}')
    lines.append(f'Daily earned: {daily}')
    lines.append('
--- Recent Chat ---')
    for c in chat_history:
        lines.append(f"[{c.get('ts')}] {c.get('who')}: {c.get('text')}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('
'.join(lines))

    rec = {'id': str(uuid.uuid4()), 'filename': filename, 'path': filepath, 'generated_at': now.isoformat(), 'trigger': trigger_reason}
    with state_lock:
        app_state.setdefault('reports', []).append(rec)
        save_state()
    return rec


def make_pdf_report(now, text_path, title_override=None):
    if not REPORTLAB_AVAILABLE:
        return None
    pdf_name = now.strftime('%Y-%m-%d_%H-%M-%S_summary.pdf')
    pdf_path = os.path.join(REPORTS_DIR, pdf_name)
    try:
        c = canvas.Canvas(pdf_path, pagesize=letter)
        with open(text_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        y = 750
        if title_override:
            c.setFont('Helvetica-Bold', 14)
            c.drawString(40, y, title_override)
            y -= 24
        c.setFont('Helvetica', 10)
        for line in lines:
            c.drawString(40, y, line.strip())
            y -= 12
            if y < 40:
                c.showPage(); y = 750
        c.save()
        return pdf_path
    except Exception:
        app.logger.exception('PDF creation failed')
        return None


def send_email(to_email, subject, body, attachments=None):
    smtp_host = os.environ.get('SMTP_HOST')
    if not smtp_host:
        app.logger.info('SMTP not configured, skipping email send')
        return False
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    msg = EmailMessage()
    msg['From'] = smtp_user or 'jravis@localhost'
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)
    for p in (attachments or []):
        try:
            with open(p, 'rb') as fh:
                data = fh.read()
            msg.add_attachment(data, maintype='application', subtype='octet-stream', filename=os.path.basename(p))
        except Exception:
            app.logger.exception('Failed attaching %s', p)
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            if smtp_user and smtp_pass:
                s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception:
        app.logger.exception('Email send failed')
        return False

# Scheduler
stop_event = threading.Event()

def report_scheduler(stop_event):
    # checks every REPORT_CHECK_INTERVAL seconds for daily 10:00 IST and weekly Sunday 00:00 UTC
    last_daily = None
    last_weekly = None
    while not stop_event.is_set():
        now_utc = datetime.now(UTC)
        now_ist = now_utc.astimezone(IST)
        # Daily at 10:00 IST (run once per day)
        if now_ist.hour == 10 and now_ist.minute == 0:
            day_key = now_ist.date().isoformat()
            if day_key != last_daily:
                try:
                    rec = make_text_report(now_utc, trigger_reason='daily_10_IST')
                    if REPORTLAB_AVAILABLE:
                        pdf = make_pdf_report(now_utc, rec['path'])
                    if REPORT_EMAIL:
                        attachments = [pdf] if (REPORTLAB_AVAILABLE and pdf) else [rec['path']]
                        send_email(REPORT_EMAIL, 'JRAVIS Daily Report', 'Attached daily report', attachments=attachments)
                except Exception:
                    app.logger.exception('Daily report error')
                last_daily = day_key
        # Weekly Sunday 00:00 UTC
        if now_utc.weekday() == 6 and now_utc.hour == 0 and now_utc.minute == 0:
            week_key = now_utc.isocalendar()[1]
            if week_key != last_weekly:
                try:
                    rec = make_text_report(now_utc, trigger_reason='weekly_sun_00_UTC')
                    if REPORTLAB_AVAILABLE:
                        pdf = make_pdf_report(now_utc, rec['path'], title_override='Weekly JRAVIS Summary')
                    if REPORT_EMAIL:
                        attachments = [pdf] if (REPORTLAB_AVAILABLE and pdf) else [rec['path']]
                        send_email(REPORT_EMAIL, 'JRAVIS Weekly Report', 'Attached weekly report', attachments=attachments)
                except Exception:
                    app.logger.exception('Weekly report error')
                last_weekly = week_key
        for _ in range(int(REPORT_CHECK_INTERVAL)):
            if stop_event.is_set():
                break
            time.sleep(1)

worker_thread = threading.Thread(target=report_scheduler, args=(stop_event,), daemon=True)
worker_thread.start()

@atexit.register
def _shutdown():
    stop_event.set()
    save_state()

# API & UI
@app.route('/api/state')
@require_login
def api_state():
    return jsonify(app_state)

@app.route('/api/phase/<phase_id>', methods=['POST'])
@require_login
def api_update_phase(phase_id):
    payload = request.get_json() or {}
    with state_lock:
        phases = app_state.setdefault('phases', {})
        if phase_id not in phases:
            phases[phase_id] = {'name': payload.get('name', f'Phase {phase_id}'), 'streams': [], 'notes': ''}
        phases[phase_id]['name'] = payload.get('name', phases[phase_id].get('name'))
        phases[phase_id]['notes'] = payload.get('notes', phases[phase_id].get('notes'))
        phases[phase_id]['streams'] = payload.get('streams', phases[phase_id].get('streams', []))
        save_state()
    return jsonify({'ok': True, 'phase': phases[phase_id]})

@app.route('/api/chat', methods=['POST'])
@require_login
def api_chat():
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'empty'}), 400
    now = datetime.now(UTC).isoformat()
    msg = {'who': 'Boss', 'text': text, 'ts': now}
    with state_lock:
        app_state.setdefault('chat_history', []).append(msg)
        reply_text = f'Logged: "{text}". I will prepare next steps.'
        if OPENAI_AVAILABLE:
            try:
                resp = openai.ChatCompletion.create(model='gpt-4o-mini', messages=[{'role':'user','content':text}], max_tokens=150)
                reply_text = resp.choices[0].message.content.strip()
            except Exception:
                app.logger.exception('OpenAI reply failed')
        reply = {'who': 'Dhruvayu', 'text': reply_text, 'ts': datetime.now(UTC).isoformat()}
        app_state['chat_history'].append(reply)
        save_state()
    return jsonify({'ok': True})

@app.route('/api/generate_report', methods=['POST'])
@require_login
def api_generate_report():
    rec = make_text_report(datetime.now(UTC), trigger_reason='manual')
    return jsonify(rec)

@app.route('/reports/<path:filename>')
@require_login
def serve_report(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)

@app.route('/api/shutdown', methods=['POST'])
@require_login
def api_shutdown():
    stop_event.set()
    save_state()
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
        return jsonify({'ok': True, 'msg': 'shutting down'})
    else:
        return jsonify({'error': 'not running with werkzeug'}), 500

# Main UI
@app.route('/')
@require_login
def index():
    html = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>JRAVIS Dashboard v5 Ultimate</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root{--bg:#071021;--card:rgba(255,255,255,0.04);--glass:rgba(255,255,255,0.03);--accent:#0b72ff;--muted:#93a6c4}
    body{margin:0;font-family:Inter,Arial,system-ui;background:linear-gradient(180deg,#031023 0%, #07121d 100%);color:#e6f0fb}
    header{display:flex;align-items:center;justify-content:space-between;padding:14px 20px}
    .brand{display:flex;align-items:center;gap:12px}
    .logo img{height:48px}
    .top-controls{display:flex;gap:10px;align-items:center}
    .btn{background:var(--accent);border:none;padding:8px 12px;border-radius:10px;color:white;cursor:pointer}
    .container{max-width:1200px;margin:10px auto;padding:12px}
    .grid{display:grid;grid-template-columns:1fr 420px;gap:16px}
    .card{background:var(--card);padding:14px;border-radius:12px;box-shadow:0 8px 20px rgba(2,6,23,0.6)}
    .tabs{display:flex;gap:8px}
    .tab{padding:8px 10px;border-radius:8px;background:transparent;border:1px solid rgba(255,255,255,0.03);cursor:pointer}
    .tab.active{background:linear-gradient(180deg, rgba(11,114,255,0.14), rgba(11,114,255,0.06));box-shadow:inset 0 -2px 0 rgba(11,114,255,0.25)}
    table{width:100%;border-collapse:collapse;color:#dfefff}
    td,th{padding:8px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.02)}
    .progress{height:12px;background:rgba(255,255,255,0.04);border-radius:8px;overflow:hidden}
    .progress > i{display:block;height:100%}
    #map{height:220px;border-radius:8px}

    @media(max-width:980px){.grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
  <header>
    <div class="brand"><div class="logo"><img src="/static/logo.png" onerror="this.style.display='none'"></div><div><strong>JRAVIS</strong><div style="font-size:12px;color:var(--muted)">Phase 1 Global System Status</div></div></div>
    <div class="top-controls">
      <div style="text-align:right;color:var(--muted);font-size:13px">Status: <strong id="brainStatus">ACTIVE</strong><br/><span id="lastLoop">Last Loop: --</span></div>
      <button class="btn" onclick="location.href='/logout'">Logout</button>
    </div>
  </header>
  <div class="container">
    <div class="grid">
      <div>
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-weight:700">Phases</div>
            <div class="tabs" id="phaseTabs"></div>
          </div>
          <div id="phaseContent"></div>
        </div>

        <div style="height:12px"></div>

        <div class="card" style="margin-top:12px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-weight:700">Charts & Map</div>
            <div style="font-size:12px;color:var(--muted)">Live</div>
          </div>
          <canvas id="incomeChart" height="120"></canvas>
          <div style="height:12px"></div>
          <div id="map"></div>
        </div>
      </div>

      <div>
        <div class="card">
          <div style="font-weight:700;margin-bottom:8px">Summary</div>
          <div id="summaryTop"></div>
          <div style="height:12px"></div>
          <div style="font-weight:700;margin-bottom:8px">Recent Reports</div>
          <div id="reportsList">Loading...</div>
        </div>

        <div style="height:12px"></div>

        <div class="card">
          <div style="font-weight:700;margin-bottom:8px">Dhruvayu Chat</div>
          <div id="chatBox" style="height:270px;overflow:auto;padding:6px;background:rgba(0,0,0,0.15);border-radius:8px;color:#dff;">
          </div>
          <div style="display:flex;gap:8px;margin-top:8px">
            <input id="chatInput" placeholder="How can I assist?" style="flex:1;padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:#fff" />
            <button class="btn" onclick="sendChat()">Send</button>
          </div>
        </div>

      </div>
    </div>
  </div>

<script>
let activePhase = '1';
async function api(path, opts){ const r = await fetch(path, opts); if(r.headers.get('content-type')?.includes('application/json')) return r.json(); return r.text(); }
function renderPhaseTabs(phases){ const el = document.getElementById('phaseTabs'); el.innerHTML=''; Object.keys(phases).forEach(pid=>{ const btn = document.createElement('button'); btn.className='tab'+(pid===activePhase?' active':''); btn.textContent='P'+pid; btn.onclick=()=>{ activePhase=pid; renderPhase(phases[pid], pid); renderPhaseTabs(phases); }; el.appendChild(btn); }); }
function renderPhase(data, pid){ const c = document.getElementById('phaseContent'); c.innerHTML=''; const title = document.createElement('div'); title.style.fontWeight='700'; title.textContent = data.name; c.appendChild(title); const tbl = document.createElement('table'); const thead = document.createElement('thead'); thead.innerHTML='<tr><th>#</th><th>Stream</th><th>Last Run</th><th>Status</th><th>Amount</th></tr>'; tbl.appendChild(thead); const tbody = document.createElement('tbody'); (data.streams||[]).forEach((s,i)=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td>${i+1}</td><td>${s.name||s}</td><td>${s.last_run||'--'}</td><td>${s.status||''}</td><td>${s.amount_today||0}</td>`; tbody.appendChild(tr); }); tbl.appendChild(tbody); c.appendChild(tbl); const edit = document.createElement('button'); edit.className='btn'; edit.style.marginTop='8px'; edit.textContent='Edit Phase'; edit.onclick=()=>editPhase(pid,data); c.appendChild(edit); }
function editPhase(pid,data){ const newName = prompt('Phase name', data.name)||data.name; const newNotes = prompt('Phase notes', data.notes||'')||data.notes||''; const streamsText = (data.streams||[]).map(s=>s.name||s).join(', '); const newStreams = prompt('Comma-separated stream names', streamsText)||streamsText; const payload = {name:newName,notes:newNotes,streams:newStreams.split(',').map(s=>({name:s.trim(),last_run:'',status:'OK',amount_today:0}))}; fetch('/api/phase/'+pid, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(()=>loadState()); }
async function loadState(){ const s = await api('/api/state'); renderPhaseTabs(s.phases); renderPhase(s.phases[activePhase],activePhase); renderSummary(s); renderReports(s.reports||[]); renderChat(s.chat_history||[]); }
function renderSummary(s){ document.getElementById('brainStatus').textContent = s.status?.brain || 'OK'; document.getElementById('lastLoop').textContent = 'Last Loop: ' + (s.status?.last_loop||'--'); const out = document.getElementById('summaryTop'); out.innerHTML = `<div>Monthly Target: ₹${s.target_monthly||0}</div><div>Monthly Earned: ₹${s.monthly_earned||0}</div><div>Daily Earned: ₹${s.daily_earned||0}</div><div style="margin-top:8px"><div class="progress"><i style="width:${Math.min(100,((s.monthly_earned||0)/ (s.target_monthly||1))*100)}%;background:linear-gradient(90deg,#0b72ff,#00d4ff)"></i></div></div>` }
function renderReports(reports){ const el = document.getElementById('reportsList'); el.innerHTML=''; (reports||[]).slice().reverse().forEach(r=>{ const a=document.createElement('a'); a.href='/reports/'+r.filename; a.textContent=r.filename; a.style.display='block'; el.appendChild(a); }); }
function renderChat(messages){ const box=document.getElementById('chatBox'); box.innerHTML=''; (messages||[]).forEach(m=>{ const d=document.createElement('div'); d.style.margin='6px 0'; d.innerHTML=`<strong>${m.who}</strong> <span style='color:#99b3d6;font-size:12px'>${new Date(m.ts).toLocaleString()}</span><div>${m.text}</div>`; box.appendChild(d); }); box.scrollTop=box.scrollHeight; }
async function sendChat(){ const input=document.getElementById('chatInput'); const text=input.value.trim(); if(!text) return; input.value=''; await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})}); await loadState(); }
let incomeChart=null; function initChart(){ const ctx=document.getElementById('incomeChart').getContext('2d'); incomeChart = new Chart(ctx, {type:'line',data:{labels:[],datasets:[{label:'Daily',data:[],fill:true}]},options:{responsive:true}}); }
function initMap(){ try{ const map = L.map('map').setView([20,0],2); L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:8}).addTo(map); L.marker([20,77]).addTo(map).bindPopup('HQ').openPopup(); }catch(e){console.warn('Leaflet init failed',e);} }
window.onload = function(){ initChart(); initMap(); loadState(); setInterval(loadState,8000); }
</script>
</body>
</html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    if DEPLOY_TARGET == 'replit':
        print('Running in Replit mode. If you see xml/pyexpat errors, downgrade pip: pip install --upgrade pip==24.2')
    else:
        print('Running in production mode. Use gunicorn for best results.')
    print('Starting JRAVIS Dashboard v5 Ultimate on port 10000')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=(DEPLOY_TARGET=='replit'))
