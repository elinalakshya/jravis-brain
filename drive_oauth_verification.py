# JRAVIS OAuth Verification — Phase 1.9
# Connects JRAVIS directly to your Google Drive using personal Gmail OAuth
import os, io, json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

print("🚀 [JRAVIS Drive OAuth Verification] Starting check...\n")

# Scopes define what access JRAVIS has to your Drive
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Step 1: Load OAuth client info from Replit secret
creds_json = os.getenv("GDRIVE_OAUTH_CLIENT_JSON")
if not creds_json:
    print("❌ Missing OAuth client JSON (GDRIVE_OAUTH_CLIENT_JSON).")
    exit()

client_info = json.loads(creds_json)

# Step 2: Authenticate (or reuse existing token)
token_path = "token.json"
creds = None

if os.path.exists(token_path):
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
else:
    flow = InstalledAppFlow.from_client_config(client_info, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(token_path, "w") as token:
        token.write(creds.to_json())

print(
    "✅ Authentication successful! JRAVIS is now connected to your Google Drive."
)

# Step 3: Upload a test file
service = build("drive", "v3", credentials=creds)

folder_id = os.getenv("GDRIVE_TARGET_FOLDER_ID")
if not folder_id:
    print(
        "⚠️ No folder ID found (GDRIVE_TARGET_FOLDER_ID). Uploading to My Drive root."
    )
    folder_id = None

content = io.BytesIO(b"JRAVIS Drive OAuth Verification Successful!")
file_metadata = {
    "name":
    f"JRAVIS_Verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
}
if folder_id:
    file_metadata["parents"] = [folder_id]

media = MediaIoBaseUpload(content, mimetype="text/plain")

try:
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields="id, name").execute()
    print(f"✅ Test file uploaded: {file.get('name')} (ID: {file.get('id')})")
    print("\n🎯 JRAVIS Drive integration verified successfully via OAuth!")
except Exception as e:
    print("\n❌ Upload failed:")
    print(e)
