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
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            print("Credentials expired. Attempting refresh...")
            try:
                creds.refresh(Request())
                refreshed = True
                print("Credentials refreshed successfully.")
            except Exception as e:
                print(f"Refresh failed: {e}")

        if not refreshed:
            if creds and creds.expired:
                print("Token expired and refresh is not possible. Please log in again.")
            else:
                print("No valid credentials. Starting authentication flow...")

            # This line reads your credentials.json
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Try browser-based flow first; fall back to console flow if needed.
            try:
                creds = flow.run_local_server(port=0, open_browser=True)
            except Exception as e:
                print(f"Browser login failed: {e}")
                print("Falling back to console-based login. Follow the URL and paste the code here.")
                creds = flow.run_console()
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Saved new credentials to 'token.json'.")

    print("\nAuthentication successful!")
    print("You can now run the main 'run.py' server.")

if __name__ == '__main__':
    main()
