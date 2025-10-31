# JRAVIS Phase-1.9 OAuth Token Saver — Manual Code Paste
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json

TOKEN_FILE = "token.json"
CLIENT_SECRET_FILE = "client_secret.json"  # your OAuth client JSON file
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

print("🔑 JRAVIS OAuth Token Setup (Manual Mode)")
print("Paste your authorization code from the browser below ⬇️\n")

auth_code = input("Enter code: ").strip()

from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
flow.fetch_token(code=auth_code)

creds = flow.credentials

# Save token securely
with open(TOKEN_FILE, "w") as token:
    token.write(creds.to_json())

print("\n✅ JRAVIS OAuth token saved successfully!")
print(f"Saved to: {os.path.abspath(TOKEN_FILE)}")

# Test upload (optional)
try:
    service = build("drive", "v3", credentials=creds)
    print("✅ Google Drive API connected successfully.")
except Exception as e:
    print("❌ Connection test failed:", e)
