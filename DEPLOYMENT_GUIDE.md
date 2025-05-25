# 🚀 Tableau Governance Framework - Production Deployment Guide

## Overview

This guide walks through deploying the Tableau Server governance automation framework in a production environment. The framework provides automated compliance monitoring, policy enforcement, and resource optimization across multi-site Tableau deployments.

## Pre-Deployment Checklist

### 1. Environment Requirements

**Server Requirements:**
- Linux/Windows Server with Python 3.8+
- Network access to Tableau Server
- Minimum 2GB RAM, 10GB disk space
- Scheduled task/cron capabilities

**Tableau Server Requirements:**
- Tableau Server 2021.4+ (REST API v3.5+)
- Personal Access Token (PAT) enabled
- Site Administrator or Server Administrator privileges

**Network Requirements:**
- HTTPS access to Tableau Server (port 443)
- Optional: SMTP access for email alerts (port 587/465)
- Optional: Internet access for Slack notifications

### 2. Security Setup

**Create Tableau PAT:**
1. Login to Tableau Server as admin
2. Go to Account Settings → Personal Access Tokens
3. Create new token with name: `governance-automation`
4. Save token name and secret securely

**Set up service account (recommended):**
- Create dedicated service account for automation
- Grant minimum required permissions (Site Admin)
- Use this account for PAT generation

## Installation Steps

### 1. Download and Setup
```bash
# Clone or extract the framework
cd /opt  # or your preferred directory
git clone <repository> tableau-governance
cd tableau-governance

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor
```

**Required environment variables:**
```bash
# Tableau Server Configuration
TABLEAU_SERVER_URL=https://your-tableau-server.domain.com
TABLEAU_TOKEN_NAME=governance-automation
TABLEAU_TOKEN_SECRET=your-secret-token-here
TABLEAU_SITE_ID=""  # Empty for multi-site scanning

# Logging Configuration
LOG_LEVEL=INFO

# Optional: Email Notifications
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=587
EMAIL_FROM=tableau-bot@yourdomain.com
EMAIL_TO=tableau-admin@yourdomain.com

# Optional: Slack Notifications
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#tableau-alerts
```

### 3. Validate Installation
```bash
# Run test suite
python run_tests.py

# Test connectivity
python log_stale_users.py

# Verify log output
ls -la logs/
cat logs/governance.log
```

## Production Configuration

### 1. File Permissions
```bash
# Set appropriate permissions
chmod 750 /opt/tableau-governance
chmod 640 .env
chmod 755 *.py
chmod 755 logs/

# Create logs directory if needed
mkdir -p logs
```

### 2. Log Rotation Setup

**Linux (logrotate):**
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/tableau-governance

# Add content:
/opt/tableau-governance/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### 3. Scheduled Execution

**Linux (cron):**
```bash
# Edit crontab for service account
crontab -e

# Add governance scans (daily at 2 AM)
0 2 * * * cd /opt/tableau-governance && /opt/tableau-governance/venv/bin/python log_stale_users.py
15 2 * * * cd /opt/tableau-governance && /opt/tableau-governance/venv/bin/python log_stale_content.py
30 2 * * * cd /opt/tableau-governance && /opt/tableau-governance/venv/bin/python log_stale_sites.py
45 2 * * * cd /opt/tableau-governance && /opt/tableau-governance/venv/bin/python log_extracts.py

# Weekly summary report (Mondays at 8 AM)
0 8 * * 1 cd /opt/tableau-governance && /opt/tableau-governance/venv/bin/python report_summary.py
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task: "Tableau Governance - Users"
3. Trigger: Daily at 2:00 AM
4. Action: Start Program
   - Program: `C:\path\to\tableau-governance\venv\Scripts\python.exe`
   - Arguments: `log_stale_users.py`
   - Start in: `C:\path\to\tableau-governance`
5. Repeat for other scripts

## Monitoring and Alerting

### 1. Log Monitoring

**Grafana Loki Integration:**
```bash
# Install Promtail on the server
# Configure promtail.yml:
server:
  http_listen_port: 9080

positions:
  filename: /var/lib/promtail/positions.yaml

clients:
  - url: http://your-loki-server:3100/loki/api/v1/push

scrape_configs:
  - job_name: tableau-governance
    static_configs:
      - targets:
          - localhost
        labels:
          job: tableau-governance
          __path__: /opt/tableau-governance/logs/governance.log
```

**ELK Stack Integration:**
```bash
# Filebeat configuration for log shipping
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /opt/tableau-governance/logs/governance.log
  json.keys_under_root: true
  json.overwrite_keys: true
  fields:
    service: tableau-governance
    environment: production
