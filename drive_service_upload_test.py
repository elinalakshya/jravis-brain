#!/usr/bin/env python3
"""
JRAVIS Drive Service Uploader  (Mission Lock Enabled)
Mode: Service Account (no OAuth login)
Encryption: PDF password protection using Mission Lock Code
"""

import os
import sys
import argparse
import json
from datetime import datetime
from dateutil import tz
from PyPDF2 import PdfReader, PdfWriter
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# --------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
ROOT_FOLDER_NAME = "JRAVIS_Service_Drive"

# 🔐 Mission Lock Code (change anytime)
MISSION_LOCK_CODE = "2040LOCK"

# Folder structure inside Drive
FOLDER_STRUCTURE = {
    "Reports": ["Daily", "Weekly"],
    "Invoices": [],
    "Backups": [],
    "Logs": []
}

# Local file → Drive folder mapping
DEFAULT_UPLOAD_MAP = {
    "summary_report.pdf": "Reports/Daily",
    "invoices.pdf": "Invoices",
}


# --------------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------------
def auth():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


# --------------------------------------------------------
# PDF PASSWORD PROTECTION
# --------------------------------------------------------
def encrypt_pdf(input_path, password):
    """Create a password-protected copy of the PDF."""
    if not os.path.exists(input_path):
        print(f"[SKIP] Missing file for encryption: {input_path}")
        return None

    output_path = input_path.replace(".pdf", "_locked.pdf")
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password)
        with open(output_path, "wb") as f:
            writer.write(f)

        print(
            f"🔒 Encrypted {os.path.basename(input_path)} → {os.path.basename(output_path)}"
        )
        return output_path
    except Exception as e:
        print(f"[ERROR] Failed to encrypt {input_path}: {e}")
        return None


# --------------------------------------------------------
# DRIVE UTILITIES
# --------------------------------------------------------
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
    print(f"Created folder: {name}")
    return folder["id"]


def ensure_root(service):
    fid = find_folder(service, ROOT_FOLDER_NAME)
    if not fid:
        fid = create_folder(service, ROOT_FOLDER_NAME)
        print(f"Created root folder '{ROOT_FOLDER_NAME}'")
    return fid


def ensure_folder_path(service, path):
    parts = [p for p in path.split("/") if p]
    parent = ensure_root(service)
    for part in parts:
        fid = find_folder(service, part, parent_id=parent)
        if not fid:
            fid = create_folder(service, part, parent_id=parent)
        parent = fid
    return parent


def upload_file(service, local_path, drive_folder_id, replace_same_name=True):
    if not os.path.exists(local_path):
        print(f"[SKIP] File not found: {local_path}")
        return None

    filename = os.path.basename(local_path)
    safe_filename = filename.replace("'", "\\'")
    q = f"name = '{safe_filename}' and '{drive_folder_id}' in parents"
    existing = service.files().list(q=q,
                                    fields="files(id, name)").execute().get(
                                        "files", [])
    media = MediaFileUpload(local_path, resumable=True)

    if existing and replace_same_name:
        file_id = existing[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"Updated existing file: {filename}")
        return file_id
    else:
        meta = {"name": filename, "parents": [drive_folder_id]}
        uploaded = service.files().create(body=meta,
                                          media_body=media,
                                          fields="id").execute()
        print(f"Uploaded new file: {filename}")
        return uploaded["id"]


# --------------------------------------------------------
# MAIN LOGIC
# --------------------------------------------------------
def run_uploads(service, upload_map):
    ensure_root(service)
    for local_file, rel_folder in upload_map.items():
        locked_file = encrypt_pdf(local_file, MISSION_LOCK_CODE)
        if locked_file:
            folder_id = ensure_folder_path(service, rel_folder)
            upload_file(service, locked_file, folder_id)
    print("✅ All uploads complete.")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--test",
                   action="store_true",
                   help="Run in test mode with sample files")
    p.add_argument("--files",
                   nargs="*",
                   help="Local files to upload (used with --test)")
    p.add_argument("--map", help="Custom JSON mapping file")
    return p.parse_args()


def load_map(path):
    if not path:
        return DEFAULT_UPLOAD_MAP
    with open(path, "r") as f:
        return json.load(f)


def main():
    args = parse_args()
    service = auth()
    upload_map = load_map(args.map)

    if args.test:
        if not args.files:
            print("⚠️  Provide test files: --test --files file1.pdf file2.pdf")
            sys.exit(1)
        temp_map = {}
        if len(args.files) >= 1:
            temp_map[args.files[0]] = "Reports/Daily"
        if len(args.files) >= 2:
            temp_map[args.files[1]] = "Invoices"
        run_uploads(service, temp_map)
        print("🧪 TEST upload complete.")
    else:
        run_uploads(service, upload_map)


if __name__ == "__main__":
    main()
