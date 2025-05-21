import os
import json
import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "../logs/")
today = datetime.datetime.now().date()
summary = []

def load_log(file_prefix):
    file_path = os.path.join(LOG_DIR, f"{file_prefix}_{today}.json")
    if os.path.exists(file_path):
        with open(file_path) as f:
            data = json.load(f)
            return data.get("summary", "No summary"), data.get("count", 0)
    return f"No {file_prefix} log found", 0

log_types = ["inactive_users", "stale_content", "stale_sites", "extract_tasks"]

for log in log_types:
    log_summary, count = load_log(log)
    summary.append(f"{log.replace('_', ' ').title()}: {log_summary} (Count: {count})")

report_file = os.path.join(LOG_DIR, f"daily_summary_{today}.txt")
with open(report_file, "w") as f:
    f.write(f"Tableau Cleanup Summary – {today}\n\n")
    for line in summary:
        f.write(line + "\n")

print(f"Summary written to {report_file}")
