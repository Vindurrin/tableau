🧑‍💼 1) External Interviewers – What they care about
Area	What You Say
Initiative	“I identified that our Tableau Server was accumulating inactive content and users, risking performance and non-compliance…”
Technical Depth	“…so I built a Python-based governance framework using the REST API and personal access tokens, with JSON-logged output for downstream tools like Grafana and Slack.”
Automation	“It’s scheduled to run without downtime, modular across users/content/sites, and supports full delete mode if enabled — like a DevOps governance daemon.”
Value Delivered	“We’re projecting a 30–50% reduction in content bloat and a 40% admin time savings.”

👥 2) Direct Management – What they care about
Priority	What You Say
Cost Avoidance	“We're extending the useful life of our current Tableau infrastructure by purging stale data and users automatically — delaying the need for additional cores or cloud cost.”
Compliance Alignment	“The cleanup thresholds align with FERPA and NIST 800-171 standards, which improves our audit defensibility.”
Operational Visibility	“All cleanup results are centrally logged and can integrate with our existing Grafana stack for visibility and alerting.”
Zero-Risk Testing	“It’s log-only by default, and we’re testing in a sandbox site — it’s safe and measurable.”

🧾 Polished Resume Bullet (1–2 Lines, Action + Impact)
Architected a self-healing Tableau governance automation pipeline using Python, REST APIs, and infrastructure-as-code principles; enforced policy-as-code cleanup of stale users, content, and extracts, triggering Slack/email reports and achieving a projected X% performance gain and Y% storage recovery. Integrated with proprietary IDM to manage 300+ user groups through a containerized admin framework, reducing provisioning time and administrative overhead.

🧾 Expanded Version (Interview, Performance Review, Portfolio)
Leveraging my role as Tableau Server administrator, I designed and implemented a governance automation pipeline to enforce data hygiene, performance, and compliance in line with FERPA/NIST policy. Using Python scripting, REST API automation, and Windows task scheduling, I developed cleanup scripts that log and optionally purge:

Inactive users (365+ days)

Stale content (730+ days)

Orphaned extract schedules

These processes generate JSON logs, sent to Slack/email for alerting, and optionally ingestible by Grafana for dashboarding.

Key outcomes (replace placeholders as metrics come in):

Reclaimed X GB (Y%) of disk space on initial run

Rescheduled Z% of extracts to off-peak hours (pre-7am), reducing peak CPU/memory load

Removed X idle users, improving license efficiency and audit posture

This framework is deployed in perpetual scheduled runs, allowing Tableau Server to self-clean based on policy without downtime.

Additionally, I worked with internal IAM teams to integrate a containerized user group management system that supports 300+ provisioned groups without requiring ownership or group membership, significantly improving user onboarding and administrative delegation agility across data platforms.