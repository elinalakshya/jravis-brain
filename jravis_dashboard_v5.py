#!/usr/bin/env python3
"""
jravis_dashboard_v5.py
JRAVIS Dashboard v5 — Dark glass UI + Live Global Income Map + Stream summary

Usage: deploy to Render with gunicorn:
    gunicorn jravis_dashboard_v5:app --bind 0.0.0.0:$PORT

Environment variables:
  SECRET_KEY   - Flask secret
  LOCK_CODE    - lock code (password)
  SHARED_KEY   - shared secret between JRAVIS and VA Bot
  VABOT_URL    - VA Bot base URL (e.g. https://va-bot-connector.onrender.com)
  INCOME_API   - income-system JSON endpoint (optional)
  THEME        - 'dark' (default) or 'neon'
"""
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import os, requests, time, json, traceback

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "jrvis_secret_fallback")

LOCK_CODE = os.environ.get("LOCK_CODE", "2040lock")
SHARED_KEY = os.environ.get("SHARED_KEY", "jrvis_vabot_2040_securekey")
VABOT_URL = os.environ.get("VABOT_URL",
                           "https://va-bot-connector.onrender.com")
INCOME_API = os.environ.get("INCOME_API", "")
THEME = os.environ.get("THEME", "dark").lower()

# ---------------------------
# sample fallback dataset (used when income API doesn't provide geo info)
# shape: list of {"country":"India","country_code":"IN","stream":"Printify","amount":5000,"timestamp":"..."}
# ---------------------------
SAMPLE_STREAMS = [
    {
        "country": "India",
        "country_code": "IN",
        "stream": "Printify",
        "amount": 624000,
        "timestamp": "2025-10-10T00:00:00Z"
    },
    {
        "country": "United States",
        "country_code": "US",
        "stream": "YouTube",
        "amount": 8250,
        "timestamp": "2025-10-09T00:00:00Z"
    },
    {
        "country": "United Kingdom",
        "country_code": "GB",
        "stream": "Fiverr",
        "amount": 1500,
        "timestamp": "2025-10-08T00:00:00Z"
    },
    {
        "country": "Germany",
        "country_code": "DE",
        "stream": "Shopify",
        "amount": 900,
        "timestamp": "2025-10-06T00:00:00Z"
    },
]


