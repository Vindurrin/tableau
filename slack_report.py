from slack_sdk import WebClient
import os
import datetime

SLACK_TOKEN = "xoxb-your-token"
SLACK_CHANNEL = "#tableau-alerts"

today = datetime.datetime.now().date()
summary_file = os.path.join(os.path.dirname(__file__), f"../logs/daily_summary_{today}.txt")

with open(summary_file, "r") as f:
    body = f.read()

client = WebClient(token=SLACK_TOKEN)
response = client.chat_postMessage(channel=SLACK_CHANNEL, text=f"```{body}```")

if response["ok"]:
    print("Posted to Slack.")
else:
    print("Slack post failed:", response)
