# Preparing the rest of the script templates with logging functionality for stale content, sites, and extracts.

log_stale_content = """\
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
    json.dump(stale_workbooks, f, indent=2)

print(f"Logged {len(stale_workbooks)} stale workbooks to {log_file}")
"""

log_stale_sites = """\
import tableauserverclient as TSC
import datetime
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "cleanup_config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

SERVER_URL = "https://your-tableau-server"
TOKEN_NAME = "your-pat-name"
TOKEN_SECRET = "your-pat-secret"

DAYS_STALE = config.get("stale_site_days", 365)
LOG_DIR = os.path.join(os.path.dirname(__file__), config.get("log_path", "../logs/"))
os.makedirs(LOG_DIR, exist_ok=True)
cutoff_date = datetime.datetime.now() - datetime.timedelta(days=DAYS_STALE)

auth = TSC.PersonalAccessTokenAuth(TOKEN_NAME, TOKEN_SECRET)
server = TSC.Server(SERVER_URL, use_server_version=True)

stale_sites = []

with server.auth.sign_in(auth):
    all_sites, _ = server.sites.get()
    for site in all_sites:
        if site.admin_mode == 'ContentOnly' and site.content_url != "":
            # Assume last modified as proxy for usage
            last_updated = site.updated_at or site.created_at
            if last_updated and last_updated < cutoff_date:
                stale_sites.append({
                    "site_name": site.name,
                    "site_id": site.id,
                    "content_url": site.content_url,
                    "last_updated": last_updated.isoformat(),
                    "days_stale": (datetime.datetime.now() - last_updated).days
                })

log_file = os.path.join(LOG_DIR, f"stale_sites_{datetime.datetime.now().date()}.json")
with open(log_file, "w") as f:
    json.dump(stale_sites, f, indent=2)

print(f"Logged {len(stale_sites)} stale sites to {log_file}")
"""

log_extracts = """\
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

with server.auth.sign_in(auth):
    all_tasks, _ = server.tasks.get()
    for task in all_tasks:
        if isinstance(task, TSC.TaskItem) and hasattr(task, "extract_refresh"):
            extract_logs.append({
                "task_id": task.id,
                "schedule_id": task.schedule_id,
                "workbook_id": getattr(task, 'workbook_id', 'unknown'),
                "datasource_id": getattr(task, 'datasource_id', 'unknown'),
                "priority": task.priority,
                "type": "Extract Refresh"
            })

log_file = os.path.join(LOG_DIR, f"extract_tasks_{datetime.datetime.now().date()}.json")
with open(log_file, "w") as f:
    json.dump(extract_logs, f, indent=2)

print(f"Logged {len(extract_logs)} extract refresh tasks to {log_file}")
"""

# Write scripts
scripts = {
    "log_stale_content.py": log_stale_content,
    "log_stale_sites.py": log_stale_sites,
    "log_extracts.py": log_extracts
}

script_dir = "/mnt/data/tableau_cleanup/scripts"
for name, code in scripts.items():
    with open(os.path.join(script_dir, name), "w") as f:
        f.write(code)