# ---------------------------
# Utility: fetch income API and normalize
# ---------------------------
def fetch_income_data():
  """
    Returns dict:
      {
        "total_income": float,
        "progress_percent": float,
        "target": int,
        "streams": [ {country,country_code,stream,amount,timestamp}, ... ],
        "daily_income": [..], "dates": [..]  # optional for chart
      }
    If INCOME_API missing or fails, returns sample data packaged similarly.
    """
  if not INCOME_API:
    # construct a minimal response using SAMPLE_STREAMS
    total = sum(s["amount"] for s in SAMPLE_STREAMS)
    return {
        "total_income": total,
        "progress_percent": round(min(100, total / 40000000 * 100), 2),
        "target": 40000000,
        "streams": SAMPLE_STREAMS,
        "daily_income": [s["amount"] for s in SAMPLE_STREAMS],
        "dates": [s["timestamp"][:10] for s in SAMPLE_STREAMS],
        "note": "sample"
    }

  try:
    r = requests.get(INCOME_API, timeout=8)
    r.raise_for_status()
    payload = r.json()
    # Accept flexible payload shapes:
    # 1) summary object like {"total_income":..., "streams":[...], "daily_income":[...], "dates":[...]}
    # 2) a flat list of income entries
    if isinstance(payload, dict) and "streams" in payload:
      streams = payload.get("streams") or []
      # try to normalize each stream entry
      normalized = []
      for s in streams:
        # try common keys
        country = s.get("country") or s.get("country_name") or s.get(
            "location") or ""
        country_code = s.get("country_code") or s.get("cc") or s.get(
            "country_iso") or ""
        stream_name = s.get("stream") or s.get("source") or s.get(
            "channel") or "unknown"
        amount = float(
            s.get("amount") or s.get("earnings") or s.get("value") or 0)
        ts = s.get("timestamp") or s.get("time") or ""
        normalized.append({
            "country": country,
            "country_code": country_code,
            "stream": stream_name,
            "amount": amount,
            "timestamp": ts
        })
      total = payload.get("total_income") or sum(x["amount"]
                                                 for x in normalized)
      return {
          "total_income":
          float(total),
          "progress_percent":
          float(
              payload.get("progress_percent", min(100,
                                                  total / 40000000 * 100))),
          "target":
          payload.get("target", 40000000),
          "streams":
          normalized or SAMPLE_STREAMS,
          "daily_income":
          payload.get("daily_income", []),
          "dates":
          payload.get("dates", []),
          "note":
          "api"
      }
    elif isinstance(payload, list):
      # list of entries
      normalized = []
      for s in payload:
        country = s.get("country") or s.get("country_name") or ""
        country_code = s.get("country_code") or s.get("cc") or ""
        stream_name = s.get("stream") or s.get("source") or "unknown"
        amount = float(s.get("amount") or s.get("value") or 0)
        ts = s.get("timestamp") or ""
        normalized.append({
            "country": country,
            "country_code": country_code,
            "stream": stream_name,
            "amount": amount,
            "timestamp": ts
        })
      total = sum(x["amount"] for x in normalized)
      return {
          "total_income":
          float(total),
          "progress_percent":
          round(min(100, total / 40000000 * 100), 2),
          "target":
          40000000,
          "streams":
          normalized or SAMPLE_STREAMS,
          "daily_income": [x["amount"] for x in normalized],
          "dates":
          [x["timestamp"][:10] if x["timestamp"] else "" for x in normalized],
          "note":
          "api_list"
      }
    else:
      # unknown shape — fallback
      return fetch_income_data_on_error("unknown shape", payload)
  except Exception as e:
    return fetch_income_data_on_error(str(e), None)


def fetch_income_data_on_error(err, payload):
  # Fallback to sample
  total = sum(s["amount"] for s in SAMPLE_STREAMS)
  return {
      "total_income": total,
      "progress_percent": round(min(100, total / 40000000 * 100), 2),
      "target": 40000000,
      "streams": SAMPLE_STREAMS,
      "daily_income": [s["amount"] for s in SAMPLE_STREAMS],
      "dates": [s["timestamp"][:10] for s in SAMPLE_STREAMS],
      "note": "fallback",
      "error": str(err)
  }


# ---------------------------
# Routes: UI + API
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def index():
  if "logged_in" in session:
    return redirect(url_for("dashboard"))
  error = None
  if request.method == "POST":
    code = request.form.get("code", "")
    if code == LOCK_CODE:
      session["logged_in"] = True
      return redirect(url_for("dashboard"))
    error = "Invalid code"
  return render_template_string(LOGIN_HTML, error=error, theme=THEME)


@app.route("/dashboard")
def dashboard():
  if "logged_in" not in session:
    return redirect(url_for("index"))
  return render_template_string(DASH_HTML,
                                theme=THEME,
                                vabot_url=VABOT_URL,
                                shared_key=SHARED_KEY)


@app.route("/health")
def health():
  return jsonify({"status": "ok", "time": int(time.time())}), 200


# Endpoint to accept tasks from UI or other services and forward to VA Bot
@app.route("/api/send_task", methods=["POST"])
def api_send_task():
  auth = request.headers.get("Authorization", "")
  if auth:
    token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
    if token != SHARED_KEY:
      return jsonify({"error": "unauthorized"}), 401

  data = request.get_json(force=True, silent=True) or request.form.to_dict()
  if not data or "action" not in data:
    return jsonify({"error": "invalid payload"}), 400

  # simply forward to VA Bot receiver
  try:
    headers = {"Authorization": f"Bearer {SHARED_KEY}"}
    r = requests.post(f"{VABOT_URL.rstrip('/')}/api/receive_task",
                      json=data,
                      headers=headers,
                      timeout=12)
    return jsonify({
        "status": "sent",
        "va_status": r.status_code,
        "va_text": r.text
    }), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 500


