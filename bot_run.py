# For this app, we will be using socket mode to connect to Slack
import json as js
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.workflows.step import WorkflowStep

# Load the settings file
settings = js.load(open("settings.json", "r"))

# Create the app
app = App(token=settings["SLACK_BOT_TOKEN"])


#? Define the Message Sender Workflow Functions
def messageReminderEdit(ack, step, configure):
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
					"text": "This workflow is for IVCRC ONLY! Messages here will be sent only to the IVCRC general chat."
				}
			]
		},
		{
			"type": "divider"
		},
		{
			"type": "input",
            "block_id": "message_Set",
			"element": {
				"type": "plain_text_input",
				"multiline": True,
				"action_id": "messageInput"
			},
			"label": {
				"type": "plain_text",
				"text": "What would you like the message to say?"
			}
		}
    ]

    configure(blocks=blocks)

def messageReminderSave(ack, view, update):
    ack()
    
    values = view["state"]["values"]
    message = values["message_Set"]["messageInput"]["value"]
    
    settings["REMINDER_MSG"] = message
    
    with open("./settings.json", "w") as f:
        js.dump(settings, f, indent=4)
    
    update()

def messageReminderExecute(step, complete, fail):

    reminderMsg = settings["REMINDER_MSG"]
    
    try:
        app.client.chat_postMessage(
            channel=settings["SLACK_IVCRC_GENERAL_CHANNEL_ID"],
            text = reminderMsg
        )
        complete()
    except:
        error = {"message": "Message send failed."}
        fail(error=error)

messageReminder = WorkflowStep(
    callback_id="meetingReminder",
    edit=messageReminderEdit,
    save=messageReminderSave,
    execute=messageReminderExecute
    )


app.step(messageReminder)

# Run the App
if __name__ == "__main__":
    SocketModeHandler(app, settings["SLACK_APP_TOKEN"]).start()