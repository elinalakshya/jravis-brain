# JRAVIS Diagnostic: List accessible Google Drive folders
import os, json
from google.oauth2 import service_account
from googleapiclient.discovery import build

print("🚀 Checking accessible folders for JRAVIS service account...\n")

creds_json = os.getenv("GDRIVE_CREDENTIALS_JSON")
if not creds_json:
    print("❌ No GDRIVE_CREDENTIALS_JSON in environment.")
    exit()

creds = service_account.Credentials.from_service_account_info(
    json.loads(creds_json), scopes=["https://www.googleapis.com/auth/drive"])

service = build("drive", "v3", credentials=creds)

results = service.files().list(
    q="mimeType='application/vnd.google-apps.folder'",
    fields="files(id, name, owners/emailAddress)",
    pageSize=20).execute()

folders = results.get("files", [])
if not folders:
    print("⚠️ No folders visible to this account.")
else:
    print("✅ Folders visible to service account:\n")
    for f in folders:
        print(
            f"- {f['name']} ({f['id']}) [Owner: {f['owners'][0]['emailAddress']}]"
        )
