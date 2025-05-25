# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a **production-ready Tableau Server governance automation framework** that uses policy-as-code principles to manage stale resources across multi-site deployments. The system operates in **log-only** (safe discovery) and **cleanup mode** (automated deletion) with enterprise-grade security, logging, and error handling.

### Core Components

**Foundation Layer:**
- **`config.py`** - Secure configuration with environment variable support
- **`tableau_client.py`** - Shared base client with multi-site scanning, retry logic, and structured logging
- **`logger.py`** - Enterprise structured logging with JSON output for SIEM integration
- **`retry_utils.py`** - Resilient API operations with exponential backoff

**Governance Scripts:**
- **`log_stale_users.py`** - Multi-site inactive user detection  
- **`log_stale_content.py`** - Workbook and datasource staleness analysis
- **`log_stale_sites.py`** - Site-level activity monitoring
- **`log_extracts.py`** - Extract schedule optimization analysis

**Legacy Support:**
- **`report_summary.py`, `email_report.py`, `slack_report.py`** - Existing reporting (needs refactor)
- **`cleanup_config.json`** - Legacy config (supplemented by environment variables)

### Key Design Patterns

1. **Security-First**: Environment variables for credentials, no secrets in code
2. **Multi-Site Aware**: All scripts scan across ALL sites in the deployment
3. **Enterprise Logging**: Structured JSON logs with correlation IDs and performance metrics
4. **Resilient Operations**: Automatic retry logic with exponential backoff
5. **Standardized Output**: Consistent JSON schema across all governance operations
6. **Safe-by-Default**: Log-only mode prevents destructive actions until explicitly enabled

## Development Commands

### Setup and Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your Tableau Server credentials
```

### Testing
```bash
# Run full test suite
python run_tests.py

# Run specific test files
python -m pytest tests/test_config.py -v
python -m pytest tests/test_logger.py -v
```

### Running Governance Scripts
```bash
# Multi-site user analysis
python log_stale_users.py

# Multi-site content analysis
python log_stale_content.py

# Site-level activity analysis
python log_stale_sites.py

# Extract schedule optimization
python log_extracts.py
```

### Configuration

**Environment Variables (Required):**
```bash
TABLEAU_SERVER_URL=https://your-tableau-server.domain.com
TABLEAU_TOKEN_NAME=your-pat-name
TABLEAU_TOKEN_SECRET=your-pat-secret
TABLEAU_SITE_ID=""  # Empty for multi-site operations
```

**Optional Configuration:**
```bash
LOG_LEVEL=INFO
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL=#tableau-alerts
SMTP_SERVER=smtp.yourdomain.com
EMAIL_FROM=tableau-bot@yourdomain.com
EMAIL_TO=admin@yourdomain.com
```

### Log Output

**Structured JSON logs:**
- **Application logs**: `logs/governance.log` (structured JSON for SIEM)
- **Scan results**: `logs/{scan_type}_YYYY-MM-DD.json` (governance data)

**Integration with monitoring:**
- Grafana Loki: Use `logs/governance.log` with Promtail
- ELK Stack: Filebeat can ingest the JSON logs directly
- Splunk: HEC ingestion of structured logs

### Production Deployment

**Security Checklist:**
- ✅ Environment variables configured (no hardcoded credentials)
- ✅ Log directory permissions set appropriately
- ✅ Network connectivity to Tableau Server verified
- ✅ PAT permissions validated (site admin or server admin)

**Monitoring Setup:**
- Configure log rotation (built-in: 10MB files, 5 backups)
- Set up alerting on error-level log entries
- Monitor scan duration and item counts for anomalies

**Scheduling (Linux/cron example):**
```bash
# Daily governance scans at 2 AM
0 2 * * * cd /path/to/tableau && python log_stale_users.py
15 2 * * * cd /path/to/tableau && python log_stale_content.py
30 2 * * * cd /path/to/tableau && python log_stale_sites.py
45 2 * * * cd /path/to/tableau && python log_extracts.py
```

### API Rate Limits and Retries

The framework includes automatic retry logic for:
- Network timeouts and connection errors
- Tableau Server rate limiting (429 errors)  
- Temporary server errors (5xx responses)
- Exponential backoff with jitter to prevent thundering herd

### Troubleshooting

**Common Issues:**
- **Authentication failures**: Verify PAT credentials and permissions
- **Site access errors**: Ensure PAT has appropriate site-level access
- **Network timeouts**: Check network connectivity and firewall rules
- **JSON parsing errors**: Verify log file permissions and disk space

**Debug Mode:**
```bash
LOG_LEVEL=DEBUG python log_stale_users.py
```

### Performance Optimization

**For large deployments:**
- Consider running scripts during off-peak hours
- Monitor memory usage for sites with many resources
- Use site-specific filtering if needed (modify scan functions)
- Configure appropriate timeouts for large data retrievals