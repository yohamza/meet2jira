import io
import re
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
    Finds the newest Google Doc.
    
    Logic:
    1. If folder_id is 'root' (default): Search GLOBALLY for files named "Notes By Gemini".
       This covers 'Shared with me', 'Shared Drives', and 'My Drive'.
    2. If folder_id is specific (e.g., '123abc...'): Search only inside that folder.
    """
    creds = get_credentials()
    if not creds:
        return None, None

    try:
        drive_service = build('drive', 'v3', credentials=creds)

        # 1. Search for the newest Google Doc in the specified folder
        # We query for files in that folder, that are Google Docs, and aren't trashed.
        base_query = "mimeType='application/vnd.google-apps.document' and trashed=false"

        if folder_id == 'root':
            # "Search Mode": Find "Notes By Gemini" anywhere (Shared or My Drive)
            print("Searching ALL Drive (Shared/Personal) for 'Notes By Gemini'...")
            query = f"name contains 'Notes By Gemini' and {base_query}"
        else:
            # "Folder Mode": Strict search inside a specific folder
            print(f"Searching inside folder ID: {folder_id}...")
            query = f"'{folder_id}' in parents and {base_query}"
        
        response = drive_service.files().list(
            q=query,
            orderBy="createdTime desc",  # Get the newest file first
            pageSize=1,
            fields="files(id, name)",
            supportsAllDrives=True, 
            includeItemsFromAllDrives=True  # We only need the ID and name
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

def extract_id_from_url(url):
    """
    Parses a Google Doc URL to find the file ID.
    """
    # Pattern looks for text between '/d/' and the next forward slash
    pattern = r"/document/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def get_transcript_by_id(doc_id):
    """
    Downloads a specific Google Doc by its ID.
    Returns: (doc_name, transcript_text)
    """
    creds = get_credentials()
    if not creds:
        return None, None

    try:
        drive_service = build('drive', 'v3', credentials=creds)

        # 1. Get file metadata (we need the name for the DB)
        file_meta = drive_service.files().get(
            fileId=doc_id,
            supportsAllDrives=True
        ).execute()
        doc_name = file_meta.get('name')

        # 2. Download content
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
        
        print(f"Downloaded specific file: '{doc_name}'")
        return doc_name, transcript_text

    except HttpError as err:
        print(f"An error occurred: {err}")
        return None, None