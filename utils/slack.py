import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import mimetypes
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

#https://slack.dev/python-slack-sdk/api-docs/slack_sdk/web/client.html
#https://api.slack.com/methods

import logging as l
l.basicConfig(level=l.INFO, format='%(message)s')

#? Takes in the message itself, setting file, and the client for @params and returns the ts of the msg
def sendTxtMsg(msg, channelId, slackClient):
    try:
        response = slackClient.chat_postMessage(
            channel=channelId,
            text = msg
        )
        return response["ts"]
    except SlackApiError as e:
        l.error(f"{e}")
        

#? Replies in thread with @params.
#TODO: Look into combining this with sendTxtMsg() 
def replyinThread(msg, thread, channelId, slackClient):
    try:
        response = slackClient.chat_postMessage(
            channel=channelId,
            text=msg,
            thread_ts=thread
        )
        return response["ts"]
    except SlackApiError as e:
        l.error(f"{e}")

#? Gets path to file and other @params and returns the ts of the new msg
def sendMsgWithAttachment(msg, file, fileName, channelId, slackClient, ts=None):    
    try:
        response = slackClient.files_upload(
            channels=channelId,
            file=file,
            filename=fileName,
            thread_ts=ts,
            initial_comment=msg
            )


        return response["file"]["id"]
    except SlackApiError as e:
        l.error(f"{e}")


def addPin(ts, channelId, slackClient):
    try:
        response = slackClient.pins_add(
            channel=channelId,
            timestamp=ts
        )
    except SlackApiError as e:
        l.error(f"{e}")
        
def removePin(ts, channelId, slackClient):
    try:
        response = slackClient.pins_remove(
            channel=channelId,
            timestamp=ts
        )
    except SlackApiError as e:
        l.error(f"{e}")