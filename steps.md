🧱 Full Process with Refinement
Step	Action
Step 0	✅ Prep PATs + access — Make sure the Personal Access Token and site configuration (SAML, auth domain, etc.) are valid on test Tableau Server
Step 1	✅ Split out Python scripts — Each one handles users, content, sites, extracts independently
Step 2	✅ Assess cleanup_config.json — Ensure thresholds match policy (e.g. 365 days) and output paths exist
Step 3	✅ Run on test Tableau Server — Set up:

Test site

1–2 fake users (last login set to past date)

Dummy workbooks/content never accessed

Stale extract tasks |
| Step 4 | ✅ Validate log output — Check structure, file naming, consistency; simulate “delete mode” by setting log_only: false (dry run) |
| Step 5 | ✅ Log routing — Either:

Ingest into Grafana via Promtail

Or manually review JSON logs and archive |
| Step 6 | 🔒 Compliance & policy review — Align thresholds and retention with FERPA, state record management, etc. |
| Step 7 | 🧪 Pilot automation — Run via cron or Task Scheduler for 2–4 weeks to validate no impact, then gradually enable real actions |