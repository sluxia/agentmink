
# Project Plan (interactive)

## Question 1 — Primary problem

Answer (from user): companies need a system that allows them to connect their local files, MCPs and other tools to AI. We also need to be able to set PII globally so that whatever data coming from those tools gets filtered of PII before it reaches the AI.

Ruminations / implications:
- Data connectors: we'll need adapters for local files, MCPs, and third-party tools (sync, streaming, or on-demand).
- Global PII policy: a centralized, configurable PII filter/enforcer that runs before any data reaches AI models.
- Trust boundary: connectors must run in a way that minimizes exfiltration risk (local agents or secure proxies).
- Latency vs privacy: real-time use-cases require low-latency filtering; batch workflows can tolerate stronger heuristics.
- Access control & audit: per-connector permissions and audit logs for filtered content and policy decisions.

Assumptions to confirm:
- "MCPs" refers to Model/Marketplace/Compute Providers or Model Control Planes—please clarify which you mean.
- PII definitions: we need a canonical list (names, emails, SSNs, keys), plus support for custom patterns.
- Connectors may run on-premises (local agent) or in the cloud; clarify constraints.

Proposed acceptance criteria for Q1:
- The system can register at least one local-files connector and one external tool connector.
- A global PII policy can be defined and applied to data flows before model requests.
- The system logs PII-detection events and blocks/sanitizes data according to policy.


