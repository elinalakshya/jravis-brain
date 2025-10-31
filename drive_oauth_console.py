# drive_oauth_console.py  — Replit-safe manual flow
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRET_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

print("🚀 JRAVIS OAuth manual mode starting...")

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)

# Create auth URL and show it
auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
print("\n📡 Visit this URL to authorize:")
print(auth_url)
print(
    "\nAfter authorizing, copy the code (the page shows a code or redirects).")

code = input("\nPaste the authorization code here: ").strip()

# Exchange for token
flow.fetch_token(code=code)

creds = flow.credentials
with open("token.json", "w") as f:
    f.write(creds.to_json())

print("\n✅ token.json saved. You are done.")
