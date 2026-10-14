# CyberShield AI — Final Demonstration Script & Viva Defense Guide

This guide is designed for presenting and demonstrating CyberShield AI during project evaluations, customer presentations, and academic viva defenses.

---

## 1. Pre-Demo Verification Checklist

Complete these checks prior to beginning the presentation:
- [x] **Live Backend API**: Verify `GET https://cybershield-ai-xnn7.onrender.com/api/v1/health` returns `{"status":"healthy"}`.
- [x] **Live Neon PostgreSQL**: Verify `GET https://cybershield-ai-xnn7.onrender.com/api/v1/health/db` returns `{"status":"healthy","database":"connected"}`.
- [x] **Frontend Web Application**: Open the live dashboard in your browser.
- [x] **Local Monitoring Agent**: Start the agent on your machine (`python main.py`) and confirm its status is `ONLINE` in the dashboard.
- [x] **Automated Test Suite**: 322 automated tests passing with 0 failures (`pytest tests/ -v`).
- [x] **Clean Working Tree**: Git repository tagged at `v1.0.0`.

---

## 2. Step-by-Step 10-Minute Live Demonstration Script

| Time | Stage | Action to Perform in UI | Key Talking Points |
| :--- | :--- | :--- | :--- |
| **0:00 - 1:00** | **Introduction & Login** | Navigate to login page. Enter credentials: `admin@cybershield.ai`. Click **Sign In**. | *"CyberShield AI is a unified cybersecurity monitoring and threat management platform. The login page is protected by SlowAPI rate limiting (10 req/min per IP) to prevent brute-force attacks and enforces role-based access control."* |
| **1:00 - 2:30** | **Executive Dashboard** | Show Dashboard KPIs, agent telemetry counters, recent incident table, and severity chart. | *"The dashboard provides immediate situational awareness. Notice the active agent telemetry reporting CPU and memory utilization, auto-refreshing every 60 seconds, and the live incident severity distribution."* |
| **2:30 - 3:30** | **Monitoring Agents** | Navigate to **Agents**. Point to the registered sensor machine showing `ONLINE`. Click **Generate Token**. | *"Our standalone agent runs inside customer subnets. Because cloud backends cannot reach private IPs directly, our agent bridges this gap using secure, outbound-only HTTPS and SHA-256 hashed bearer credentials."* |
| **3:30 - 4:30** | **Network Assets & Discovery** | Navigate to **Devices**. Show discovered hosts (IP, MAC, vendor, OS). Click **Run Discovery Scan** (show legal warning dialog). | *"Network discovery uses authorized Nmap ping sweeps and ARP cache correlation. CyberShield enforces legal authorization confirmations before any scanning task is dispatched."* |
| **4:30 - 5:30** | **Vulnerability Management** | Navigate to **Vulnerability Mgmt**. Show detected CVEs, CVSS scores, affected software versions. | *"The agent performs deep service banner grabbing (`nmap -sV`). The backend deterministically matches software versions against our local CVE database without relying on external cloud scanners."* |
| **5:30 - 7:00** | **Incident Alert Lifecycle & Triage** | Navigate to **Alerts**. Click the Brute Force alert. Change status from `Open` ➔ `Acknowledged` ➔ `Investigating`. Show timeline. | *"Our detection engine flagged 5 failed logins within 10 minutes from the same IP. Here, the security analyst can acknowledge the incident, assign investigation notes, and review the immutable audit timeline below."* |
| **7:00 - 8:00** | **Local AI Security Assistant** | Click **Explain with AI** on the alert or navigate to **AI Assistant**. Show root cause analysis and MITRE mapping. | *"Our explanation engine is LocalRuleAI — completely on-premise and deterministic. Unlike public LLMs, no sensitive corporate data, IPs, or vulnerabilities are ever sent to third parties. It works offline, costs zero in API fees, and is fully explainable."* |
| **8:00 - 9:00** | **Compliance & Reporting** | Navigate to **Reports**. Click **Generate Report**. Download the generated PDF and open it. | *"Security leaders need compliance-ready reports. Using fpdf2, CyberShield generates print-ready executive summaries with branded headers, KPI tables, and CSV exports for SIEM integration."* |
| **9:00 - 10:00** | **Threat Intelligence & Audit Trail** | Navigate to **Threat Intelligence** and **Settings ➔ Audit Logs**. | *"Threat indicators match suspicious IPs against known IOCs automatically. Every administrative action is permanently recorded in the compliance audit trail for SOC 2 and ISO 27001 readiness."* |

