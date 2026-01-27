import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Declare the scopes for Google Calendar and Tasks API
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks"
]


"""
Get Google API credentials, handling OAuth flow and token storage.
"""
def get_creds(credentials_path: str = "credentials.json",
              token_path: str = "token.json",):
    creds = None

    # Load existing token if available
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, initiate the OAuth flow
    if not creds or not creds.valid:

        # If credentials are expired but have a refresh token, refresh them
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        # Otherwise, start a new OAuth flow to get credentials
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            
            # Run the flow to get credentials (HEADLESS FOR NOW)
            # if not headless: flow.run_local_server(port=0)
            creds = flow.run_local_server(port=0)

            # Save the credentials for future use   
            with open(token_path, "w") as f:
                f.write(creds.to_json())
    
    return creds
