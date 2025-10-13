# -*- coding: utf-8 -*-
"""
JRAVIS Dashboard v5
Single-file Flask app to serve a simple Mission 2040 dashboard.
Features:
- / -> Dashboard HTML
- /api/live_progress -> JSON progress data
- /api/live_logs -> list of log lines
- /api/command -> POST to send a command (returns JSON)
- /api/trigger -> POST to trigger all streams (returns text)
- Background scheduler (APScheduler) to simulate progress updates
- Optional LOCK_CODE via environment variable (simple protection)

Dependencies (from requirements): Flask, APScheduler, PyYAML (optional), gunicorn

This file is intentionally self-contained and safe to deploy.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from threading import Lock
from textwrap import dedent

from flask import Flask, request, jsonify, make_response, abort
from apscheduler.schedulers.background import BackgroundScheduler

# ---------- Configuration ----------
APP_NAME = "JRAVIS Dashboard v5"
LOCK_CODE = os.getenv("LOCK_CODE",
                      "")  # if set, APIs requiring lock will validate
PORT = int(os.getenv("PORT", "10000"))

# Simple in-memory state used by endpoints and scheduler
_state = {
    "progress_percent": 0,
    "total_income": 0,
    "daily_income": 0,
    "last_loop": None,
    "logs": [],
    "streams": [],
}
_state_lock = Lock()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("jravis")

# ---------- Flask app ----------
app = Flask(__name__)


# Helper: require lock code if set
def check_lock(req):
    if not LOCK_CODE:
        return True
    # Accept lock via header or JSON/body param
    hdr = req.headers.get("X-LOCK-CODE")
    if hdr and hdr == LOCK_CODE:
        return True
    try:
        j = req.get_json(silent=True) or {}
        if j.get("lock_code") == LOCK_CODE:
            return True
    except Exception:
        pass
    return False


# Helper: append log line
def append_log(line: str):
    with _state_lock:
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{t}] {line}"
        _state["logs"].append(entry)
        # Keep logs manageable
        if len(_state["logs"]) > 1000:
            _state["logs"] = _state["logs"][-1000:]
        logger.info(line)


# Simulate progress update (called by scheduler)
def scheduler_tick():
    with _state_lock:
        # increment progress slowly, and simulate income
        pct = _state.get("progress_percent", 0)
        if pct < 100:
            pct = min(100, pct + 1)
            _state["progress_percent"] = pct
            inc = 1000 + int(pct * 10)
            _state["daily_income"] = _state.get("daily_income", 0) + inc
            _state["total_income"] = _state.get("total_income", 0) + inc
            _state["last_loop"] = datetime.now().isoformat()
            append_log(f"Auto tick: progress {pct}%, +{inc} income")
        else:
            append_log("Auto tick: progress at 100% — idle")


# Start background scheduler
sched = BackgroundScheduler()
sched.add_job(scheduler_tick, "interval", seconds=10, id="progress_tick")
sched.start()
append_log("Scheduler started")


# ---------- Endpoints ----------
@app.get("/")
def index():
    # Serve an inline HTML dashboard (simple, no templates)
    html = dedent('''
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>JRAVIS v5 - Mission 2040</title>
      <style>
        body{font-family:system-ui,Arial,Helvetica,sans-serif;background:#0d1117;color:#c9d1d9;margin:0;padding:0}
        .container{max-width:1100px;margin:20px auto;padding:18px}
        .card{background:#0b1220;border-radius:8px;padding:14px;margin-bottom:12px;box-shadow:0 6px 18px rgba(0,0,0,0.4)}
        .row{display:flex;gap:12px;align-items:center}
        .progress{background:#17202a;border-radius:6px;height:26px;overflow:hidden}
        .progress > .bar{height:100%;background:linear-gradient(90deg,#6ee7b7,#3b82f6);width:0}
        .muted{color:#8b949e;font-size:0.9rem}
        #logbox{height:220px;overflow:auto;background:#071018;padding:10px;border-radius:6px}
        input,button{padding:8px;border-radius:6px;border:1px solid #233244;background:#071722;color:#e6eef8}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>JRAVIS Dashboard v5 — Mission 2040</h2>
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div class="muted">Progress</div>
              <div class="progress" aria-hidden>
                <div id="progress-bar" class="bar" style="width:0%"></div>
              </div>
              <div id="progress-text" class="muted">0%</div>
            </div>
            <div style="text-align:right">
              <div class="muted">Monthly</div>
              <div id="monthly">INR 0</div>
              <div class="muted">Daily</div>
              <div id="daily">INR 0</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div style="flex:1;margin-right:12px">
              <div class="muted">Logs</div>
              <div id="logbox"></div>
            </div>
            <div style="width:280px">
              <div class="muted">Send Command</div>
              <input id="chat-input" placeholder="Type command (e.g. 'phase 1' or 'trigger all')" style="width:100%" />
              <div style="height:8px"></div>
              <button onclick="sendCmd()">Send</button>
              <button onclick="triggerAll()" style="margin-left:6px">Trigger All</button>
            </div>
          </div>
        </div>

        <div class="card muted">Last loop: <span id="last-loop">--</span></div>
      </div>

    <script>
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
      }catch(e){console.log('progress fetch failed', e)}
    }

    async function refreshLogs(){
      try{
        const res = await fetch('/api/live_logs');
        const lines = await res.json();
        const box = document.getElementById('logbox');
        box.innerHTML = lines.map(l => '<div>'+l.replace(/</g,'&lt;')+'</div>').join('');
        box.scrollTop = box.scrollHeight;
      }catch(e){console.log('log fetch failed', e)}
    }

    async function sendCmd(){
      const v = document.getElementById('chat-input').value.trim();
      if(!v) return;
      if(v.toLowerCase().startsWith('phase')){
        // client-side helper: just show phase
        alert('Phase switch: ' + v);
        document.getElementById('chat-input').value = '';
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
      }catch(e){alert('send failed');}
      document.getElementById('chat-input').value = '';
    }

    async function triggerAll(){
      try{
        const res = await fetch('/api/trigger', {method:'POST'});
        const txt = await res.text();
        alert('Triggered: '+txt);
      }catch(e){alert('Trigger failed');}
    }

    // initial
    updateProgress();
    refreshLogs();
    setInterval(updateProgress, 15000);
    setInterval(refreshLogs, 5000);
    </script>
    </body>
    </html>
    ''')
    return make_response(html)


@app.get('/api/live_progress')
def api_live_progress():
    with _state_lock:
        data = {
            "progress_percent": _state.get("progress_percent", 0),
            "total_income": _state.get("total_income", 0),
            "daily_income": _state.get("daily_income", 0),
            "last_loop": _state.get("last_loop", None),
        }
    return jsonify(data)


@app.get('/api/live_logs')
def api_live_logs():
    # returns list of recent log lines
    with _state_lock:
        logs = list(_state.get('logs', [])[-200:])
    return jsonify(logs)


@app.post('/api/command')
def api_command():
    if not check_lock(request):
        return make_response('Locked', 403)
    j = request.get_json(silent=True) or {}
    cmd = j.get('cmd') or ''
    if not cmd:
        return jsonify({'status': 'error', 'message': 'no cmd provided'})
    append_log(f"Manual command: {cmd}")
    # handle a couple of commands locally
    if cmd.lower().startswith('add '):
        try:
            val = int(cmd.split()[1])
            with _state_lock:
                _state['total_income'] = _state.get('total_income', 0) + val
            return jsonify({'status': 'ok', 'added': val})
        except Exception:
            return jsonify({'status': 'error', 'message': 'invalid add value'})
    return jsonify({'status': 'ok', 'cmd': cmd})


@app.post('/api/trigger')
def api_trigger():
    if not check_lock(request):
        return make_response('Locked', 403)
    # Simulate triggering streams: we'll append a log and bump progress slightly
    append_log('Trigger: manual trigger requested')
    with _state_lock:
        _state['progress_percent'] = min(100,
                                         _state.get('progress_percent', 0) + 2)
        _state['total_income'] = _state.get('total_income', 0) + 5000
    return make_response('OK')


# Graceful shutdown of scheduler on exit
import atexit


@atexit.register
def shutdown():
    try:
        sched.shutdown(wait=False)
    except Exception:
        pass


# Allow running with `python jravis_dashboard_v5.py` for local testing
if __name__ == '__main__':
    logger.info('Starting JRAVIS Dashboard (local)')
    # development server only
    app.run(host='0.0.0.0', port=PORT, debug=False)
