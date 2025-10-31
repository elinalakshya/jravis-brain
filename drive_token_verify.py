# ✅ JRAVIS Drive Token Verification (ASCII-safe)
import os, io, json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload

TOKEN_FILE = "token.json"

if not os.path.exists(TOKEN_FILE):
    print("❌ token.json not found. Please run drive_oauth_auto.py first.")
    exit()

creds = Credentials.from_authorized_user_file(
    TOKEN_FILE, ["https://www.googleapis.com/auth/drive.file"])

try:
    service = build("drive", "v3", credentials=creds)
    print("✅ Connected to Google Drive successfully.")

    # Upload a small verification file
    test_content = io.BytesIO(b"JRAVIS OAuth Drive Test Successful")
    file_metadata = {"name": "JRAVIS_OAuth_Test.txt"}
    media = MediaIoBaseUpload(test_content, mimetype="text/plain")

    uploaded = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields="id, name").execute()

    print(f"📤 Uploaded file: {uploaded['name']} (ID: {uploaded['id']})")

except Exception as e:
    print("❌ Drive verification failed:")
    print(e)
