import shutil
import json
import datetime
import os

disk_usage = shutil.disk_usage("/")
today = datetime.datetime.now().isoformat()

output = {
    "timestamp": today,
    "total_gb": round(disk_usage.total / (1024**3), 2),
    "used_gb": round(disk_usage.used / (1024**3), 2),
    "free_gb": round(disk_usage.free / (1024**3), 2)
}

log_path = os.path.join(os.path.dirname(__file__), "../logs/")
os.makedirs(log_path, exist_ok=True)
file_path = os.path.join(log_path, f"disk_check_{today[:10]}.json")

with open(file_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Disk usage logged to {file_path}")
