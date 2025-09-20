sender_email = "youremail@gmail.com"  # your Gmail
app_password = "your_app_password"  # Gmail app password
client_email = "client@example.com"  # recipient email
invoice_no = "INV-1001"  # invoice number PDF to send

# Define PDF file name
pdf_file = f"Invoice_{invoice_no}.pdf"

# Debug print
print(f"Sending {pdf_file} to {client_email}")

import smtplib
from email.message import EmailMessage

# Create email
msg = EmailMessage()
msg['Subject'] = f"Invoice {invoice_no}"
msg['From'] = sender_email
msg['To'] = client_email
msg.set_content(
    f"Dear client,\n\nPlease find attached your invoice {invoice_no}.\n\nThanks!"
)

# Attach PDF
with open(pdf_file, 'rb') as f:
  msg.add_attachment(f.read(),
                     maintype='application',
                     subtype='pdf',
                     filename=pdf_file)

# Send email
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
  smtp.login(sender_email, app_password)
  smtp.send_message(msg)

print(f"Email sent successfully to {client_email} with {pdf_file} attached!")

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail login
email_sender = "your_email@gmail.com"
app_password = os.environ["APP_PASSWORD"]  # 🔑 loaded from Replit Secrets
email_receiver = "nrveeresh327@gamil.com"

# Email setup
msg = MIMEMultipart()
msg["From"] = email_sender
msg["To"] = email_receiver
msg["Subject"] = "Test Invoice Email"

body = "Boss, this is a test email sent from VA Bot."
msg.attach(MIMEText(body, "plain"))

# Gmail server
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
  server.login(email_sender, app_password)
  server.sendmail(email_sender, email_receiver, msg.as_string())

print("✅ Email sent successfully!")
