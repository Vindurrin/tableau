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
    json.dump({
        "summary": f"{len(stale_sites)} stale sites found",
        "count": len(stale_sites),
        "sites": stale_sites
    }, f, indent=2)

print(f"Logged {len(stale_sites)} stale sites to {log_file}")
