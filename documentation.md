# ✅ Tableau Server Governance Automation Summary

## 🧩 Overview

This automation framework enables **policy-driven cleanup** of Tableau Server environments, identifying and logging:
- Inactive users (based on last login)
- Stale content (old or unused workbooks)
- Inactive sites
- Peak-hour extract schedules

All findings are logged as structured JSON, rolled into a **daily summary report**, and optionally pushed to **email and Slack**. It runs on a schedule and is governed by a central config file (`cleanup_config.json`).

---

## 📁 Components

### 🛠️ Core Scripts
| Script | Function |
|--------|----------|
| `log_stale_users.py` | Logs users inactive for 365+ days |
| `log_stale_content.py` | Logs workbooks not updated in 730+ days |
| `log_stale_sites.py` | Logs unused Tableau sites |
| `log_extracts.py` | Logs extract refresh schedules, flags peak-hour jobs |

### 📤 Output
- Logs are saved in `/logs/` as `*.json`
- Daily digest is saved as `daily_summary_YYYY-MM-DD.txt`

### 🔁 Optional Extensions
| Script | Purpose |
|--------|---------|
| `report_summary.py` | Builds human-readable summary from log files |
| `email_report.py` | Emails the summary to admins |
| `slack_report.py` | Posts summary to Slack |
| `disk_check.py` | Logs disk usage before/after cleanup |

### 🔧 Configuration
- Controlled by `cleanup_config.json`
- Key settings:
  - `stale_user_days`: Days before a user is flagged
  - `log_only`: Toggle true/false for safe read-only mode vs active cleanup

---

## 🧪 Testing Plan (Safe on Test Server)

**Manual Run Steps**:
1. Install `tableauserverclient`, `slack_sdk`:
   ```bash
   pip install tableauserverclient slack_sdk
Set up PAT and server/site config in scripts

Run each log_*.py script manually

Review JSON logs

Run report_summary.py and check output

Optionally test email_report.py and slack_report.py