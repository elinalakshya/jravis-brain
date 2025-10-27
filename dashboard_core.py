#!/usr/bin/env python3
"""
Integrated JRAVIS v5 -> v6 UI upgrade (single-file).
Features:
 - Lock screen + session
 - Dashboard UI (left sidebar, center panels, right feed)
 - /api/live (JSON)
 - /api/feed/stream (SSE)
 - /api/chat (store + simple JRAVIS reply)
 - Reads phase1_exec.db for exec_log/tasks to produce live feed
"""

import os
import sqlite3
import json
import time
from datetime import datetime
from flask import Flask, request, redirect, session, render_template_string, jsonify, Response

# ---------- CONFIG ----------
LOCK_CODE = os.getenv("LOCK_CODE", "LakshyaSecureCode@2040")
FLASK_SECRET = os.getenv("DASHBOARD_SECRET", "JRAVIS@Mission2040")
DB_PATH = os.getenv("DB_PATH", "dashboard.db")  # dashboard orders & chat
PHASE1_DB = os.getenv("PHASE1_DB_PATH", "phase1_exec.db")  # phase1 worker DB
REFRESH_SECONDS = 15

app = Flask(__name__)
app.secret_key = FLASK_SECRET


# ---------- DB INIT ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # orders table for dashboard revenue (if you insert test orders)
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stream TEXT,
        amount REAL,
        currency TEXT DEFAULT 'INR',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)
    # chat table for dashboard chat
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        message TEXT,
        reply TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------- HELPERS ----------
def read_orders_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), IFNULL(SUM(amount),0) FROM orders")
    total_orders, total_revenue = c.fetchone()
    c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 20")
    recent = c.fetchall()
    conn.close()
    return int(total_orders or 0), float(total_revenue or 0.0), recent


