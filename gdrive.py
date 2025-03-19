import os
import json
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account

# Define Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Authenticate and return the Google Drive API service."""
    service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def upload_db(db_path, folder_id):
    """Upload SQLite database to Google Drive."""
    service = get_drive_service()
    file_metadata = {'name': os.path.basename(db_path), 'parents': [folder_id]}
    media = MediaFileUpload(db_path, mimetype='application/x-sqlite3', resumable=True)
    
    files = service.files().list(q=f"name='{os.path.basename(db_path)}' and '{folder_id}' in parents", fields="files(id)").execute()
    existing_files = files.get('files', [])
    
    if existing_files:
        file_id = existing_files[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
        print("✅ Database updated on Google Drive.")
    else:
        service.files().create(body=file_metadata, media_body=media).execute()
        print("✅ Database uploaded to Google Drive.")

def download_db(db_path, folder_id):
    """Download SQLite database from Google Drive."""
    service = get_drive_service()
    
    files = service.files().list(q=f"name='{os.path.basename(db_path)}' and '{folder_id}' in parents", fields="files(id)").execute()
    existing_files = files.get('files', [])
    
    if existing_files:
        file_id = existing_files[0]['id']
        request = service.files().get_media(fileId=file_id)
        
        with open(db_path, 'wb') as f:
            f.write(request.execute())
        print("✅ Database downloaded from Google Drive.")
    else:
        print("⚠️ No database found on Google Drive. Creating a new one.")