Next question (Q2): Who are the primary users (personas) and how will they use the system? (Answer briefly; I'll ruminate and design Q3 from that.)


## Question 2 — Primary users / personas

Answer (from user): companies with multiple users, and at least one person who can set up the system on a server. They spin it up and every other device connects via a central MCP endpoint on port 8000/mcp and there is a dashboard for visibility and performance.

Ruminations / implications:
- Deployment model: server-hosted central MCP service (single server or cluster) that exposes `/mcp` on port `8000` for device agents to connect.
- Roles: installer/admin user who configures the server, and multiple end-users/devices that connect to the MCP.
- Device agents: lightweight clients that run on user devices or in-network and maintain a connection (push or persistent socket) to the MCP.
- Dashboard: must surface connected devices, health/heartbeat, throughput, latency, PII-filtering events, and basic performance metrics.
- Security: TLS, authentication (API keys, certificates, or SSO), firewall considerations for exposing port `8000`, and secure onboarding flows for devices.
- Multi-user controls: RBAC for admin vs viewers, per-connector permissions, and audit logs for policy changes and PII events.
- Scalability & resilience: plan for connection limits, horizontal scaling (if needed), and metrics/observability for scaling decisions.

Assumptions to confirm:
- Devices will be able to reach the central server (NAT/traversal concerns) or will use an outbound-only connection from agents to MCP.
- Single-tenant vs multi-tenant deployment: is one server per company or one server serving many companies?
- Dashboard requirements: read-only visibility vs configuration from the UI.

Proposed acceptance criteria for Q2:
- A server can be deployed and listens on port `8000` with an `/mcp` endpoint.
- A device agent can connect and appear in the dashboard's connected-devices list.
- An admin user can view PII-filtering events and basic performance metrics in the dashboard.

Next question (Q3): What are the must-have features for the MVP (3–6 items)?


## Question 3 — Must-have features for MVP

Answer (from user): file input, PII functionality, retrieval

Ruminations / implications:
- File input: connectors for local files (filesystem watchers, upload endpoints, or mounted volumes) and parsers for common types (txt, PDF, DOCX, CSV).
- PII functionality: global PII policy engine that detects and either masks, redacts, or blocks sensitive tokens before data is sent to models. Support patterns, ML-based detectors, and custom rules.
- Retrieval: ability to index ingested files and perform retrieval (search/embedding-based) to provide context to models while ensuring PII is filtered on retrieval.
- Data pipeline: ingestion -> PII-filter -> index/store -> retrieval -> model request (with sanitized context).
- Testing: include synthetic PII test cases and audit logs to validate filtering correctness.

Assumptions to confirm:
- Which file types are highest priority for MVP? (e.g., PDFs and text files)
- Retrieval expects vector embeddings; confirm whether we should include an embedding store (e.g., FAISS) in MVP.
- PII actions: prefer mask vs redact vs block—decide default behavior.

Proposed acceptance criteria for Q3:
- The system accepts files from a local-file connector and successfully ingests them.
- A PII policy can be applied that detects and redacts at least three common PII types (names, emails, phone numbers) during ingestion and retrieval.
- Ingested data is indexed and a retrieval query returns relevant documents with PII handled according to policy.

Next question (Q4): What are nice-to-have features that can wait after MVP? (Answer briefly; I'll ruminate and design Q5 from that.)


## Question 4 — Nice-to-have features

Answer (from user): transparency of all agent performance, memory, retention and metrics

Ruminations / implications:
- Dashboard extensions: detailed agent performance views (throughput, latency, error rates), memory usage per agent, and retention summaries.
- Memory & retention controls: UI and API to configure retention policies (time-based, size-based), purge or archive data, and view stored memory contents (with PII redaction applied where required).
- Metrics pipeline: collect, store, and visualize metrics (Prometheus + Grafana or hosted alternatives) and keep traces for debugging and audit.
- Explainability: surface why PII was detected/filtered and provide example redactions for admin review.
- Export & compliance: allow exporting logs and retention reports for compliance and audits.

Assumptions to confirm:
- Retention policies need to be configurable per-company, per-connector, or per-agent.
- Metrics retention and visibility must avoid exposing raw PII; metrics should be aggregated or sanitized.

Proposed acceptance criteria for Q4:
- Dashboard shows agent-level performance metrics and memory usage.
- Admins can configure retention policies and trigger purges/exports via UI or API.
- PII-redacted memory views are available for audit without exposing raw sensitive data.

Next question (Q5): Are there existing products or competitors we should model or avoid? (Answer briefly; I'll ruminate and design Q6 from that.)


## Question 5 — Competitors / existing products

Answer (from user): many

Ruminations / implications:
- There are many existing vendors and open-source projects in adjacent spaces (enterprise model governance, RAG platforms, data connectors, PII redaction tools).
- We should perform a targeted competitor analysis to identify direct feature overlaps (global PII policies, on-prem connectors, MCP endpoints, device agents, dashboards) and clear differentiation areas.
- Likely competitor categories to review: enterprise AI governance (policy/enforcement), retrieval/RAG platforms, secure data connectors, PII/redaction services, and agent orchestration platforms.

Next actions for competitor research:
- Compile a short list of 8–12 representative products across the categories above.
- For each, capture what they do well, gaps versus our vision, pricing / deployment model, and any IP/legal constraints to avoid.

Proposed acceptance criteria for Q5:
- A one-page competitor summary with 8–12 products and 3–5 bullets each describing strengths/gaps.

Next question (Q6): Target platforms: web, mobile, desktop, CLI, API-only? (Answer briefly; I'll ruminate and design Q7 from that.)


## Question 6 — Target platforms

Answer (from user): webapp

Ruminations / implications:
- Build a web-first product: single-page dashboard (React/Vue/Svelte) plus REST/GraphQL API for device agents.
- Dashboard responsibilities: onboarding, connector management, PII policy UI, metrics, and device list.
- Server responsibilities: host MCP `/mcp` endpoint on port `8000`, provide API endpoints for ingestion, retrieval, policy management, and metrics.
- Consider progressive enhancement: API-first design so CLI or lightweight clients can be added later.

Assumptions to confirm:
- Web hosting environment and whether the dashboard should support self-hosted installs behind corporate firewalls.

Proposed acceptance criteria for Q6:
- A basic web dashboard is runnable locally and can list connected agents.
- REST API endpoints are documented and reachable for agents to register and send data.

Next question (Q7): Any constraints: timeline, budget, hosting, compliance, data privacy?


## Implementation next steps (agreed)

- Next immediate task: File upload -> Brain
	- Goal: accept uploaded files, run PII sanitation, index content, and persist to the "brain" (memory/index) for retrieval.
	- Minimal acceptance criteria:
		- `POST /ingest/file` persists sanitized content to a storage backend and returns an id.
		- Ingested documents are indexed and retrievable via a simple query API.
		- PII redaction occurs before persistence and an event is logged.
	- Proposed components to add now:
		- Embedding generation step (configurable provider)
		- Vector index (local FAISS or hosted vector DB)
		- Document store metadata (SQLite/Postgres)

- Next after that: Tools connectors
	- Goal: implement connectors to integrate MCP, filesystems, and third-party APIs.
	- Minimal acceptance criteria:
		- Connector registration flow in the dashboard/API.
		- A working filesystem connector that watches a configured folder and ingests new files to the brain.
		- A pluggable connector interface so additional connectors can be added later.

Next immediate question for design (single): do you prefer a local vector store (FAISS) or a hosted/vector DB service (Pinecone, Weaviate, etc.) for the brain? Answer briefly and I'll design the ingestion flow accordingly.