def read_phase1_metrics():
    """Return systems list and last_sync from phase1 DB (if available)."""
    if not os.path.exists(PHASE1_DB):
        return [], None
    conn = sqlite3.connect(PHASE1_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        q = """SELECT t.system_id, t.payload, el.status, el.timestamp
               FROM exec_log el
               LEFT JOIN tasks t ON el.task_id = t.id
               ORDER BY el.timestamp DESC
               LIMIT 1000"""
        c.execute(q)
        rows = c.fetchall()
    except Exception:
        conn.close()
        return [], None

    agg = {}
    last_sync = None
    for r in rows:
        payload_raw = r["payload"] or "{}"
        try:
            payload = json.loads(payload_raw)
            sys_name = payload.get(
                "system",
                {}).get("name") or f"system-{r['system_id'] or 'unknown'}"
        except Exception:
            sys_name = f"system-{r['system_id'] or 'unknown'}"
        if sys_name not in agg:
            agg[sys_name] = {"success": 0, "failure": 0, "last_success": None}
        if r["status"] and r["status"].lower().startswith("success"):
            agg[sys_name]["success"] += 1
            agg[sys_name]["last_success"] = agg[sys_name]["last_success"] or r[
                "timestamp"]
            last_sync = last_sync or r["timestamp"]
        else:
            agg[sys_name]["failure"] += 1
            last_sync = last_sync or r["timestamp"]

    conn.close()
    systems = [{"name": k, **v} for k, v in agg.items()]
    systems = sorted(systems, key=lambda x: (-x["success"], x["name"]))
    return systems, last_sync


# ---------- API: live JSON ----------
@app.route("/api/live")
def api_live():
    total_orders, total_revenue, recent = read_orders_summary()
    systems, last_sync = read_phase1_metrics()
    # progress example toward monthly target - customizable via env
    try:
        target = float(os.getenv("MONTHLY_TARGET", "100000"))
    except:
        target = 100000.0
    progress = min(int((total_revenue / target) * 100), 100) if target else 0
    return jsonify({
        "orders":
        total_orders,
        "revenue":
        round(total_revenue, 2),
        "progress":
        progress,
        "target":
        target,
        "systems":
        systems,
        "recent_orders": [{
            "id": r[0],
            "stream": r[1],
            "amount": r[2],
            "currency": r[3],
            "created_at": r[4]
        } for r in recent],
        "last_sync":
        last_sync
    })


# ---------- SSE: live feed from phase1 exec_log ----------
def sse_stream():
    """
    Simple polling-based SSE streamer.
    Emits new exec_log rows as events.
    """
    last_ts = None
    while True:
        if not os.path.exists(PHASE1_DB):
            # emit heartbeat to keep connection alive
            yield f"event: heartbeat\ndata: {json.dumps({'time': datetime.utcnow().isoformat()})}\n\n"
            time.sleep(2)
            continue

        conn = sqlite3.connect(PHASE1_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        try:
            if last_ts:
                c.execute(
                    "SELECT el.id, t.payload, el.status, el.timestamp FROM exec_log el LEFT JOIN tasks t ON el.task_id=t.id WHERE el.timestamp > ? ORDER BY el.timestamp ASC LIMIT 50",
                    (last_ts, ))
            else:
                c.execute(
                    "SELECT el.id, t.payload, el.status, el.timestamp FROM exec_log el LEFT JOIN tasks t ON el.task_id=t.id ORDER BY el.timestamp DESC LIMIT 10"
                )
            rows = c.fetchall()
        except Exception:
            rows = []
        conn.close()

        if rows:
            # if we fetched newest-first, reverse to stream oldest->newest
            rows = list(rows)
            rows_sorted = sorted(rows, key=lambda r: r["timestamp"])
            for r in rows_sorted:
                payload = r["payload"] or "{}"
                try:
                    payload_parsed = json.loads(payload)
                except:
                    payload_parsed = {"raw": payload}
                ev = {
                    "id": r["id"],
                    "payload": payload_parsed,
                    "status": r["status"],
                    "timestamp": r["timestamp"]
                }
                last_ts = r["timestamp"]
                yield f"event: exec_log\ndata: {json.dumps(ev, default=str)}\n\n"
        else:
            # heartbeat
            yield f"event: heartbeat\ndata: {json.dumps({'time': datetime.utcnow().isoformat()})}\n\n"

        time.sleep(2)


@app.route("/api/feed/stream")
def feed_stream():
    return Response(sse_stream(), mimetype="text/event-stream")


# ---------- Chat endpoint ----------
def jravis_simple_reply(user_msg: str) -> str:
    """Deterministic JRAVIS-style reply for now."""
    msg = user_msg.lower()
    # simple rule-based suggestions
    if "income" in msg or "paypal" in msg:
        return "JRAVIS: First PayPal window expected within 3–5 business days after first sale. I will track payouts and notify you."
    if "dashboard" in msg or "error" in msg:
        return "JRAVIS: Dashboard issue noted. I will re-init the DB and show live metrics — done."
    if "phase 2" in msg:
        return "JRAVIS: Phase 2 plan ready. I can start setup when you confirm — ETA 2 weeks to baseline."
    return "JRAVIS: Acknowledged. I have queued this for action and will report back in the activity feed."


@app.route("/api/chat", methods=["POST"])
def api_chat():
    # require unlocked session
    if not session.get("unlocked"):
        return jsonify({"error": "locked"}), 401
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "empty"}), 400
    # store user message
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat (sender, message) VALUES (?, ?)",
              ("user", message))
    uid = c.lastrowid
    conn.commit()
    # craft reply
    reply = jravis_simple_reply(message)
    c.execute("UPDATE chat SET reply=? WHERE id=?", (reply, uid))
    conn.commit()
    conn.close()
    # also emit a small exec_log-like event into phase1 DB if exists (non-destructive)
    try:
        if os.path.exists(PHASE1_DB):
            pconn = sqlite3.connect(PHASE1_DB)
            pc = pconn.cursor()
            # not modifying existing tables; we can insert into exec_log if table exists with safe shape
            try:
                pc.execute(
                    "INSERT INTO exec_log (id, task_id, timestamp, status, response_code, response_text) VALUES (?, ?, ?, ?, ?, ?)",
                    (None, None, datetime.utcnow().isoformat(), "success", 200,
                     f"Chat reply: {reply[:200]}"))
                pconn.commit()
            except Exception:
                # fall back - do nothing
                pass
            pconn.close()
    except Exception:
        pass
    return jsonify({"reply": reply})


