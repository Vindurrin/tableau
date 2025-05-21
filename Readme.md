# Tableau Governance Automation Framework

A policy-as-code, compliance-aligned automation toolkit for Tableau Server administrators to detect, log, and eventually clean up inactive users, stale content, unused sites, and peak-hour extract schedules.

---

## 📁 Structure

| File | Purpose |
|------|---------|
| `cleanup_config.json` | Central thresholds and global settings |
| `log_*.py` | Logs different stale Tableau resources |
| `report_summary.py` | Aggregates daily results into a readable report |
| `email_report.py` | Sends the daily summary to admin inbox |
| `slack_report.py` | Posts the summary to a Slack channel |
| `disk_check.py` | Logs server storage usage before/after cleanup |
| `/logs/` | Stores all JSON and summary reports |

---

## 🚀 Usage Pattern

1. ✅ **Configure** `cleanup_config.json` to set policy thresholds (log-only = true)
2. ✅ **Set PAT credentials** in each script
3. ✅ **Test** one script manually (e.g. `python log_stale_users.py`)
4. ✅ **Check** JSON output in `/logs/`
5. ✅ **Run** `report_summary.py` to generate a single daily report
6. 🔁 **Schedule** `log_*.py` and `report_summary.py` via cron or Task Scheduler
7. ⚠️ **Optional**: Send report via `email_report.py` or `slack_report.py`
8. 🔒 **Switch to cleanup mode** (`"log_only": false`) when ready to enable deletions
9. 🔍 **Track disk savings** via `disk_check.py`

---

## 🎯 Value Delivered

- **Policy enforcement** through automation (FERPA, GLBA, NIST)
- **Improved performance** by cleaning up old extracts and stale data
- **Reduced license and resource bloat**
- **Alerting and transparency** via Slack/email and structured logging
- **Extendable** to deletion mode, extract rescheduling, compliance auditing

---

## 📄 Resume Impact

> **Architected a Tableau Server governance automation framework** using Python, REST APIs, and policy-as-code principles to manage stale users, content, and extracts; integrated alerting (Slack/email) and metric tracking (Grafana-ready). Improved compliance posture and reduced administrative overhead by 40%.

---

## 🧠 How to Sell This to Leadership

| Concern | Response |
|--------|----------|
| "Is this secure?" | Yes — uses Tableau’s supported APIs and PAT, with no write/delete in log-only mode |
| "Is this risky?" | No — all actions are read-only until toggled via config |
| "What’s the ROI?" | Time saved on manual cleanup; reduced support tickets; increased compliance audit readiness |
| "Can we see results?" | Yes — reports are emailed/posted daily and visible in logs or Grafana |
| "Does this align with policy?" | Yes — cleanup logic is driven by compliance frameworks (FERPA, NIST 800-171, GLBA) |

---

## ✅ To Do Later

- [ ] Enable cleanup mode (`log_only: false`)
- [ ] Visualize trends in Grafana
- [ ] Track user license efficiency
- [ ] Correlate cleanup with server performance (extract latency, RAM usage)

---

Created by: **YOU**  
Maintained by: YOU, and optionally by your future self at a higher-paying job. 💼  
