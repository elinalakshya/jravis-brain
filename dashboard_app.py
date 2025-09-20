#!/usr/bin/env python3
"""
Tiny local dashboard for VA Bot:
- /dashboard : shows latest meshytube JSON preview + link to health endpoint
Run: python3 dashboard_app.py
"""
from flask import Flask, jsonify, send_file, render_template_string
import glob, json, os

app = Flask(__name__)

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
    const r = await fetch('/proxy/health');
    const j = await r.json();
    document.getElementById('health').textContent = JSON.stringify(j, null, 2);
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

@app.route('/dashboard')
def dashboard():
    return render_template_string(TEMPLATE)

@app.route('/latest-json')
def latest_json():
    files = sorted(glob.glob('DailyReport/out/connectors_meshytube_*.json'))
    if not files:
        return ('', 204)
    with open(files[-1], 'r') as fh:
        return jsonify(json.load(fh))

@app.route('/proxy/health')
def proxy_health():
    # call local app health endpoint
    try:
        import urllib.request, json
        with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5) as r:
            return (r.read(), r.getheader('Content-Type'))
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route('/run-capture', methods=['POST'])
def run_capture():
    # run capture script (non-blocking quick exec) - we run it synchronously but return text
    try:
        rc = os.system('PYTHONPATH=. python3 DailyReport/capture_meshytube.py > /tmp/capture.out 2>&1')
        with open('/tmp/capture.out','r') as fh:
            out = fh.read(2000)
        return out if out else 'ok'
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(port=8050, host='0.0.0.0')