# ---------- UI (inlined) ----------
# A single-page Tailwind + vanilla JS frontend that:
# - unlocks via POST /unlock
# - polls /api/live every REFRESH_SECONDS
# - listens to /api/feed/stream SSE and appends live feed
FRONTEND = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>JRAVIS Command Console — Mission 2040 (v6)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { background:#030712; color:#e6fbff; font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial; }
    .neon { color:#00ff88; text-shadow:0 0 8px rgba(0,255,136,0.25); }
    .glass { background: rgba(10,14,20,0.6); border:1px solid rgba(0,255,136,0.06); backdrop-filter: blur(6px); }
    .feed-item { font-size:0.92rem; border-bottom:1px solid rgba(255,255,255,0.02); padding:8px 0; }
    .chatbox { position:fixed; right:20px; bottom:24px; width:360px; max-width:90%; z-index:60; }
  </style>
</head>
<body>
  <div id="app" class="min-h-screen p-6">
    <div id="locked-screen" class="min-h-screen flex items-center justify-center" style="display:none">
      <div class="glass p-8 rounded-2xl text-center w-[420px]">
        <h2 class="text-2xl neon mb-2">🔒 JRAVIS Dashboard Locked</h2>
        <p class="text-sm text-gray-300 mb-4">Enter your lock code to access the control center.</p>
        <input id="lockcode" class="w-full p-3 rounded bg-[#071021] border border-[#0f2430] text-white mb-3" placeholder="Lock code" />
        <button onclick="unlock()" class="w-full btn-neon py-2 rounded text-black font-semibold">Unlock</button>
        <p id="unlock-error" class="text-red-400 mt-2" style="display:none"></p>
      </div>
    </div>

    <div id="dashboard" style="display:none">
      <div class="flex gap-4">
        <!-- left sidebar -->
        <div class="w-1/5 glass p-4 rounded-lg">
          <h3 class="neon font-bold text-lg">JRAVIS Brain</h3>
          <p class="text-sm text-gray-300 mt-2">Mission 2040 • Phase 1 Active</p>
          <div class="mt-4">
            <div class="text-xs text-gray-400">Status</div>
            <div class="neon font-semibold">ACTIVE</div>
          </div>
          <div class="mt-6">
            <div class="text-xs text-gray-400">Worker</div>
            <div class="text-green-400 font-semibold" id="worker-status">Running</div>
          </div>
          <div class="mt-6">
            <div class="text-xs text-gray-400">Next Sync</div>
            <div id="next-sync" class="text-sm">N/A</div>
          </div>
        </div>

        <!-- center -->
        <div class="flex-1">
          <div class="grid grid-cols-3 gap-4 mb-4">
            <div class="glass p-4 rounded-lg text-center">
              <div class="text-xs text-gray-400">Total Revenue</div>
              <div class="text-2xl neon font-bold" id="total-rev">₹ 0.00</div>
            </div>
            <div class="glass p-4 rounded-lg text-center">
              <div class="text-xs text-gray-400">Total Orders</div>
              <div class="text-2xl font-bold" id="total-orders">0</div>
            </div>
            <div class="glass p-4 rounded-lg text-center">
              <div class="text-xs text-gray-400">Target Progress</div>
              <div class="text-xl neon font-bold" id="progress">0%</div>
            </div>
          </div>

          <div class="glass p-4 rounded-lg mb-4">
            <h4 class="neon font-semibold">Phase 1 — Systems</h4>
            <div id="systems-list" class="mt-3 space-y-2"></div>
          </div>

          <div class="glass p-4 rounded-lg">
            <h4 class="neon font-semibold">Recent Orders</h4>
            <div id="orders-list" class="mt-3"></div>
          </div>
        </div>

        <!-- right feed -->
        <div class="w-1/4">
          <div class="glass p-3 rounded-lg mb-4">
            <h4 class="neon font-semibold">Activity Feed</h4>
            <div id="feed" style="max-height:420px; overflow:auto; margin-top:8px"></div>
          </div>

          <div class="glass p-3 rounded-lg">
            <h4 class="neon font-semibold">Quick Actions</h4>
            <button onclick="insertTestOrder()" class="btn-neon mt-3 w-full">Insert ₹1200 Test Order</button>
            <button onclick="fetchNow()" class="mt-3 w-full bg-[#06202a] p-2 rounded">Refresh Now</button>
          </div>
        </div>
      </div>
    </div>

    <!-- chat dock -->
    <div class="chatbox" id="chatbox" style="display:none">
      <div class="glass p-3 rounded-lg">
        <div class="flex justify-between items-center">
          <div class="neon font-semibold">Chat • JRAVIS</div>
          <button onclick="toggleChat()" class="text-sm text-gray-300">Close</button>
        </div>
        <div id="chat-feed" style="height:220px; overflow:auto; margin-top:8px"></div>
        <div class="mt-2 flex gap-2">
          <input id="chat-msg" class="flex-1 p-2 rounded bg-[#071021] border border-[#0f2430]" placeholder="Say something..." />
          <button onclick="sendChat()" class="btn-neon">Send</button>
        </div>
      </div>
    </div>

  </div>

<script>
const REFRESH = {{refresh}};
let eventSource = null;

function showLocked(show){
  document.getElementById('locked-screen').style.display = show ? 'flex' : 'none';
  document.getElementById('dashboard').style.display = show ? 'none' : 'block';
  document.getElementById('chatbox').style.display = show ? 'none' : 'block';
}

function unlock(){
  const code = document.getElementById('lockcode').value;
  fetch('/unlock', { method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:'code='+encodeURIComponent(code)})
    .then(r => {
      if (r.redirected) {
        // unlocked
        showLocked(false);
        start();
      } else {
        document.getElementById('unlock-error').style.display='block';
        document.getElementById('unlock-error').innerText='Invalid code';
      }
    })
    .catch(e => { console.error(e); });
}

function start(){
  fetchNow();
  // poll for metrics
  setInterval(fetchNow, REFRESH*1000);
  // open SSE for feed
  if (eventSource) eventSource.close();
  eventSource = new EventSource('/api/feed/stream');
  eventSource.addEventListener('exec_log', e => {
    try {
      const d = JSON.parse(e.data);
      appendFeed(d);
    } catch (err) {}
  });
  eventSource.addEventListener('heartbeat', e => {
    // ignore or show small heartbeat
  });
}

function fetchNow(){
  fetch('/api/live').then(r=>r.json()).then(data=>{
    document.getElementById('total-rev').innerText = '₹ ' + (data.revenue||0).toLocaleString();
    document.getElementById('total-orders').innerText = data.orders || 0;
    document.getElementById('progress').innerText = (data.progress||0) + '%';
    // systems
    const sys = data.systems || [];
    const sdiv = document.getElementById('systems-list'); sdiv.innerHTML='';
    sys.forEach((s,i)=> {
      const el = document.createElement('div');
      el.className='flex justify-between items-center p-2 border-b border-[rgba(255,255,255,0.03)]';
      el.innerHTML = `<div><div class="text-sm">${i+1}. ${s.name}</div><div class="text-xs text-gray-400">Success: ${s.success} • Fail: ${s.failure}</div></div><div class="text-sm">${s.last_success||'—'}</div>`;
      sdiv.appendChild(el);
    });
    // orders
    const orders = data.recent_orders || [];
    const odiv = document.getElementById('orders-list'); odiv.innerHTML='';
    orders.forEach(o => {
      const r = document.createElement('div');
      r.className = 'flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.02)]';
      r.innerHTML = `<div>${o.stream}</div><div>₹ ${o.amount}</div><div class="text-xs text-gray-400">${o.created_at}</div>`;
      odiv.appendChild(r);
    });
  }).catch(e=>console.error(e));
}

function appendFeed(ev){
  const feed = document.getElementById('feed');
  const el = document.createElement('div');
  el.className = 'feed-item';
  const when = new Date(ev.timestamp).toLocaleString();
  const sys = ev.payload.system && ev.payload.system.name ? ev.payload.system.name : 'system';
  el.innerHTML = `<div class="text-xs text-gray-400">${when}</div><div><strong>${sys}</strong> — ${ev.status}</div>`;
  feed.prepend(el);
  // keep max items
  while(feed.children.length>120) feed.removeChild(feed.lastChild);
}

function toggleChat(){ document.getElementById('chatbox').style.display = (document.getElementById('chatbox').style.display==='none') ? 'block':'none'; }
function sendChat(){
  const msg = document.getElementById('chat-msg').value;
  if(!msg) return;
  fetch('/api/chat',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: msg})})
    .then(r=>r.json()).then(j=>{
      // append user + bot replies
      const feed = document.getElementById('chat-feed');
      const u = document.createElement('div'); u.className='text-sm text-gray-200 mb-1'; u.innerText = 'You: ' + msg; feed.appendChild(u);
      const b = document.createElement('div'); b.className='text-sm text-green-300 mb-2'; b.innerText = 'JRAVIS: ' + (j.reply || '...'); feed.appendChild(b);
      feed.scrollTop = feed.scrollHeight;
      document.getElementById('chat-msg').value='';
    }).catch(e=>{ console.error(e); alert('chat send failed'); });
}

