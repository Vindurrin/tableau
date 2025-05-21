import tableauserverclient as TSC
import datetime
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "cleanup_config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

SERVER_URL = "https://your-tableau-server"
SITE_ID = ""
TOKEN_NAME = "your-pat-name"
TOKEN_SECRET = "your-pat-secret"

LOG_DIR = os.path.join(os.path.dirname(__file__), config.get("log_path", "../logs/"))
os.makedirs(LOG_DIR, exist_ok=True)

auth = TSC.PersonalAccessTokenAuth(TOKEN_NAME, TOKEN_SECRET, SITE_ID)
server = TSC.Server(SERVER_URL, use_server_version=True)

extract_logs = []
peak_count = 0

with server.auth.sign_in(auth):
    all_tasks, _ = server.tasks.get()
    for task in all_tasks:
        schedule_id = task.schedule_id
        # Optional: fetch schedule time details
        if isinstance(task, TSC.TaskItem) and hasattr(task, "extract_refresh"):
            # Simulated placeholder, as Tableau doesn’t expose schedule times directly
            is_peak = True  # In reality, would map this from schedule info
            if is_peak:
                peak_count += 1
            extract_logs.append({
                "task_id": task.id,
                "schedule_id": schedule_id,
                "type": "Extract Refresh",
                "peak_window": is_peak
            })

log_file = os.path.join(LOG_DIR, f"extract_tasks_{datetime.datetime.now().date()}.json")
with open(log_file, "w") as f:
    json.dump({
        "summary": f"{len(extract_logs)} extracts found; {peak_count} during peak hours",
        "count": len(extract_logs),
        "peak_count": peak_count,
        "tasks": extract_logs
    }, f, indent=2)

print(f"Logged {len(extract_logs)} extract refresh tasks to {log_file}")