# VA Bot callback endpoint (VA Bot posts status back to JRAVIS)
@app.route("/api/vabot_status", methods=["POST"])
def vabot_status():
  auth = request.headers.get("Authorization", "")
  token = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else ""
  if token != SHARED_KEY:
    return jsonify({"error": "unauthorized"}), 401
  payload = request.get_json(force=True)
  # For now we simply log -> could store into DB or process
  print("[JRAVIS] VA Bot callback:", payload)
  return jsonify({"status": "ok"}), 200


# Normalized streams API for front-end (map + table)
@app.route("/api/streams", methods=["GET"])
def api_streams():
  data = fetch_income_data()
  # If stream entries have no country_code, try to map country names to ISO using a simple map
  processed = []
  for s in data.get("streams", []):
    cc = s.get("country_code") or ""
    country = s.get("country") or ""
    # fallback mapping for some common names (extendable)
    if not cc and country:
      mapping = {
          "India": "IN",
          "United States": "US",
          "UK": "GB",
          "United Kingdom": "GB",
          "Germany": "DE"
      }
      cc = mapping.get(country, "")
    processed.append({
        "country": country,
        "country_code": cc,
        "stream": s.get("stream"),
        "amount": s.get("amount", 0),
        "timestamp": s.get("timestamp", "")
    })
  return jsonify({
      "total_income": data.get("total_income"),
      "progress_percent": data.get("progress_percent"),
      "target": data.get("target"),
      "streams": processed,
      "daily_income": data.get("daily_income", []),
      "dates": data.get("dates", []),
      "note": data.get("note", "")
  }), 200


