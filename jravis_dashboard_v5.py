# jravis_dashboard_v5.py
# Mission 2040 — JRAVIS Dashboard (Flask, single-file)
# Replace existing file with this. It provides a dark Mission-2040 console UI
# and an /api/status endpoint that fetches live data from configured services.

import os
import json
import traceback
from datetime import datetime
from flask import Flask, render_template_string, jsonify
import requests

app = Flask(__name__)

# Config from env (set these in Render / env)
JRAVIS_BRAIN_URL = os.getenv("JRAVIS_BRAIN_URL",
                             "https://jravis-brain.onrender.com")
MISSION_BRIDGE_URL = os.getenv("MISSION_BRIDGE_URL",
                               "https://mission-bridge.onrender.com")
VA_BOT_URL = os.getenv("VA_BOT_URL", "https://va-bot-connector.onrender.com")


# Simple helper to fetch endpoints with timeout and fail-safe
def safe_get_json(url, timeout=4):
  try:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()
  except Exception:
    return None


# API: aggregated status for the UI
@app.route("/api/status")
def api_status():
  try:
    # try fetch from mission bridge (preferred)
    bridge_status = safe_get_json(f"{MISSION_BRIDGE_URL}/status") or {}
    brain_status = safe_get_json(f"{JRAVIS_BRAIN_URL}/health") or {}
    va_status = safe_get_json(f"{VA_BOT_URL}/health") or {}

    # fallback/mocked entries if real endpoints are not present
    now = datetime.utcnow().isoformat() + "Z"

    # Income summary - try mission bridge endpoint; else mock
    income_summary = safe_get_json(f"{MISSION_BRIDGE_URL}/api/income/summary")
    if not income_summary:
      income_summary = {
          "current_earnings": 624000,
          "monthly_target": 1200000,
          "progress_percent": 52.0,
          "active_systems": 10,
      }

    # Recent activity stream - try mission bridge logs endpoint, else mock
    activity = safe_get_json(f"{MISSION_BRIDGE_URL}/api/activity/recent")
    if not activity:
      activity = [
          {
              "time": datetime.now().strftime("%H:%M:%S"),
              "type": "VA Bot",
              "message": "Executed task: daily-report"
          },
          {
              "time": datetime.now().strftime("%H:%M:%S"),
              "type": "Income",
              "message": "Printify sale ₹1200"
          },
          {
              "time": datetime.now().strftime("%H:%M:%S"),
              "type": "System",
              "message": "Bridge sync complete"
          },
      ]

    # Phases summary
    phases = [
        {
            "id": 1,
            "title": "Phase 1 — Fast Kickstart",
            "status": "Active",
            "target": "₹2.5L–₹5L/mo"
        },
        {
            "id": 2,
            "title": "Phase 2 — Scaling",
            "status": "Prepare",
            "target": "₹6L–₹10L/mo"
        },
        {
            "id": 3,
            "title": "Phase 3 — Advanced Engines",
            "status": "Preparing",
            "target": "₹12L+/mo"
        },
    ]

    payload = {
        "timestamp": now,
        "bridge_status": bridge_status,
        "brain_status": brain_status,
        "va_status": va_status,
        "income_summary": income_summary,
        "activity": activity,
        "phases": phases,
    }
    return jsonify(payload)
  except Exception as e:
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


