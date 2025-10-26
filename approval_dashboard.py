"""
approval_dashboard.py
Lightweight Flask dashboard for SecurityGuardV2 approvals.
Run:  python approval_dashboard.py
Then open http://127.0.0.1:3300/approvals
"""

from flask import Flask, render_template_string, redirect, url_for
from security_guard_v2 import SecurityGuardV2

sg = SecurityGuardV2()
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>JRAVIS Approval Dashboard</title>
  <style>
    body { font-family: sans-serif; margin: 2rem; background: #f5f6fa; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { padding: 0.6rem; border-bottom: 1px solid #ccc; text-align: left; }
    th { background: #eee; }
    button { padding: 0.3rem 0.8rem; border: none; border-radius: 6px; cursor: pointer; }
    .approve { background: #4caf50; color: white; }
    .deny { background: #f44336; color: white; }
  </style>
</head>
<body>
<h2>JRAVIS Approval Dashboard</h2>
<table>
  <tr><th>ID</th><th>Description</th><th>Amount</th><th>Currency</th><th>Status</th><th>Action</th></tr>
  {% for aid, rec in approvals.items() %}
  <tr>
    <td>{{ aid }}</td>
    <td>{{ rec.desc }}</td>
    <td>{{ rec.amount }}</td>
    <td>{{ rec.currency }}</td>
    <td>{{ rec.status }}</td>
    <td>
      <form action="{{ url_for('approve', aid=aid) }}" method="post" style="display:inline;">
        <button class="approve">Approve</button>
      </form>
      <form action="{{ url_for('deny', aid=aid) }}" method="post" style="display:inline;">
        <button class="deny">Deny</button>
      </form>
    </td>
  </tr>
  {% endfor %}
</table>
</body>
</html>
"""


@app.route("/approvals")
def list_approvals():
  approvals = sg.list_pending()
  return render_template_string(HTML, approvals=approvals)


@app.route("/approve/<aid>", methods=["POST"])
def approve(aid):
  sg.approve(aid, "Boss", lock=os.getenv("SYSTEM_LOCK_CODE"))
  return redirect(url_for("list_approvals"))


@app.route("/deny/<aid>", methods=["POST"])
def deny(aid):
  sg.deny(aid, "Boss", "Denied via dashboard")
  return redirect(url_for("list_approvals"))


if __name__ == "__main__":
  import os
  port = int(os.getenv("APPROVAL_DASHBOARD_PORT", 3300))
  app.run(host="0.0.0.0", port=port)
