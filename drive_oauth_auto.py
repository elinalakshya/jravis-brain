# JRAVIS Phase-1.9 Auto OAuth — Permanent Google Drive Token Setup

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

print("🚀 [JRAVIS Drive Auto OAuth] Starting setup...")

# Start the OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)

# 🔁 Use run_local_server (works better in current versions)
creds = flow.run_local_server(
    host='localhost',
    port=8080,
    authorization_prompt_message='Please visit this link in your browser:',
    success_message='✅ Authorization complete! You can close this tab.',
    open_browser=True)

# Save the token
with open("token.json", "w") as token:
                              token.write(creds.to_json())

print("✅ Token saved successfully as token.json")

# Save the token for future runs
with open(TOKEN_FILE, "w") as token:
                              token.write(creds.to_json())

print("✅ Token saved successfully as token.json")

# Verify the connection
service = build("drive", "v3", credentials=creds)
about = service.about().get(fields="user,emailAddress").execute()
print(f"📂 Connected to Google Drive as: {about['user']['emailAddress']}")
