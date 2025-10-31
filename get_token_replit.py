from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
auth_url, _ = flow.authorization_url(prompt='consent')
print("\n🔗 Visit this URL and authorize access:\n", auth_url, "\n")
code = input("👉 Paste the authorization code here: ").strip()
flow.fetch_token(code=code)
creds = flow.credentials
with open("token.json", "w") as f:
    f.write(creds.to_json())
print("\n✅ token.json created successfully.\n")
