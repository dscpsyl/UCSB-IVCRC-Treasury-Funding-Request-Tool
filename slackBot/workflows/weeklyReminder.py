import json as js
from datetime import datetime as dt
from slack_bolt.workflows.step import WorkflowStep


#? Define the workflow for asking the chair to specify weekly variables
workflow = WorkflowStep.builder("weeklyReminderOptions")

@workflow.edit
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

@workflow.save
def save_weeklyReminderWorkflow(ack, update):
	"""Becasue there is nothing to update in the settings,
 this function does nothing.
	"""
 
	ack()
	update()

@workflow.execute
def execute_weeklyReminderWorkflow(client, complete, fail):
	"""This function will send a message to the IVCRC Internal-Chair
 	Slack account with a message asking it to trigger a modal to update
 	the weekly meeting message variables. It will save the message tts
 	to a file named the date.txt in the env folder. 

	Args:
		All arguments are passed from the Slack Bolt listner API.
	"""

	blocks = [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": f"Hello! Please complete the following form to update the weekly meeting reminder message for {dt.now().strftime('%m/%d/%y')} at least an 24 hours before the meeting time!"
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
	
	with open("settings.json", "r") as f:
		settings = js.load(f)


	try:
		tts = client.chat_postMessage(
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
