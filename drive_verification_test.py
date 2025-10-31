# JRAVIS Drive Verification – Fixed Version
import os, io, json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

print("🚀 [JRAVIS Drive Verification] Starting check...\n")

try:
    creds_json = os.getenv("GDRIVE_CREDENTIALS_JSON")
    folder_id = os.getenv("GDRIVE_TARGET_FOLDER_ID")

    if not creds_json or not folder_id:
        raise Exception(
            "Missing credentials or folder ID in environment variables.")

    creds = service_account.Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"
        ])
    service = build("drive", "v3", credentials=creds)

    print("✅ Google credentials loaded successfully.")

    # Check access by listing inside the folder instead of files().get()
    results = service.files().list(q=f"'{folder_id}' in parents",
                                   fields="files(id, name)",
                                   pageSize=1).execute()

    print(f"✅ Connected to Drive folder: {folder_id}")

    # Upload a test file
    content = io.BytesIO(b"JRAVIS Drive Verification Successful!")
    file_metadata = {
        "name":
        f"JRAVIS_Verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(content, mimetype="text/plain")

    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields="id").execute()
    print(f"✅ Test file uploaded: {file.get('id')}")

    print("\n🎯 JRAVIS Drive integration verified successfully!")

except Exception as e:
    print("\n❌ Drive verification failed:")
    print(e)
