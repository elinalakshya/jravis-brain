#!/usr/bin/env python3
"""
YouTube OAuth helper for VA Bot (Manual OOB Flow)
- Works even if localhost redirect is blocked
- Shows a URL, you log in, copy the code, paste into Replit
- Saves refresh token to tmp/tokens.json
"""

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

TOKEN_FILE = Path("tmp/tokens.json")
TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "❌ Missing YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET in env")

# Force OOB style
creds_data = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
    }
}

flow = InstalledAppFlow.from_client_config(
    creds_data,
    scopes=["https://www.googleapis.com/auth/yt-analytics.readonly"])

# Generate the manual URL
auth_url, _ = flow.authorization_url(prompt="consent")
print("\n👉 Open this URL in any browser (Elina’s Google account):\n")
print(auth_url)
print(
    "\nAfter approval, Google will show you a one-time code. Copy and paste it below.\n"
)

# Ask for the code manually
code = input("Paste the authorization code here: ").strip()
flow.fetch_token(code=code)
creds = flow.credentials

with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

print("✅ YouTube OAuth completed. Token saved to", TOKEN_FILE)
