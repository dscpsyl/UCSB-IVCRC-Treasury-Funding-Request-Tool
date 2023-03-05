from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

#? GOOGLE: Takes in a list of scopes to retrieve token for access. Should only be called MAX once per runtime.
def authToken(_Scope):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('env/token.json'):
        creds = Credentials.from_authorized_user_file('env/token.json', _Scope)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'res/credentials.json', _Scope)
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('env/token.json', 'w') as token:
                token.write(creds.to_json())
    return creds


#? SLACK: Returns the client object for use
def clientMake(settings):
    client = WebClient(token=settings["SLACK_BOT_TOKEN"])
    
    return client