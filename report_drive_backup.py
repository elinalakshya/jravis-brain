# JRAVIS Phase-1.9 — Auto Upload Reports + Invoices to Google Drive
import os, io, json, glob
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CRED_JSON = os.getenv("GDRIVE_CREDENTIALS_JSON", "")
TARGET_FOLDER_ID = os.getenv("GDRIVE_TARGET_FOLDER_ID", "")
INVOICE_DIR = os.getenv("INVOICE_DIR", "./invoices")
REPORT_DIR = os.getenv("REPORT_DIR", ".")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def make_drive_service():
    info = json.loads(CRED_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=SCOPES)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def ensure_folder(service, parent_folder_id, name):
    q = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and '{parent_folder_id}' in parents and trashed=false"
    res = service.files().list(q=q, fields="files(id)").execute()
    items = res.get("files", [])
    if items:
        return items[0]["id"]
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id]
    }
    return service.files().create(body=meta, fields="id").execute()["id"]


def upload_file(service, path, folder_id):
    media = MediaFileUpload(path, resumable=True)
    meta = {"name": os.path.basename(path), "parents": [folder_id]}
    service.files().create(body=meta, media_body=media, fields="id").execute()
    print("Uploaded:", os.path.basename(path))


def collect_files(date_obj, days=1):
    files = []
    date_str = date_obj.strftime("%d-%m-%Y")
    for f in glob.glob(os.path.join(REPORT_DIR, f"{date_str}_*.pdf")):
        files.append(f)
    for d in range(days):
        folder = os.path.join(
            INVOICE_DIR, (date_obj - timedelta(days=d)).strftime("%Y-%m-%d"))
        if os.path.isdir(folder):
            files += glob.glob(os.path.join(folder, "*.pdf"))
    return files


def backup_for_date(days=1):
    if not CRED_JSON or not TARGET_FOLDER_ID:
        print("Missing GDRIVE credentials or folder ID")
        return
    date_obj = datetime.now().date()
    service = make_drive_service()
    folder_id = ensure_folder(service, TARGET_FOLDER_ID,
                              date_obj.strftime("%Y-%m-%d"))
    files = collect_files(date_obj, days)
    if not files:
        print("No files found for upload.")
        return
    for f in files:
        try:
            upload_file(service, f, folder_id)
        except Exception as e:
            print("Failed to upload", f, e)


if __name__ == "__main__":
    backup_for_date()
