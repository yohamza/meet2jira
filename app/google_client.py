import io
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# The 'token.json' file stores your access and refresh tokens.
TOKEN_FILE = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_credentials():
    """
    Gets valid user credentials from token.json.
    Refreshes the token if it's expired.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save the refreshed credentials
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        else:
            print("Error: 'token.json' is missing or invalid.")
            print("Please run 'python get_token.py' again to authenticate.")
            return None
    return creds

def get_transcript_from_folder(folder_id):
    """
    Finds the newest Google Doc in a specific folder and downloads it as text.
    
    Returns a tuple: (document_name, transcript_text) or (None, None)
    """
    creds = get_credentials()
    if not creds:
        return None, None

    try:
        drive_service = build('drive', 'v3', credentials=creds)

        # 1. Search for the newest Google Doc in the specified folder
        # We query for files in that folder, that are Google Docs, and aren't trashed.
        query = (
            f"'{folder_id}' in parents and "
            "mimeType='application/vnd.google-apps.document' and "
            "trashed=false"
        )
        
        response = drive_service.files().list(
            q=query,
            orderBy="createdTime desc",  # Get the newest file first
            pageSize=1,
            fields="files(id, name)"  # We only need the ID and name
        ).execute()

        files = response.get('files', [])
        if not files:
            print(f"No Google Docs found in folder: {folder_id}")
            return None, None
            
        doc = files[0]
        doc_id = doc['id']
        doc_name = doc['name']
        print(f"Found newest file: '{doc_name}' (ID: {doc_id})")

        # 2. Download that file as plain text
        # We use 'export_media' because we are converting a Google Doc to text.
        request = drive_service.files().export_media(
            fileId=doc_id,
            mimeType='text/plain'
        )
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")

        fh.seek(0)
        transcript_text = fh.read().decode('utf-8')
        
        # We return the doc_name to use as the 'meeting_code'
        return doc_name, transcript_text

    except HttpError as err:
        print(f"An error occurred: {err}")
        return None, None