---

## 3. Viva Defense & Technical Q&A Preparation

### Q1: Why did you choose FastAPI over Django or Flask?
> **Answer**: FastAPI was chosen because it provides native asynchronous execution (`asyncio`), high-performance request handling comparable to NodeJS/Go, Pydantic v2 data validation with automatic type enforcement, and auto-generated OpenAPI (Swagger) documentation. Django introduces unnecessary ORM overhead and session baggage for an API-first microservice architecture, while Flask lacks built-in asynchronous request pipelines and type validation.

### Q2: Is this "real" AI? What is the "Local Security Explanation Engine"?
> **Answer**: `LocalRuleAI` is an on-premise, rule-based expert system designed specifically for cybersecurity root cause analysis. It synthesizes real telemetry from the database (CVSS scores, MITRE ATT&CK tactics, failed login counts, port exposure) into structured, actionable explanations. This is a deliberate security architectural decision:
> 1. **Zero Data Exfiltration**: Private IP addresses, hostnames, and vulnerability data are never sent to third-party LLMs (OpenAI, Anthropic, Google).
> 2. **Deterministic & Auditable**: Rule-based outputs eliminate hallucinations and guarantee consistent advice for compliance auditors.
> 3. **Offline Resilience & Zero Cost**: Operates entirely in air-gapped environments without recurring API costs.

### Q3: Why use a standalone monitoring agent instead of scanning directly from the backend?
> **Answer**: Production backends deployed on cloud providers (like Render or AWS) cannot reach private RFC 1918 IP addresses (e.g., `192.168.1.0/24` or `10.0.0.0/8`) inside a customer's local enterprise or home network due to NAT and firewalls. The CyberShield Agent runs inside the local network and uses secure, outbound-only HTTPS requests to poll for scanning tasks and upload telemetry, eliminating the need to expose inbound ports on the customer network.

### Q4: How is the platform secured against attacks?
> **Answer**: Security is built in depth across all layers:
> - **Authentication**: Users authenticate via bcrypt password hashing (work factor 12) and receive signed HS256 JWT tokens. Agents authenticate via 384-bit random tokens stored as SHA-256 hashes.
> - **Rate Limiting**: SlowAPI restricts `POST /auth/login` to 10 requests per minute per IP to mitigate brute-force attacks.
> - **Security Headers**: Middleware enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict referrer policies.
> - **Tenant Boundary**: Every query is scoped by `organization_id`, strictly isolating organizational data.
> - **Credential Safety**: Secrets and tokens are never logged at any log level.

### Q5: How does the system handle database connection scaling with Neon Serverless?
> **Answer**: Neon Serverless PostgreSQL scales compute to zero and utilizes PgBouncer connection pooling. We implemented a dual-URL architecture:
> 1. Runtime operations connect via the pooled PgBouncer URL with `prepare_threshold=None` and TCP keepalives to prevent connection dropouts.
> 2. Alembic schema migrations connect via `DATABASE_URL_DIRECT` directly to the compute instance to execute DDL statements cleanly.

### Q6: What enhancements would you implement given more development time?
> **Answer**:
> 1. **Real-time WebSockets**: Push instant desktop alert notifications rather than 30s polling intervals.
> 2. **Machine Learning Anomaly Detection**: Incorporate unsupervised isolation forests to identify baseline behavioral anomalies in user traffic.
> 3. **Extended Log Collectors**: Add native syslog (RFC 5424) listeners and Zeek/Suricata IDS log ingestion.
> 4. **Automated Remediation Actions**: Implement optional active firewall rule injection (iptables/Windows Firewall) directly from the dashboard.
