import tableauserverclient as TSC
import datetime
import json
import os

# Load configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "cleanup_config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

SERVER_URL = "https://your-tableau-server"
SITE_ID = ""  # Default site
TOKEN_NAME = "your-pat-name"
TOKEN_SECRET = "your-pat-secret"

DAYS_INACTIVE = config.get("stale_user_days", 365)
LOG_ONLY = config.get("log_only", True)
LOG_DIR = os.path.join(os.path.dirname(__file__), config.get("log_path", "../logs/"))
os.makedirs(LOG_DIR, exist_ok=True)

auth = TSC.PersonalAccessTokenAuth(TOKEN_NAME, TOKEN_SECRET, SITE_ID)
server = TSC.Server(SERVER_URL, use_server_version=True)

inactive_users = []
cutoff_date = datetime.datetime.now() - datetime.timedelta(days=DAYS_INACTIVE)

with server.auth.sign_in(auth):
    all_users, _ = server.users.get()
    for user in all_users:
        if user.last_login and user.last_login < cutoff_date:
            inactive_users.append({
                "username": user.name,
                "full_name": user.fullname,
                "email": user.email or "N/A",
                "last_login": user.last_login.isoformat(),
                "days_inactive": (datetime.datetime.now() - user.last_login).days,
                "site_id": SITE_ID
            })

log_file = os.path.join(LOG_DIR, f"inactive_users_{datetime.datetime.now().date()}.json")
with open(log_file, "w") as f:
    json.dump({
        "summary": f"{len(inactive_users)} inactive users found",
        "count": len(inactive_users),
        "users": inactive_users
    }, f, indent=2)

print(f"Logged {len(inactive_users)} inactive users to {log_file}")
