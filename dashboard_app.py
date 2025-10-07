#!/usr/bin/env python3
"""
VA BOT Dashboard for Render deployment
- /dashboard : web dashboard
- /latest-json : preview latest MeshyTube JSON
- /proxy/health : proxy check
- /run-capture : trigger capture script
- /health : simple uptime ping
"""

from flask import Flask, jsonify, send_file, render_template_string, request
import glob, json, os, datetime, urllib.request

app = Flask(__name__)

# -------------------- HTML TEMPLATE --------------------
TEMPLATE = """
<!doctype html>
<title>VA Bot Dashboard</title>
<style>
body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; margin: 24px; }
.card { background: #fff; padding: 18px; border-radius: 10px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); margin-bottom: 16px; }
h1 { margin:0 0 8px 0; font-size: 20px; }
pre { white-space: pre-wrap; word-break:break-word; }
.badge { display:inline-block; padding:4px 8px; border-radius:999px; background:#eef; font-weight:600; }
</style>
<h1>VA Bot — Dashboard</h1>
<div class="card">
  <div><strong>Health</strong> <span class="badge">/health</span></div>
  <pre id="health">Loading...</pre>
</div>
<div class="card">
  <div><strong>Latest connectors_meshytube JSON</strong></div>
  <pre id="json">Loading...</pre>
</div>
<div class="card">
  <div><strong>Actions</strong></div>
  <button onclick="runCapture()">Run capture now</button>
  <em> — calls local capture script via server</em>
</div>
<script>
async function loadHealth(){
  try{
    const r = await fetch('/health');
    const t = await r.text();
    document.getElementById('health').textContent = t;
  }catch(e){ document.getElementById('health').textContent = String(e); }
}
async function loadJSON(){
  try{
    const r = await fetch('/latest-json');
    if(r.status===204){ document.getElementById('json').textContent = "No JSON found"; return; }
    const j = await r.json();
    document.getElementById('json').textContent = JSON.stringify(j, null, 2);
  }catch(e){ document.getElementById('json').textContent = String(e); }
}
async function runCapture(){
  const r = await fetch('/run-capture', { method: 'POST' });
  const txt = await r.text();
  alert('Capture run: ' + txt);
  await loadJSON();
}
loadHealth();
loadJSON();
setInterval(loadHealth, 30000);
setInterval(loadJSON, 60000);
</script>
"""


# -------------------- ROUTES --------------------
@app.route("/")
def index():
    return jsonify({
        "status": "✅ VA BOT online",
        "time": datetime.datetime.now().isoformat()
    })


@app.route("/dashboard")
def dashboard():
    return render_template_string(TEMPLATE)


@app.route("/health")
def health():
    return "OK", 200


@app.route("/latest-json")
def latest_json():
    files = sorted(glob.glob('DailyReport/out/connectors_meshytube_*.json'))
    if not files:
        return ('', 204)
    with open(files[-1], 'r') as fh:
        return jsonify(json.load(fh))


@app.route("/proxy/health")
def proxy_health():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/health',
                                    timeout=5) as r:
            return (r.read(), r.getheader('Content-Type'))
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/run-capture", methods=["POST"])
def run_capture():
    try:
        rc = os.system(
            'PYTHONPATH=. python3 DailyReport/capture_meshytube.py > /tmp/capture.out 2>&1'
        )
        with open('/tmp/capture.out', 'r') as fh:
            out = fh.read(2000)
        return out if out else 'ok'
    except Exception as e:
        return str(e), 500


# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"⚙️  Starting VA BOT Dashboard on port {port}")
    app.run(host="0.0.0.0", port=port)
