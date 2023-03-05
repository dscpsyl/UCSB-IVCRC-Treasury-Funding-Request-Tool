from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import logging as l
l.basicConfig(level=l.INFO, format='%(message)s')

#?Takes in list of params and then appends to it the data
def sheetsAppend(sheetID, data, insertDataOption, rang, creds):
    
    try:
        service = build('sheets', 'v4', credentials=creds)
        request = service.spreadsheets().values().append(spreadsheetId=sheetID, range=rang, valueInputOption="USER_ENTERED", insertDataOption=insertDataOption, body=data)
        response = request.execute()
        l.debug("Updated: " + response["spreadsheetId"])
    except HttpError as err:
        print(err)
    
    return 0

#? @params and returns values of sheets
def sheetsGet(sheetID, rang, creds, valueRenderOption="FORMULA"):
    try:
        service = build('sheets', 'v4', credentials=creds)
        request = service.spreadsheets().values().get(spreadsheetId=sheetID, range=rang, valueRenderOption=valueRenderOption)
        response = request.execute()
        return response
    except HttpError as err:
        print(err)
        return -1
        
def sheetUpdate(sheetID, data, rang, creds):
    try:
        service = build('sheets', 'v4', credentials=creds)
        request = service.spreadsheets().values().update(spreadsheetId=sheetID, range=rang, valueInputOption="USER_ENTERED", body=data)
        response = request.execute()
        l.debug("Updated: " + response["spreadsheetId"])
    except HttpError as err:
        print(err)
        return -1