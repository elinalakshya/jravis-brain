#!/usr/bin/env python3
"""
Drive Sync Daemon for JRAVIS

- Polls local folders for new PDFs (summary_report.pdf, invoices.pdf, any *.pdf)
- Encrypts each PDF with Mission Lock Code (creates *_locked.pdf)
- Uploads locked PDF to Drive using Service Account credentials (credentials.json)
- Moves original and locked files to archive folders
- Has --once flag to run a single pass (useful for immediate testing)

Configurable at top of this file.
"""
import os
import time
import glob
import shutil
import argparse
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from PyPDF2 import PdfReader, PdfWriter

# ---------- CONFIG ----------
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
ROOT_FOLDER = "1TY3MseGj5GyWwOTk7A7QZ7aGZs1sFU16"  # Drive root (ensure shared)
LOCAL_WATCH_DIR = "./to_upload"  # Drop reports here
LOCAL_ARCHIVE_DIR = "./archive"  # Processed files go here
MISSION_LOCK_CODE = "2040LOCK"  # Change when needed
POLL_INTERVAL = 20  # seconds between checks
DEFAULT_MAP = {
    # local subfolder -> Drive path under ROOT_FOLDER
    "summary_report.pdf": "Reports/Daily",
    "invoices.pdf": "Invoices"
}
# ----------------------------


def auth():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_folder(service, name, parent_id=None):
    safe_name = name.replace("'", "\\'")
    q_parts = [
        f"name = '{safe_name}'",
        "mimeType = 'application/vnd.google-apps.folder'"
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
    # ensure root
    root_id = find_folder(service, ROOT_FOLDER)
    if not root_id:
        root_id = create_folder(service, ROOT_FOLDER)
    parent = root_id
    for part in parts:
        fid = find_folder(service, part, parent_id=parent)
        if not fid:
            fid = create_folder(service, part, parent_id=parent)
        parent = fid
    return parent


def upload_file_to_drive(service, local_path, drive_folder_id):
    filename = os.path.basename(local_path)
    safe_filename = filename.replace("'", "\\'")
    q = f"name = '{safe_filename}' and '{drive_folder_id}' in parents"
    existing = service.files().list(q=q,
                                    fields="files(id, name)").execute().get(
                                        "files", [])
    media = MediaFileUpload(local_path, resumable=True)
    if existing:
        fid = existing[0]["id"]
        service.files().update(fileId=fid, media_body=media).execute()
        print(f"[Drive] Updated {filename}")
        return fid
    else:
        meta = {"name": filename, "parents": [drive_folder_id]}
        uploaded = service.files().create(body=meta,
                                          media_body=media,
                                          fields="id").execute()
        print(f"[Drive] Uploaded {filename}")
        return uploaded["id"]


def encrypt_pdf(input_path, password):
    if not os.path.exists(input_path):
        return None
    out = input_path.replace(".pdf", "_locked.pdf")
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
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


def process_file(service, filepath):
    # encrypt
    locked = encrypt_pdf(filepath, MISSION_LOCK_CODE)
    if not locked:
        return False
    # decide drive folder
    name = os.path.basename(filepath)
    drive_path = DEFAULT_MAP.get(name, "Reports/Daily")
    folder_id = ensure_folder_path(service, drive_path)
    upload_file_to_drive(service, locked, folder_id)
    # archive originals and locked
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(LOCAL_ARCHIVE_DIR, exist_ok=True)
    dst_orig = os.path.join(LOCAL_ARCHIVE_DIR,
                            f"{ts}__{os.path.basename(filepath)}")
    dst_locked = os.path.join(LOCAL_ARCHIVE_DIR,
                              f"{ts}__{os.path.basename(locked)}")
    shutil.move(filepath, dst_orig)
    shutil.move(locked, dst_locked)
    print(f"[Archive] moved to {LOCAL_ARCHIVE_DIR}")
    return True


def run_once():
    service = auth()
    os.makedirs(LOCAL_WATCH_DIR, exist_ok=True)
    # find pdfs in LOCAL_WATCH_DIR (top-level only)
    files = glob.glob(os.path.join(LOCAL_WATCH_DIR, "*.pdf"))
    if not files:
        print("[Info] No PDFs found to process.")
    for f in files:
        try:
            process_file(service, f)
        except Exception as e:
            print("[Error] processing", f, e)


def run_daemon():
    print("[Daemon] Starting Drive Sync Daemon...")
    while True:
        try:
            run_once()
        except Exception as e:
            print("[Daemon][ERROR]", e)
        time.sleep(POLL_INTERVAL)


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--once",
                   action="store_true",
                   help="Run single pass and exit")
    return p.parse_args()


if __name__ == "__main__":
    args = parse()
    if args.once:
        run_once()
    else:
        run_daemon()
