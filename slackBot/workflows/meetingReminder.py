import json as js
from datetime import datetime as dt
import os
from slack_bolt.workflows.step import WorkflowStep


#? Define the workflow for sending the meeting reminder
workflow = WorkflowStep.builder("meetingReminder")

@workflow.edit
def edit_messageReminder(ack, configure):
	ack()
 
	blocks = [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "Message Sender Settings"
			}
		},
		{
			"type": "context",
			"elements": [
				{
					"type": "plain_text",
					"text": "This workflow is for IVCRC ONLY! Messages here will be sent only to the IVCRC general chat. No configuration available."
				}
			]
		}
	]
	configure(blocks=blocks)

@workflow.save
def save_messageReminder(ack, update):
	ack()
	update()
	
@workflow.execute
def execute_messageReminder(client, complete, fail):
	"""Executes on the time trigger. This function will send a message to the IVCRC general chat
	with the weekly meeting reminder message depending on the information provided by the chair.
	If the chair, did not submit anything, it will send a message saying that the chair did not
	complete the form and tag the chair in all variable fields.

	Args:
		All arguments are passed from the Slack Bolt listner API.
	"""
 
	with open("settings.json", "r") as f:
		settings = js.load(f)
 
	# Read the default msg
	reminderMsg = settings["REMINDER_MSG"]

	# Try to read the weekly reminder info
	try:
		with open(f"./env/{dt.now().strftime('%m-%d-%Y')}-weeklyReminderInfo.json", "r") as f:
			info = js.load(f)
	
		msg = "<!channel> " + info["msgBlurb"] + "\n" + f"This week's meeting will be led by <@{info['meetingLeader']}> and food will be provided by <@{info['foodProvider']}>!" + "\n\n" + reminderMsg
	# If the file does not exist, then that means the chair did not fill out the form
	except:
		# Remove the message from the chair dm
		with open(f"./env/{dt.now().strftime('%m-%d-%Y')}-chairReminderMsg.txt", "r") as f:
			tts = f.read()

		client.chat_delete(
		channel=settings["SLACK_IVCRC_CHAIR_USER_ID"],
		ts=tts
		)

		os.remove(f"./env/{dt.now().strftime('%m-%d-%Y')}-chairReminderMsg.txt")

		# Send a new confirmation message to the chair
		client.chat_postMessage(
		channel=settings["SLACK_IVCRC_CHAIR_USER_ID"],
		text=f"You were too late and did not complete the form for {dt.now().strftime('%m/%d/%Y')} on time! :("
		)
  
		msg = f"<!channel> This week's meeting will be led by <@{settings['SLACK_IVCRC_CHAIR_USER_ID']}> and food will be provided by <@{settings['SLACK_IVCRC_CHAIR_USER_ID']}>! (The Chair did not fill out the information in time)" + "\n\n" + reminderMsg

	try:
		client.chat_postMessage(
			channel=settings["SLACK_IVCRC_GENERAL_CHANNEL_ID"],
			text = msg
		)
  
		complete()

	except:
		error = {"message": "messageReminder.execute:: Message send failed."}
		fail(error=error)
  
	os.remove(f"./env/{dt.now().strftime('%m-%d-%Y')}-weeklyReminderInfo.json")
