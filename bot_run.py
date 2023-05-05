# For this app, we will be using socket mode to connect to Slack
import json as js
import os
from datetime import datetime as dt
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.workflows.step import WorkflowStep

#* Import the workflows
from slackBot.workflows import weeklyReminder, meetingReminder

#* Load the settings file
settings = js.load(open("settings.json", "r"))

#* Create the app
app = App(token=settings["SLACK_BOT_TOKEN"])

#* Apply the weekly meeting reminders workflow
app.step(weeklyReminder.workflow)
app.step(meetingReminder.workflow)

#* Modal for the chair to update the weekly meeting reminder
@app.action("chairReminderForm")
def modal_chairReminderForm(ack, body):
	"""Action function to open the modal for the chair to update the weekly meeting reminder msg variables.

	Args:
		All arguments are passed from the Slack Bolt listner API.
	"""
 
	ack()
	
	app.client.views_open(
	 
		trigger_id = body["trigger_id"],
  
		view = {"type": "modal",
				"callback_id": "weeklyMeetingReminderForm",
				"title": {"type": "plain_text", "text": "IVCRC Reminder Form"},
				"submit": {"type": "plain_text","text": "Submit"},
				"close": {"type": "plain_text","text": "Cancel"},
				
				"blocks": [{
					"type": "header",
					"text": {
		 				"type": "plain_text",
						"text": "Let's get some information about this week's meeting!",
						}},{
					"type": "input",
					"block_id": "weeklyMeetingLeaderBlock",
					"optional": False,
					"element": {
						"type": "users_select",
						"placeholder": {
							"type": "plain_text",
							"text": "Select IVCRC Chair"
						},
					"action_id": "weeklyMeetingLeader"
					},
					"label": {
						"type": "plain_text",
						"text": "Who will be leading the meeting this week?",
					}},
	  				{"type": "divider"},
					{
					"type": "input",
					"block_id": "weeklyFoodProviderBlock",
					"optional": False,
					"element": {
						"type": "users_select",
						"placeholder": {
							"type": "plain_text",
							"text": "Select IVCRC member",
	   					},
					"action_id": "weeklyFoodProvider"
					},
					"label": {
						"type": "plain_text",
						"text": "Who will be ordering food for this week's meeting?",
					}},
					{"type": "divider"},
					{
					"type": "input",
					"block_id": "reminderBlurbBlock",
					"optional": True,
					"element": {
						"type": "plain_text_input",
						"multiline": True,
						"action_id": "reminderBlurb"
					},
					"label": {
						"type": "plain_text",
						"text": "Is there something you'd like to mention with the meeting reminder this week?",
	  				}}
	 			]
	   	}
	)

#* Updates to the weekly meeting reminder message after modal is submitted
@app.view("weeklyMeetingReminderForm")
def handle_view_submission_events(ack, body):
	"""Listens for the chair to submit the weekly meeting reminder form and then updates the message with the new variables.

	Args:
		All arguments are passed from the Slack Bolt listner API.
	"""
    
	ack()
	
	# Open and read the form msg ts from the file
	with open(f"./env/{dt.now().strftime('%m-%d-%Y')}-chairReminderMsg.txt", "r") as f:
		tts = f.read()
	
	# Delete the message from the chair    
	app.client.chat_delete(
		channel=settings["SLACK_IVCRC_CHAIR_USER_ID"],
		ts=tts
	)
	
	# Send a new confirmation message to the chair
	app.client.chat_postMessage(
		channel=settings["SLACK_IVCRC_CHAIR_USER_ID"],
		text=f"Thank you for completing the form for {dt.now().strftime('%m/%d/%Y')}!"

	)
	
	# Delete the file
	os.remove(f"./env/{dt.now().strftime('%m-%d-%Y')}-chairReminderMsg.txt")
	
	# Grab the three revelant pieces of data from the form
	meetingLeader = body["view"]["state"]["values"]["weeklyMeetingLeaderBlock"]["weeklyMeetingLeader"]["selected_user"]
	foodProvider = body["view"]["state"]["values"]["weeklyFoodProviderBlock"]["weeklyFoodProvider"]["selected_user"]
	msgBlurb = body["view"]["state"]["values"]["reminderBlurbBlock"]["reminderBlurb"]["value"]
	
	if msgBlurb == None:
		msgBlurb = ""
	
	info = {"meetingLeader": meetingLeader, "foodProvider": foodProvider, "msgBlurb": msgBlurb}
	
	# Write info to temp file
	with open(f"./env/{dt.now().strftime('%m-%d-%Y')}-weeklyReminderInfo.json", "w") as f:
		js.dump(info, f, indent=4)

########################################################################################!

#! Define the workflow for sending the member report message to open modal
memberReport = WorkflowStep.builder("memberReport")

@memberReport.edit
def edit_memberReport(ack, configure):
	pass

@memberReport.save
def save_memberReport(ack, step, update):
	pass

@memberReport.execute
def execute_memberReport(step, complete, fail):
	pass

app.step(memberReport)

#! Define the handeling of modal opening for member reports

#! Define the updates for member reports modal submissions

# Run the App
if __name__ == "__main__":
	SocketModeHandler(app, settings["SLACK_APP_TOKEN"]).start()