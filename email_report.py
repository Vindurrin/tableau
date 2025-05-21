import smtplib
from email.mime.text import MIMEText
import os
import datetime

today = datetime.datetime.now().date()
summary_file = os.path.join(os.path.dirname(__file__), f"../logs/daily_summary_{today}.txt")

with open(summary_file, "r") as f:
    body = f.read()

msg = MIMEText(body)
msg['Subject'] = f"Tableau Cleanup Summary – {today}"
msg['From'] = "tableau-bot@yourdomain.edu"
msg['To'] = "your-email@yourdomain.edu"

# Replace with your SMTP server
SMTP_SERVER = "smtp.yourdomain.edu"

with smtplib.SMTP(SMTP_SERVER) as s:
    s.send_message(msg)

print("Email sent.")
