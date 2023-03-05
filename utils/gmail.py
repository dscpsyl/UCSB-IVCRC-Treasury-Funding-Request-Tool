from __future__ import print_function

import os.path
import sys
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# from googleapiclient.http import MediaFileUpload

import mimetypes
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import email.encoders
from email.message import EmailMessage

import logging as l
l.basicConfig(level=l.INFO, format='%(message)s')

#? takes in an html file as the message with other @params to draft up an email
def createEmailBody(senderEmail, receiverEmail, subject, htmlFile):
    with open(htmlFile, "r") as file:
        messageHTML = file.read()
                
    body = MIMEText(messageHTML, "html")
    body["Subject"] = subject
    body["From"] = senderEmail
    body["To"] = receiverEmail
    body = base64.urlsafe_b64encode(body.as_bytes())
    
    return {'message': {'raw': body.decode()}}

#? Takes in createEmailBody() @params with a path to attachment File
def createEmailBodyWithPdfAttachment(senderEmail, receiverEmail, subject, htmlFile, attachmentFile):
    with open(htmlFile, "r") as file:
        messageHTML = file.read()
    
    body = MIMEMultipart()
    body["subject"] = subject
    body["from"] = senderEmail
    body["to"] = receiverEmail
    
    msg = MIMEText(messageHTML, "html")
    body.attach(msg)

    content_type, encoding = mimetypes.guess_type(attachmentFile)
    main_type, sub_type = content_type.split('/', 1)
    
    fp = open(attachmentFile, 'rb')
    msg = MIMEBase(main_type, sub_type)
    msg.set_payload(fp.read())
    fp.close()
   
    
    filename = os.path.basename(attachmentFile)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    email.encoders.encode_base64(msg)
    body.attach(msg)
    body = base64.urlsafe_b64encode(body.as_bytes())
    
    return {'raw': body.decode()} 


#? Creates a draft on the user's account and returns the ID of that draft
def createDraft(userId, messageBody, creds):
    try:
        service = build('gmail', 'v1', credentials=creds)
        draft = service.users().drafts().create(userId=userId, body=messageBody).execute()
        
        
    except HttpError as error:
        l.error(f"{error}")
        sys.exit(1)
    
    return draft["id"]

def sendDraft(userId, draftId, creds):
    try:
        service = build('gmail', 'v1', credentials=creds)
        request = service.users().drafts().send(userId=userId,body = {"id" : draftId}).execute()
        response = request["id"]
        print(f"Sent Email with response id:{response}...")
    except HttpError as error:
        l.error(f"{error}")
        sys.exit(1)
