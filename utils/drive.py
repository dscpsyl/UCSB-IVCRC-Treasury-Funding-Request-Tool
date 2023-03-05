from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import logging as l
l.basicConfig(level=l.INFO, format='%(message)s')

#? takes in info and copies files already on drive
def driveCpy(fileId, newFileName, parentFolder, creds): 
    try:
        service = build('drive', 'v3', credentials=creds)
        
        dataTest = {
            "name": newFileName,
            "parents": [parentFolder],
        }
        request = service.files().copy(fileId=fileId, supportsAllDrives=True, fields="id",body=dataTest)
        response = request.execute()
        l.debug("Created new file with id: " + response["id"] + " ...")
        return response["id"]
    except HttpError as error:
        l.error(f"{error}")

#? takes in a file id and returns the file object for it with the specified fields
def driveFileInfo(fileId, creds, fields="*"):
    try:
        service = build('drive', 'v3', credentials=creds)
        
        request = service.files().get(fileId=fileId, supportsAllDrives=True, fields=fields)
        response = request.execute()
        return response
    except HttpError as error:
        l.error(f"{error}")

#? Takes in a file and folder and uploads it to the drive. Returns the fileId
def driveUP(file, parentFolder, fileName, creds):
    try:
        service = build('drive', 'v3', credentials=creds)
        body = {"name" : fileName, "parents" : [parentFolder]}
        media = MediaFileUpload(file)
        
        request = service.files().create(fields="id", supportsAllDrives=True, media_body=media, body=body)
        response = request.execute()
        return response["id"]
    except HttpError as error:
        l.error(f"{error}")
    
#? Move drive file to a new folder. Returns the id of the new file
def driveMV(fileId, newParent, creds):
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Get current parent ID
        _oldParent = driveFileInfo(fileId, creds, fields="parents")
        
        # Update the parent ID
        request = service.files().update(fileId=fileId, addParents=newParent, removeParents=_oldParent["parents"][0], supportsAllDrives=True)
        response = request.execute()
        return response["id"]
    except HttpError as error:
        l.error(f"{error}")    

#? Gets @params and returns raw bytes of the file
def driveEXPORT(fileId, MIMEType, creds):
    try:
        service = build('drive', 'v3', credentials=creds)
        request = service.files().export(fileId=fileId, mimeType=MIMEType)
        
        response = request.execute()
        return response
        
    except HttpError as error:
        l.error(f"{error}")
        
#? Gets @params and returns list of files in driveID
def driveLIST(corpora, driveID, fields, includeItemsFromAllDrives, orderBy, pageSize, pageToken, q, supportsAllDrives, creds):
    try:
        service = build('drive', 'v3', credentials=creds)
        request = service.files().list(corpora=corpora, driveId=driveID, fields=fields, includeItemsFromAllDrives=includeItemsFromAllDrives, orderBy=orderBy, pageSize=pageSize, pageToken=pageToken, q=q, supportsAllDrives=supportsAllDrives)
        
        response = request.execute()
        return response
        
    except HttpError as error:
        l.error(f"{error}")
        
#? @params to share to a new user
def shareFile(fileId, userId, type, role, creds):
    try:
        service = build('drive', 'v3', credentials=creds)
        permission = {
            "type": type,
            "role": role,
            "emailAddress": userId
        }
        request = service.permissions().create(fileId=fileId, fields='id', body=permission, supportsAllDrives=True)
        response = request.execute()
        return response
        
    except HttpError as error:
        l.error(f"{error}")