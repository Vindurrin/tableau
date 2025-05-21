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

DAYS_STALE = config.get("stale_content_days", 730)
LOG_DIR = os.path.join(os.path.dirname(__file__), config.get("log_path", "../logs/"))
os.makedirs(LOG_DIR, exist_ok=True)
cutoff_date = datetime.datetime.now() - datetime.timedelta(days=DAYS_STALE)

auth = TSC.PersonalAccessTokenAuth(TOKEN_NAME, TOKEN_SECRET, SITE_ID)
server = TSC.Server(SERVER_URL, use_server_version=True)

stale_workbooks = []

with server.auth.sign_in(auth):
    all_workbooks, _ = server.workbooks.get()
    for wb in all_workbooks:
        if wb.updated_at and wb.updated_at < cutoff_date:
            stale_workbooks.append({
                "name": wb.name,
                "project": wb.project_name,
                "owner_id": wb.owner_id,
                "updated_at": wb.updated_at.isoformat(),
                "days_stale": (datetime.datetime.now() - wb.updated_at).days,
                "site_id": SITE_ID
            })

log_file = os.path.join(LOG_DIR, f"stale_content_{datetime.datetime.now().date()}.json")
with open(log_file, "w") as f:
    json.dump({
        "summary": f"{len(stale_workbooks)} stale workbooks found",
        "count": len(stale_workbooks),
        "workbooks": stale_workbooks
    }, f, indent=2)

print(f"Logged {len(stale_workbooks)} stale workbooks to {log_file}")