# ---------------------------
# HTML templates (inline for single-file deploy)
# ---------------------------
LOGIN_HTML = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>JRAVIS Lock</title>
  <style>
    body { background: #071022; color:#e6eef6; font-family: Inter, Arial, sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }
    .card { background: rgba(255,255,255,0.03); padding:28px; border-radius:12px; width:320px; text-align:center; }
    input[type=password] { width:100%; padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.05); background:transparent; color:inherit; }
    button { margin-top:12px; padding:10px 16px; border-radius:8px; border:none; background:linear-gradient(90deg,#00ffff,#00ff7f); color:#042018; font-weight:700; cursor:pointer;}
    .err{ color:#ffb4b4; margin-top:8px;}
  </style>
</head>
<body>
  <div class="card">
    <h2>JRAVIS Secure Access</h2>
    <form method="post">
      <input name="code" type="password" placeholder="Enter lock code" required />
      <button>Unlock</button>
    </form>
    {% if error %}<div class="err">{{error}}</div>{% endif %}
    <div style="margin-top:8px;font-size:12px;color:#9aa7bf">Theme: {{theme}}</div>
  </div>
</body>
</html>
"""

DASH_HTML = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>JRAVIS v5 — Mission 2040</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    :root {
      --bg: #071022;
      --card: rgba(255,255,255,0.03);
      --muted: #9aa7bf;
      --accent1: #00ffff;
      --accent2: #00ff7f;
    }
    body { margin:0; font-family:Inter, Arial, sans-serif; background:var(--bg); color:#e6eef6; }
    header { padding:18px 28px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.03); }
    .brand { font-size:20px; font-weight:700; color:var(--accent1); }
    .wrap { padding:20px; max-width:1200px; margin:0 auto; }
    .grid { display:grid; grid-template-columns: 1fr 360px; gap:18px; align-items:start; }
    .card { background:var(--card); padding:16px; border-radius:12px; box-shadow:0 6px 18px rgba(0,0,0,0.6); }
    .map { height:360px; border-radius:8px; overflow:hidden; }
    .small { color:var(--muted); font-size:13px; }
    .progress { background:#0d1220; border-radius:8px; height:12px; overflow:hidden; }
    .progress > div { height:100%; background:linear-gradient(90deg,var(--accent1),var(--accent2)); width:0% }
    .streams-list { max-height:240px; overflow:auto; margin-top:10px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:8px 6px; text-align:left; color:#e6eef6; font-size:14px; }
    th { color:var(--accent1); font-weight:700; font-size:13px; }
    .muted { color:var(--muted); font-size:13px; }
    .controls { display:flex; gap:8px; margin-top:10px; }
    button { padding:8px 12px; border-radius:8px; border:none; background:linear-gradient(90deg,var(--accent1),var(--accent2)); color:#042018; font-weight:700; cursor:pointer; }
    .neon body, .neon .card { /* optional neon style */ }
  </style>
</head>
<body class="{{ 'neon' if theme=='neon' else '' }}">
  <header>
    <div class="brand">Jarvis Brain — Mission 2040</div>
    <div class="small">Status: <strong id="statusText">Live</strong></div>
  </header>

  <div class="wrap">
    <div class="grid">
      <div>
        <div class="card">
          <h3>Global Income Map</h3>
          <div id="map" class="map"></div>
          <div style="display:flex;justify-content:space-between;margin-top:10px">
            <div class="small">Auto-refresh every 30s</div>
            <div class="small">Source: <span id="mapSource">income-system</span></div>
          </div>
        </div>

        <div class="card" style="margin-top:16px;">
          <h3>Streams & Breakdown</h3>
          <div id="streamsSummary" class="streams-list">
            <!-- filled by JS -->
          </div>
        </div>
      </div>

      <div>
        <div class="card">
          <h3>Mission Progress</h3>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div class="small">Total Earnings</div>
              <div id="totalEarnings" style="font-size:22px;font-weight:700">₹0</div>
              <div class="muted" id="percentText">0% of ₹4 Cr</div>
            </div>
            <div style="width:150px">
              <div class="progress"><div id="mainProgressBar" style="width:0%"></div></div>
            </div>
          </div>

          <div style="margin-top:12px">
            <div class="small">Phase 1</div>
            <div class="progress"><div id="phase1Bar" style="width:0%"></div></div>
            <div class="small" style="margin-top:8px">Phase 2</div>
            <div class="progress"><div id="phase2Bar" style="width:0%"></div></div>
            <div class="small" style="margin-top:8px">Phase 3</div>
            <div class="progress"><div id="phase3Bar" style="width:0%"></div></div>
          </div>
        </div>

        <div class="card" style="margin-top:16px;">
          <h3>Earnings Chart</h3>
          <canvas id="earnChart" height="140"></canvas>
        </div>

        <div class="card" style="margin-top:16px;">
          <h3>Controls</h3>
          <div class="controls">
            <button onclick="sendTask('start_stream','Printify',1)">Start Printify</button>
            <button onclick="sendTask('run_phase','Phase1_Global',1)">Run Phase 1</button>
          </div>
          <div style="margin-top:10px" id="controlResult"></div>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const STREAMS_API = "/api/streams";
    const REFRESH_MS = 30000;
    const COUNTRY_TO_COORD = { /* minimal sample lat/lon for a few countries */
      "IN": [20.5937,78.9629],
      "US": [37.0902,-95.7129],
      "GB": [55.3781,-3.4360],
      "DE": [51.1657,10.4515]
    };

    // init map
    const map = L.map('map', { zoomControl: true }).setView([20,0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{ attribution:'© OpenStreetMap contributors' }).addTo(map);
    let markers = [];

    async function loadStreams(){
      try{
        const res = await fetch(STREAMS_API);
        const j = await res.json();
        document.getElementById('mapSource').innerText = j.note || 'income-system';
        updateMap(j.streams || []);
        updateSummary(j);
      }catch(e){
        console.error("streams load error", e);
      }
    }

    function clearMarkers(){
      markers.forEach(m=>map.removeLayer(m));
      markers = [];
    }

    function updateMap(streams){
      clearMarkers();
      // aggregate by country_code
      const agg = {};
      streams.forEach(s=>{
        const cc = (s.country_code || '').toUpperCase() || (s.country || '').slice(0,2).toUpperCase();
        const key = cc || s.country || 'NA';
        if(!agg[key]) agg[key] = { amount:0, list:[] };
        agg[key].amount += Number(s.amount || 0);
        agg[key].list.push(s);
      });
      // add markers
      Object.keys(agg).forEach(cc=>{
        const data = agg[cc];
        const coord = COUNTRY_TO_COORD[cc] || [0,0];
        const popupHtml = `<div style="min-width:160px"><strong>${cc}</strong><br/>Total: ₹${Number(data.amount).toLocaleString()}<br/>Streams:<ul>${data.list.slice(0,4).map(x=>`<li>${x.stream}: ₹${x.amount.toLocaleString()}</li>`).join('')}</ul></div>`;
        const marker = L.circleMarker(coord, { radius: Math.min(40, 6 + Math.log(data.amount+1)), color:'#00ffff', fillColor:'#00ff7f', fillOpacity:0.6 }).addTo(map).bindPopup(popupHtml);
        markers.push(marker);
      });
    }

    function formatCurrency(x){ return "₹" + Number(x).toLocaleString(); }

    function updateSummary(j){
      // totals
      document.getElementById('totalEarnings').innerText = formatCurrency(j.total_income || 0);
      document.getElementById('percentText').innerText = (j.progress_percent || 0) + "% of ₹" + (j.target || 40000000).toLocaleString();
      document.getElementById('mainProgressBar').style.width = (j.progress_percent || 0) + "%";
      // phases: simple mapping
      const p = j.progress_percent || 0;
      document.getElementById('phase1Bar').style.width = Math.min(100, p) + "%";
      document.getElementById('phase2Bar').style.width = Math.min(60, p * 0.6) + "%";
      document.getElementById('phase3Bar').style.width = Math.min(30, p * 0.3) + "%";
      // streams list
      const node = document.getElementById('streamsSummary');
      node.innerHTML = "";
      const streams = j.streams || [];
      streams.slice(0,40).forEach(s=>{
        const div = document.createElement('div');
        div.style.padding = "6px 0";
        div.innerHTML = `<strong>${s.stream}</strong> · ${s.country || s.country_code || 'N/A'} · ${formatCurrency(s.amount)}`;
        node.appendChild(div);
      });
      // chart
      updateChart(j.dates || [], j.daily_income || []);
    }

    // chart
    let chartInstance = null;
    function updateChart(labels, data){
      const ctx = document.getElementById('earnChart').getContext('2d');
      if(chartInstance) chartInstance.destroy();
      chartInstance = new Chart(ctx, {
        type:'line',
        data:{ labels: labels, datasets:[{ label:'Earnings', data:data, borderColor:'#00ffff', backgroundColor:'rgba(0,255,255,0.08)', fill:true }]},
        options:{ scales:{ x:{ ticks:{ color:'#cfefff' }}, y:{ ticks:{ color:'#cfefff' }}}}
      });
    }

    async function sendTask(action, stream, phase){
      try{
        const payload = { action, stream, phase };
        const res = await fetch('/api/send_task', {
          method:'POST',
          headers:{ 'Content-Type':'application/json', 'Authorization': 'Bearer ' + '{{ shared_key }}' },
          body: JSON.stringify(payload)
        });
        const j = await res.json();
        document.getElementById('controlResult').innerText = JSON.stringify(j);
      }catch(e){
        document.getElementById('controlResult').innerText = 'Error sending task';
      }
    }

    // initial load + polling
    loadStreams();
    setInterval(loadStreams, REFRESH_MS);
  </script>
</body>
</html>
"""

# ---------------------------
# Start app (when run directly)
# ---------------------------
if __name__ == "__main__":
  # pick port from env
  port = int(os.environ.get("PORT", 10000))
  print(f"[JRAVIS v5] starting on port {port} (theme={THEME})")
  app.run(host="0.0.0.0", port=port)
