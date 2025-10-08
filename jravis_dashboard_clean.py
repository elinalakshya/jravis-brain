from flask import Flask, render_template_string

app = Flask(__name__)

MAIN_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>JRAVIS Mission 2040</title>
</head>
<body style="font-family:sans-serif;background:#f6f8fa;margin:40px;">
  <h1>✅ JRAVIS Mission 2040 Dashboard</h1>
  <p>This is the clean version — no formatting, no errors.</p>
  <p>INR: {{ earn_inr }}</p>
  <p>USD: {{ earn_usd }}</p>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(MAIN_HTML, earn_inr="125000", earn_usd="1500")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Running JRAVIS Dashboard clean build on port {port}")
    app.run(host="0.0.0.0", port=port)