// test helper: insert a test order to dashboard db
function insertTestOrder(){
  fetch('/api/test_insert_order', { method:'POST' }).then(r=>r.json()).then(j=>{
    fetchNow();
    alert('Inserted test order: ₹' + j.amount);
  });
}

// on load: show locked state or dashboard if session unlocked
function init(){
  // assume locked by default
  showLocked(true);
}
window.onload = init;
</script>
</body>
</html>
"""


# ---------- Test insert order API ----------
@app.route("/api/test_insert_order", methods=["POST"])
def api_test_insert_order():
    # require unlocked session
    if not session.get("unlocked"):
        return jsonify({"error": "locked"}), 401
    amount = float(os.getenv("TEST_ORDER_AMOUNT", "1200"))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO orders (stream, amount) VALUES (?, ?)",
              ("Test Stream", amount))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "amount": amount})


# ---------- ROUTES (unlock, lockout, root, health) ----------
@app.before_request
def require_unlock():
    # allow these endpoints without unlocked session
    open_endpoints = ("unlock", "health", "api_live", "api_live_json",
                      "feed_stream", "api_live", "api_chat")
    # allow static-like endpoints (none served separately here)
    if request.endpoint in ("unlock", "health", "api_live", "feed_stream",
                            "api_chat", "api_test_insert_order", "api_live"):
        return None
    if not session.get("unlocked"):
        return redirect("/unlock")


@app.route("/unlock", methods=["GET", "POST"])
def unlock():
    if request.method == "POST":
        code = request.form.get("code") or request.get_json(
            silent=True) and request.get_json().get("code")
        if code == LOCK_CODE:
            session["unlocked"] = True
            # redirect to root (frontend will detect redirect as unlocked)
            return redirect("/")
        return ("", 401)
    # return minimal form to be posted by JS (we also accept application/x-www-form-urlencoded)
    return render_template_string("""
      <html><body style="background:#030712;color:#e6fbff;font-family:Inter,Arial;text-align:center;padding-top:120px;">
        <h2 style="color:#00ff88">🔒 JRAVIS Dashboard Locked</h2>
        <form method="post">
          <input name="code" type="password" placeholder="Enter lock code" style="padding:10px;border-radius:6px;background:#071021;color:white;border:1px solid #0f2430" />
          <button style="padding:10px 16px;margin-left:8px;background:#00ff88;border-radius:6px;color:black;border:none">Unlock</button>
        </form>
      </body></html>
    """)


@app.route("/lockout")
def lockout():
    session.clear()
    return redirect("/unlock")


@app.route("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.route("/")
def root():
    # serve the SPA frontend; client will POST to /unlock to unlock
    return render_template_string(FRONTEND, refresh=REFRESH_SECONDS)


# ---------- BOOT ----------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"[JRAVIS] Dashboard v6 (upgraded) starting on port {port}")
    app.run(host="0.0.0.0", port=port)
