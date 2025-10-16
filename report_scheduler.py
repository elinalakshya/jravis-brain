import smtplib, os, schedule, time
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime

import sys, traceback

sys.stdout.reconfigure(line_buffering=True)

print(">>> Debug: Mission 2040 worker starting (Render test)", flush=True)

try:
  # the rest of your code goes here
  LOCK_CODE = os.getenv("LOCK_CODE", "204040")
  EMAIL_USER = os.getenv("EMAIL_USER")
  EMAIL_PASS = os.getenv("App_password")
  RECEIVER = os.getenv("DAILY_REPORT_EMAIL")
except Exception as e:
  traceback.print_exc()
  sys.exit(1)


def generate_summary_pdf():
  pdf = FPDF()
  pdf.add_page()
  pdf.set_font("Arial", "B", 16)
  pdf.cell(200, 10, "Mission 2040 – Daily Summary Report", ln=True, align="C")
  pdf.set_font("Arial", size=12)
  pdf.multi_cell(
      0, 10, f"""
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Status: Automated Daily Summary
Progress: Phase 1 systems operational
""")
  file_name = f"{datetime.now().strftime('%d-%m-%Y')}_summary_report.pdf"
  pdf.output(file_name)
  return file_name


def generate_invoice_pdf():
  pdf = FPDF()
  pdf.add_page()
  pdf.set_font("Arial", "B", 16)
  pdf.cell(200, 10, "Mission 2040 – Daily Invoices", ln=True, align="C")
  pdf.set_font("Arial", size=12)
  pdf.multi_cell(0, 10, "Invoices for all income streams will appear here.")
  file_name = f"{datetime.now().strftime('%d-%m-%Y')}_invoices.pdf"
  pdf.output(file_name)
  return file_name


def send_email_with_pdfs():

  def send_email_with_pdfs():
    print("📧 Preparing Mission 2040 Daily Report email...", flush=True)

    msg = EmailMessage()
    msg["Subject"] = f"Mission 2040 Daily Report - {datetime.now().strftime('%d-%m-%Y')}"
    msg["From"] = EMAIL_USER
    msg["To"] = RECEIVER

    # 🔹 Paste this block right here:
    html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mission 2040 Daily Report</title>
        <style>
          body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f6f8;
            color: #222;
            margin: 0;
            padding: 0;
          }}
          .container {{
            max-width: 600px;
            margin: 40px auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
          }}
          .header {{
            background: linear-gradient(135deg,#0072ff,#00c6ff);
            padding: 24px;
            color: #fff;
            text-align: center;
          }}
          .header h1 {{
            margin: 0;
            font-size: 22px;
            letter-spacing: 1px;
          }}
          .content {{
            padding: 24px;
            line-height: 1.6;
          }}
          .button {{
            display: inline-block;
            background: #0072ff;
            color: #fff !important;
            padding: 12px 24px;
            margin: 20px 0;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
          }}
          .button:hover {{
            background: #005cd6;
          }}
          .footer {{
            background: #f0f0f0;
            color: #555;
            text-align: center;
            font-size: 12px;
            padding: 12px;
          }}
        </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🚀 Mission 2040 Daily Report</h1>
            </div>
            <div class="content">
              <p>Dear Boss,</p>
              <p>Your <strong>Mission 2040 Daily Report</strong> is ready.</p>
              <p>
                The attached PDF is <strong>encrypted</strong> with your Lock Code:
                <span style="background:#eee;padding:2px 6px;border-radius:4px;">{LOCK_CODE}</span>.
              </p>
              <p>Review today’s summary and approve to let VA Bot continue its automated operations.</p>

              <p style="text-align:center;">
                <a href="https://jravis-dashboard.onrender.com" class="button" target="_blank">✅ Approve Work</a>
              </p>

              <p>Stay consistent — every action today builds your 2040 vision. 🌍</p>
              <p>With focus & automation,<br><strong>Dhruvayu — Your Mission 2040 AI Companion</strong></p>
            </div>
            <div class="footer">
              <p>© {datetime.now().year} Team Lakshya | Automated Report by JRAVIS Brain</p>
            </div>
          </div>
        </body>
        </html>
        """

    # Now attach it to the email:
    msg.set_content(
        "Your Mission 2040 Daily Report is attached. Please open the PDF using your Lock Code."
    )
    msg.add_alternative(html_body, subtype="html")

    # (Then continue with your existing PDF attachment + send logic)

  summary_file = generate_summary_pdf()
  invoice_file = generate_invoice_pdf()

  msg = EmailMessage()
  msg["From"] = EMAIL_USER
  msg["To"] = RECEIVER
  msg["Subject"] = f"Mission 2040 Daily Report – {datetime.now().strftime('%d-%m-%Y')}"
  msg.set_content(f"Attached are today's reports.\nLock Code: {LOCK_CODE}")

  for file in [summary_file, invoice_file]:
    with open(file, "rb") as f:
      msg.add_attachment(f.read(),
                         maintype="application",
                         subtype="pdf",
                         filename=file)

  with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
    smtp.starttls()
    smtp.login(EMAIL_USER, EMAIL_PASS)
    smtp.send_message(msg)
    print("✅ Daily report emailed successfully.")


# ⏰ Schedulers
schedule.every().day.at("10:00").do(send_email_with_pdfs)
schedule.every().sunday.at("00:00").do(send_email_with_pdfs)

print("📅 JRAVIS Daily/Weekly Report Scheduler Running...", flush=True)

while True:
  print("⏳ Checking schedule...", flush=True)
  schedule.run_pending()
  time.sleep(30)

# 🔽 Temporary manual trigger for testing
# send_email_with_pdfs()
