#!/usr/bin/env python3
"""
JRAVIS Drive Sync Daemon (OAuth Mode)
-------------------------------------
Uploads locked PDF reports to *your* Google Drive using OAuth.
Works for personal Gmail (no Shared Drives required).

Usage:
  python drive_sync_daemon_oauth.py --once

First run will open a browser URL to authorize your account.
"""
import os
import time
import glob
import shutil
import argparse
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from PyPDF2 import PdfReader, PdfWriter

# --------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------
CREDENTIALS_FILE = "credentials.json"  # OAuth client JSON (downloaded from Google Cloud)
TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
ROOT_FOLDER_NAME = "JRAVIS_Service_Drive"
MISSION_LOCK_CODE = "2040LOCK"
LOCAL_WATCH_DIR = "./to_upload"
LOCAL_ARCHIVE_DIR = "./archive"
POLL_INTERVAL = 20

# Map for uploads
DEFAULT_MAP = {
    "summary_report.pdf": "Reports/Daily",
    "invoices.pdf": "Invoices",
}


# --------------------------------------------------------
# AUTH (OAuth user)
# --------------------------------------------------------
def auth():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            # use manual copy-paste mode
            auth_url, _ = flow.authorization_url(prompt='consent')
            print("\nPlease go to this URL in your browser:\n\n", auth_url,
                  "\n")
            code = input("Paste the authorization code here: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


# --------------------------------------------------------
# UTILITIES
# --------------------------------------------------------
def encrypt_pdf(input_path, password):
    if not os.path.exists(input_path):
        return None
    out = input_path.replace(".pdf", "_locked.pdf")
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(out, "wb") as f:
            writer.write(f)
        print(
            f"[Encrypt] {os.path.basename(input_path)} → {os.path.basename(out)}"
        )
        return out
    except Exception as e:
        print("[Encrypt][ERROR]", e)
        return None


def find_folder(service, name, parent_id=None):
    q_parts = [
        f"name = '{name}'", "mimeType = 'application/vnd.google-apps.folder'"
    ]
    if parent_id:
        q_parts.append(f"'{parent_id}' in parents")
    q = " and ".join(q_parts)
    res = service.files().list(q=q, fields="files(id, name)").execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None


def create_folder(service, name, parent_id=None):
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def ensure_folder_path(service, path):
    parts = [p for p in path.split("/") if p]
    parent = ensure_root(service)
    for part in parts:
        fid = find_folder(service, part, parent_id=parent)
        if not fid:
            fid = create_folder(service, part, parent_id=parent)
        parent = fid
    return parent


def ensure_root(service):
    fid = find_folder(service, ROOT_FOLDER_NAME)
    if not fid:
        fid = create_folder(service, ROOT_FOLDER_NAME)
        print(f"Created root folder '{ROOT_FOLDER_NAME}'")
    return fid


def upload_file(service, local_path, drive_folder_id):
    if not os.path.exists(local_path):
        print(f"[SKIP] Missing file: {local_path}")
        return
    name = os.path.basename(local_path)
    q = f"name='{name}' and '{drive_folder_id}' in parents"
    existing = service.files().list(q=q,
                                    fields="files(id, name)").execute().get(
                                        "files", [])
    media = MediaFileUpload(local_path, resumable=True)
    if existing:
        fid = existing[0]["id"]
        service.files().update(fileId=fid, media_body=media).execute()
        print(f"[Drive] Updated {name}")
    else:
        meta = {"name": name, "parents": [drive_folder_id]}
        service.files().create(body=meta, media_body=media,
                               fields="id").execute()
        print(f"[Drive] Uploaded {name}")


def process_file(service, path):
    locked = encrypt_pdf(path, MISSION_LOCK_CODE)
    if not locked:
        return
    name = os.path.basename(path)
    dest_folder = DEFAULT_MAP.get(name, "Reports/Daily")
    folder_id = ensure_folder_path(service, dest_folder)
    upload_file(service, locked, folder_id)
    os.makedirs(LOCAL_ARCHIVE_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.move(
        path, os.path.join(LOCAL_ARCHIVE_DIR,
                           f"{ts}__{os.path.basename(path)}"))
    shutil.move(
        locked,
        os.path.join(LOCAL_ARCHIVE_DIR, f"{ts}__{os.path.basename(locked)}"))
    print(f"[Archive] moved {name} to archive")


def run_once():
    service = auth()
    os.makedirs(LOCAL_WATCH_DIR, exist_ok=True)
    files = glob.glob(os.path.join(LOCAL_WATCH_DIR, "*.pdf"))
    if not files:
        print("[Info] No PDFs to process.")
        return
    for f in files:
        process_file(service, f)
    print("✅ All uploads complete.")


def run_daemon():
    while True:
        try:
            run_once()
        except Exception as e:
            print("[Daemon][ERROR]", e)
        time.sleep(POLL_INTERVAL)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    args = p.parse_args()
    if args.once:
        run_once()
    else:
        run_daemon()


if __name__ == "__main__":
    main()
