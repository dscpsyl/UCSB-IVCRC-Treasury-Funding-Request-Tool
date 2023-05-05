# For this app, we will be using socket mode to connect to Slack
import json as js
import os
from datetime import datetime as dt
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.workflows.step import WorkflowStep

# Load the settings file
settings = js.load(open("settings.json", "r"))

# Create the app
app = App(token=settings["SLACK_BOT_TOKEN"])

#? Define the workflow for asking the chair to specify weekly variables
weeklyReminderWorkflow = WorkflowStep.builder("weeklyReminderOptions")

@weeklyReminderWorkflow.edit
def edit_weeklyReminderWorkflow(ack, configure):
	"""This does not do much as it is only here to inform the user
 that there is nothing to be changed.
	"""
 
	ack()
	blocks = [
		{
			"type": "context",
			"elements": [
				{
					"type": "plain_text",
					"text": "There is nothing to edit here. This workflow does not have any options for the user to be able to change. Everything is handled internally or thorugh the workflow time trigger."
				}
			]
		}
	]
    
	configure(blocks=blocks)

@weeklyReminderWorkflow.save
def save_weeklyReminderWorkflow(ack, step, update):
	"""Becasue there is nothing to update in the settings,
 this function does nothing.
	"""
 
	ack()
	update()

@weeklyReminderWorkflow.execute
def execute_weeklyReminderWorkflow(step, complete, fail):
	"""This function will send a message to the IVCRC Internal-Chair
 Slack account with a message asking it to trigger a modal to update
 the weekly meeting message variables. It will save the message tts
 to a file named the date.txt in the env folder. 
	"""

	blocks = [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": f"Hello Chair! Please complete the following form to update the weekly meeting reminder message for {dt.now().strftime('%m/%d/%Y')} at least an 24 hours before the meeting time!"
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Complete Form",
					},
					"value": "click_me_123",
					"action_id": "chairReminderForm"
				}
			]
		}
	]



	try:
		tts = app.client.chat_postMessage(
			text=f"Hello Chair! Please complete the following form to update the weekly meeting reminder message for {dt.now().strftime('%m/%d/%Y')}!",
			blocks=blocks,		
			channel=settings["SLACK_IVCRC_CHAIR_USER_ID"]
		)

		with open(f"./env/{dt.now().strftime('%m-%d-%Y')}-chairReminderMsg.txt", "w") as f:
			f.write(tts["ts"])
  
		complete()
	except:
		error = "weeklyReminderWorkflow.execute:: Message send failed."
		fail(error=error)
  
app.step(weeklyReminderWorkflow)

#? Define the modal for the chair to update the weekly meeting reminder
@app.action("chairReminderForm")
def modal_chairReminderForm(ack, body, logger):
	"""Open the modal for the user to update the weekly meeting reminder
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

#? Define the updates to the weekly meeting reminder message after modal is submitted
@app.view("weeklyMeetingReminderForm")
def handle_view_submission_events(ack, body, logger):
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
    

#? Define the workflow for sending the meeting reminder
messageReminder = WorkflowStep.builder("meetingReminder")

@messageReminder.edit
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

@messageReminder.save
def save_messageReminder(ack, view, update):
	ack()
	update()
    
@messageReminder.execute
def execute_messageReminder(step, complete, fail):
	
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

		app.client.chat_delete(
		channel=settings["SLACK_IVCRC_CHAIR_USER_ID"],
		ts=tts
		)

		os.remove(f"./env/{dt.now().strftime('%m-%d-%Y')}-chairReminderMsg.txt")

    	# Send a new confirmation message to the chair
		app.client.chat_postMessage(
		channel=settings["SLACK_IVCRC_CHAIR_USER_ID"],
		text=f"You were too late and did not complete the form for {dt.now().strftime('%m/%d/%Y')} on time! :("
		)
  
		msg = f"<!channel> This week's meeting will be led by <@{settings['SLACK_IVCRC_CHAIR_USER_ID']}> and food will be provided by <@{settings['SLACK_IVCRC_CHAIR_USER_ID']}>! (The Chair did not fill out the information in time)" + "\n\n" + reminderMsg

	try:
		app.client.chat_postMessage(
            channel=settings["SLACK_IVCRC_GENERAL_CHANNEL_ID"],
            text = msg
        )
  
		complete()

	except:
		error = {"message": "messageReminder.execute:: Message send failed."}
		fail(error=error)
  
	os.remove(f"./env/{dt.now().strftime('%m-%d-%Y')}-weeklyReminderInfo.json")

app.step(messageReminder)


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