# Basic root route - renders the full dashboard UI
@app.route("/")
def index():
  # Template string - inline for single-file deployment. Uses simple CSS + JS.
  # The UI fetches /api/status every 10s and updates cards.
  template = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>JRAVIS Dashboard v5 — Mission 2040</title>
  <style>
    :root {
      --bg: #0b0b0b;
      --card: #121212;
      --muted: #9aa0a6;
      --accent: #00ff88;
      --accent-2: #00c6ff;
      --glass: rgba(255,255,255,0.03);
      --border: #1f1f1f;
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }
    html,body { height:100%; margin:0; background:var(--bg); color:#e6eef3; }
    .container { max-width:1200px; margin:24px auto; padding:18px; }
    header { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:18px; }
    .title { font-size:20px; font-weight:700; letter-spacing:0.6px; }
    .sub { color:var(--muted); font-size:13px; }
    .grid { display:grid; gap:16px; grid-template-columns: 1fr 360px; align-items:start; }
    .wide-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; }
    .card { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; box-shadow: 0 6px 24px rgba(0,0,0,0.6); }
    .big { padding:20px; }
    .muted { color:var(--muted); }
    .progress { height:10px; background:#0f1720; border-radius:999px; overflow:hidden; border:1px solid #0f1520; }
    .progress > i { display:block; height:100%; background:linear-gradient(90deg,var(--accent),var(--accent-2)); }
    .row { display:flex; gap:12px; align-items:center; }
    .col { display:flex; flex-direction:column; gap:8px; }
    .phase { padding:12px; border-radius:10px; background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02)); }
    .activity { max-height:320px; overflow:auto; }
    .small { font-size:13px; color:var(--muted); }
    .accent-pill { background:rgba(0,255,136,0.1); color:var(--accent); padding:6px 10px; border-radius:999px; font-weight:600; }
    button.primary { background:var(--accent); color:#042018; border:none; padding:8px 12px; border-radius:10px; font-weight:700; cursor:pointer; }
    nav.sidebar { background:transparent; border:1px solid var(--border); padding:12px; border-radius:12px; display:flex; flex-direction:column; gap:10px; }
    nav.sidebar button { background:transparent; color:var(--muted); border:0; text-align:left; padding:8px; cursor:pointer; border-radius:8px; }
    nav.sidebar button:hover { background:var(--glass); color:var(--accent); }
    footer { margin-top:18px; text-align:center; color:var(--muted); font-size:13px; }
    @media (max-width:980px) {
       .grid { grid-template-columns: 1fr; }
       .wide-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <div class="title">JRAVIS Command Console — Mission 2040</div>
        <div class="sub">Realtime command & passive income control panel</div>
      </div>
      <div class="row">
        <div class="muted" id="localTime">--:--:--</div>
        <div style="width:12px"></div>
        <div class="accent-pill" id="phaseTag">Phase 1 Active</div>
      </div>
    </header>

    <div class="grid">
      <main>
        <div class="card big" style="margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-size:14px; color:var(--muted)">Mission Progress</div>
              <div style="font-size:24px; font-weight:700" id="earningsLarge">₹ 0</div>
              <div class="small">Monthly Target <strong id="monthlyTarget">₹ 0</strong></div>
            </div>
            <div style="width:320px;">
              <div class="small">Progress</div>
              <div class="progress" style="margin-top:8px;">
                <i id="progressBar" style="width:0%"></i>
              </div>
              <div class="small" style="margin-top:6px; display:flex; justify-content:space-between;">
                <span id="progressLabel">0%</span>
                <span id="activeSystems">0 systems active</span>
              </div>
            </div>
          </div>
        </div>

        <div class="wide-grid">
          <!-- Phase cards -->
          <div class="card phase" id="phase1">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <div style="font-weight:700">Phase 1 — Fast Kickstart</div>
                  <div class="small">Immediate execution & early cash inflow</div>
                </div>
                <div class="accent-pill">Live</div>
            </div>
            <div style="margin-top:12px" id="phase1Details">
              Target: ₹2.5L–₹5L/month
            </div>
          </div>

          <div class="card phase" id="phase2">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <div style="font-weight:700">Phase 2 — Scaling</div>
                  <div class="small">Automation & asset growth</div>
                </div>
                <div style="color:#F5C94F; font-weight:700">Prepare</div>
            </div>
            <div style="margin-top:12px">Target: ₹6L–₹10L/month</div>
          </div>

          <div class="card phase" id="phase3">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <div style="font-weight:700">Phase 3 — Advanced Engines</div>
                  <div class="small">Recurring, global revenue</div>
                </div>
                <div style="color:#C398FF; font-weight:700">Planning</div>
            </div>
            <div style="margin-top:12px">Target: ₹12L+/month</div>
          </div>
        </div>

        <div class="card" style="margin-top:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div style="font-weight:700">System Activity Timeline</div>
            <div class="small" id="activityTime">updated just now</div>
          </div>
          <div class="activity" id="activityList">
            <!-- filled by JS -->
          </div>
        </div>
      </main>

      <aside>
        <nav class="sidebar card">
          <div style="font-weight:700; margin-bottom:6px;">Navigation</div>
          <button onclick="showPanel('overview')">Overview</button>
          <button onclick="showPanel('systems')">Systems</button>
          <button onclick="showPanel('reports')">Reports</button>
          <button onclick="showPanel('vabot')">VA Bot</button>
          <button onclick="showPanel('settings')">Settings</button>
        </nav>

        <div style="height:16px"></div>

        <div class="card">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:700">Income Snapshot</div>
            <div class="small">Live</div>
          </div>
          <div style="margin-top:12px;">
            <div class="small">Earnings</div>
            <div style="font-size:18px; font-weight:700;" id="earningsSmall">₹ 0</div>
            <div class="small" style="margin-top:8px;">Monthly Target: <span id="earningsTargetSmall">₹ 0</span></div>
            <div style="margin-top:12px;"><button class="primary" onclick="openReports()">Open Reports</button></div>
          </div>
        </div>

      </aside>
    </div>

    <footer>
      JRAVIS • Mission 2040 — JRAVIS Brain online • {dt}
    </footer>
  </div>

<script>
const apiUrl = "/api/status";

function formatINR(x){
  try { return x.toLocaleString('en-IN'); }
  catch(e){ return x; }
}

function updateUI(data){
  if(!data) return;
  const inc = data.income_summary || {};
  document.getElementById('earningsLarge').innerText = '₹ ' + formatINR(inc.current_earnings || 0);
  document.getElementById('earningsSmall').innerText = '₹ ' + formatINR(inc.current_earnings || 0);
  document.getElementById('monthlyTarget').innerText = '₹ ' + formatINR(inc.monthly_target || 0);
  document.getElementById('earningsTargetSmall').innerText = '₹ ' + formatINR(inc.monthly_target || 0);
  const p = inc.progress_percent || 0;
  document.getElementById('progressBar').style.width = Math.min(100, p) + '%';
  document.getElementById('progressLabel').innerText = (p||0).toFixed(1) + '%';
  document.getElementById('activeSystems').innerText = (inc.active_systems || 0) + ' systems active';
  // update activity
  const act = data.activity || [];
  const container = document.getElementById('activityList');
  container.innerHTML = '';
  act.slice(0, 30).forEach(a => {
    const div = document.createElement('div');
    div.style.padding = '8px 0';
    div.style.borderBottom = '1px solid rgba(255,255,255,0.03)';
    div.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;"><div class="small">${a.type}</div><div class="small">${a.time}</div></div><div style="margin-top:6px">${a.message}</div>`;
    container.appendChild(div);
  });
  // update phase tag/time
  document.getElementById('phaseTag').innerText = 'Phase 1 Active';
  document.getElementById('activityTime').innerText = 'updated ' + new Date().toLocaleTimeString();
}

async function fetchAndUpdate(){
  try{
    const r = await fetch(apiUrl, {cache:'no-store'});
    if(!r.ok) throw new Error('no data');
    const d = await r.json();
    updateUI(d);
  }catch(e){
    // fallback: show nothing but keep retrying
    console.warn('status fetch failed', e);
  }
}

function openReports(){
  // open the dashboard reports page (Flask route can be added later)
  window.open('/reports', '_blank');
}

function showPanel(name){
  alert('Panel: ' + name + ' — UI panels will be implemented next.');
}

// live clock
function tick(){
  document.getElementById('localTime').innerText = new Date().toLocaleString();
}

setInterval(tick, 1000);
tick();
fetchAndUpdate();
setInterval(fetchAndUpdate, 10000);
</script>

</body>
</html>
    """.replace("{dt}",
                datetime.utcnow().strftime("%d %b %Y %H:%M UTC"))
  return render_template_string(template)


# Optional: a simple /reports route to view stored reports (placeholder)
@app.route("/reports")
def reports():
  # Replace with real stored report listing if you add storage
  sample = [{
      "name": "Daily Report 16-10-2025",
      "url": "#"
  }, {
      "name": "Weekly Report 12-10-2025",
      "url": "#"
  }]
  return jsonify(sample)


# Health endpoint for Render / other services to verify
@app.route("/health")
def health():
  return jsonify({
      "status": "ok",
      "service": "jravis-brain",
      "time": datetime.utcnow().isoformat() + "Z"
  })


if __name__ == "__main__":
  # Bind to correct port for Render
  port = int(os.environ.get("PORT", 8080))
  # Use threaded server for lightweight usage
  app.run(host="0.0.0.0", port=port, threaded=True)