```

### 2. Performance Monitoring

**Key Metrics to Monitor:**
- Scan duration (should be < 5 minutes for most deployments)
- Item counts (watch for sudden spikes)
- Error rates (should be < 1%)
- Log file sizes

**Alert Conditions:**
- Any ERROR level log entries
- Scan duration > 10 minutes
- No scans completed in 25 hours
- Authentication failures

### 3. Health Check Script

Create `health_check.py`:
```python
#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

def check_recent_scans():
    """Check if scans have run recently."""
    logs_dir = Path("logs")
    yesterday = datetime.now() - timedelta(days=1)
    
    scan_types = ["inactive_users", "stale_content", "stale_sites", "extract_tasks"]
    
    for scan_type in scan_types:
        pattern = f"{scan_type}_*.json"
        files = list(logs_dir.glob(pattern))
        
        if not files:
            print(f"ERROR: No {scan_type} logs found")
            return False
            
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
        
        if file_time < yesterday:
            print(f"ERROR: {scan_type} not run recently (last: {file_time})")
            return False
            
        print(f"OK: {scan_type} last run: {file_time}")
    
    return True

if __name__ == "__main__":
    if check_recent_scans():
        print("Health check: PASS")
        sys.exit(0)
    else:
        print("Health check: FAIL")
        sys.exit(1)
```

## Security Hardening

### 1. Environment Security
```bash
# Restrict .env file access
chmod 600 .env
chown tableau-service:tableau-service .env

# Use systemd service for better security (Linux)
sudo nano /etc/systemd/system/tableau-governance.service
```

**Systemd service example:**
```ini
[Unit]
Description=Tableau Governance Scanner
After=network.target

[Service]
Type=oneshot
User=tableau-service
Group=tableau-service
WorkingDirectory=/opt/tableau-governance
ExecStart=/opt/tableau-governance/venv/bin/python log_stale_users.py
EnvironmentFile=/opt/tableau-governance/.env

[Install]
WantedBy=multi-user.target
```

### 2. Network Security
- Use TLS 1.2+ for Tableau Server connections
- Consider VPN for external deployments
- Whitelist IP addresses on Tableau Server if possible
- Use internal DNS names when available

### 3. Credential Management
- Store PAT in external secret management (HashiCorp Vault, AWS Secrets Manager)
- Rotate PAT tokens regularly (quarterly recommended)
- Monitor PAT usage in Tableau Server logs
- Use least-privilege principles for service account

## Disaster Recovery

### 1. Backup Strategy
```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backup/tableau-governance/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup configuration and scripts
cp -r /opt/tableau-governance/*.py "$BACKUP_DIR/"
cp /opt/tableau-governance/.env "$BACKUP_DIR/env.backup"
cp /opt/tableau-governance/requirements.txt "$BACKUP_DIR/"

# Backup recent logs (last 30 days)
find /opt/tableau-governance/logs -name "*.json" -mtime -30 -exec cp {} "$BACKUP_DIR/" \;

echo "Backup completed: $BACKUP_DIR"
```

### 2. Recovery Procedures
1. **Configuration Loss**: Restore from backup, verify credentials
2. **Log Loss**: Historical data lost, but scans will create new logs
3. **Server Migration**: Update TABLEAU_SERVER_URL, test connectivity
4. **Credential Compromise**: Generate new PAT, update configuration

## Troubleshooting

### Common Issues

**Authentication Errors:**
```bash
# Check PAT validity
curl -X POST "https://your-server/api/3.5/auth/signin" \
  -H "Content-Type: application/json" \
  -d '{"credentials":{"personalAccessTokenName":"your-token","personalAccessTokenSecret":"your-secret","site":{"contentUrl":""}}}'
```

**Network Connectivity:**
```bash
# Test server connectivity
telnet your-tableau-server.com 443
nslookup your-tableau-server.com
```

**Permission Issues:**
```bash
# Check file permissions
ls -la /opt/tableau-governance/
ls -la /opt/tableau-governance/.env
ls -la /opt/tableau-governance/logs/
```

**Memory Issues:**
```bash
# Monitor memory usage during scans
top -p $(pgrep -f "python.*log_")
```

### Support Information

**Log Locations:**
- Application logs: `logs/governance.log`
- Scan results: `logs/*_YYYY-MM-DD.json`
- System logs: `/var/log/syslog` (Linux) or Event Viewer (Windows)

**Debug Mode:**
```bash
LOG_LEVEL=DEBUG python log_stale_users.py
```

This will provide detailed information about API calls, timing, and internal operations.

## Success Metrics

After deployment, monitor these KPIs:
- **Scan Coverage**: All sites successfully scanned daily
- **Data Quality**: Consistent item counts and metadata
- **Performance**: Scan completion within expected timeframes
- **Reliability**: >99% successful scan rate
- **Security**: No credential exposure or authentication failures

The framework is successfully deployed when it provides consistent, reliable governance data for compliance reporting and policy enforcement across your Tableau Server environment.