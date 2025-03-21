import os
import json
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Google Drive Configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_PATH = "credentials.json"
DB_PATH = "bazarbot.db"  # Define DB_PATH directly here

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_drive_service():
    """Authenticate and return the Google Drive API service."""
    if not os.path.exists(CREDENTIALS_PATH):
        logging.error("❌ credentials.json file not found! Make sure it exists.")
        return None

    try:
        with open(CREDENTIALS_PATH, "r") as file:
            service_account_info = json.load(file)

        creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        logging.error(f"❌ Failed to authenticate with Google Drive API: {e}")
        return None


def get_existing_file_id(service, file_name, folder_id):
    """Check if file exists in Google Drive and return its file ID."""
    try:
        results = service.files().list(
            q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
            fields="files(id)"
        ).execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None
    except Exception as e:
        logging.error(f"❌ Failed to check file existence in Google Drive: {e}")
        return None


def upload_db(db_path, folder_id):
    """Upload or replace the SQLite database on Google Drive."""
    service = get_drive_service()
    if not service:
        return

    file_name = os.path.basename(db_path)
    if not os.path.exists(db_path):
        logging.warning("⚠️ Database file not found! Creating a new one...")
        open(db_path, 'w').close()

    try:
        media = MediaFileUpload(db_path, mimetype='application/x-sqlite3', resumable=True)
        existing_file_id = get_existing_file_id(service, file_name, folder_id)

        if existing_file_id:
            logging.info("🔄 Updating database on Google Drive...")
            service.files().update(fileId=existing_file_id, media_body=media).execute()
        else:
            logging.info("🆕 Uploading new database to Google Drive...")
            service.files().create(body={'name': file_name, 'parents': [folder_id]}, media_body=media).execute()
        logging.info("✅ Database uploaded successfully!")
    except Exception as e:
        logging.error(f"❌ Failed to upload database: {e}")


def download_db(db_path, folder_id):
    """Download the SQLite database from Google Drive and replace local file."""
    service = get_drive_service()
    if not service:
        return

    file_name = os.path.basename(db_path)
    file_id = get_existing_file_id(service, file_name, folder_id)

    if not file_id:
        logging.error(f"❌ Database file '{file_name}' not found in Google Drive!")
        return

    try:
        request = service.files().get_media(fileId=file_id)
        with open(db_path, "wb") as db_file:
            downloader = MediaIoBaseDownload(db_file, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        logging.info("✅ Database downloaded successfully!")
    except Exception as e:
        logging.error(f"❌ Failed to download database: {e}")
