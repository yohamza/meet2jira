import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# This is the permission we need: to read files from your Google Drive.
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def main():
    """
    Runs the one-time authentication flow.
    It will open your browser and ask for permission.
    """
    creds = None
    
    # Check if we already have a token
    if os.path.exists('token.json'):
        print("Found existing 'token.json'. Loading credentials.")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Credentials expired. Refreshing...")
            creds.refresh(Request())
        else:
            print("No valid credentials. Starting authentication flow...")
            # This line reads your credentials.json
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # This line opens your browser for you
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Saved new credentials to 'token.json'.")

    print("\nAuthentication successful!")
    print("You can now run the main 'app.py' server.")

if __name__ == '__main__':
    main()
