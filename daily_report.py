# --- Add this list of recipients at the top where EMAIL is used ---
to_emails = ["elinalakshya2025@gmail.com", "nrveeresh327@gmail.com"]

# --- Replace this line ---
msg["To"] = ", ".join(to_emails)

# --- And in sendmail, replace EMAIL with to_emails ---
server.sendmail(EMAIL, to_emails, msg.as_string())
