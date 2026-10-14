# CyberShield AI — User Manual & Operations Guide

Welcome to the **CyberShield AI** User Manual. CyberShield AI is a unified cybersecurity monitoring, threat management, and incident response platform designed for security teams, network administrators, and compliance auditors.

---

## 1. Authentication & Role-Based Access Control (RBAC)

### 1.1 Logging In
1. Navigate to the CyberShield web dashboard.
2. Enter your corporate email and password.
3. Upon authentication, a secure JSON Web Token (JWT) is issued and stored in browser session storage.
4. Your account role automatically shapes the dashboard navigation, action buttons, and access permissions.

### 1.2 User Roles & Permissions

CyberShield AI enforces a strict three-tier RBAC model:

| Capability / Action | Administrator | Security Analyst | Viewer |
| :--- | :---: | :---: | :---: |
| View Dashboards, Metrics, & Graphs | ✅ | ✅ | ✅ |
| View Devices, Scans, & Vulnerabilities | ✅ | ✅ | ✅ |
| View Security Logs & Audit Records | ✅ | ✅ | ❌ |
| Run Network Discovery Scans | ✅ | ✅ | ❌ |
| Trigger Vulnerability Scans | ✅ | ✅ | ❌ |
| Update Alert Lifecycle (Acknowledge, Resolve) | ✅ | ✅ | ❌ |
| Use AI Security Explanation Engine & Chat | ✅ | ✅ | ❌ |
| Add / Delete Threat Intelligence Indicators | ✅ (Full) | ✅ (Add only) | ❌ |
| Generate & Download PDF / CSV Reports | ✅ | ✅ | ❌ |
| Enroll, Rotate, & Revoke Agents | ✅ | ❌ | ❌ |
| Manage Users & System Settings | ✅ | ❌ | ❌ |

---

## 2. Agent Management

CyberShield utilizes lightweight monitoring agents deployed inside private corporate or home network subnets to securely bridge local network telemetry to the cloud backend.

### 2.1 Enrolling a New Agent
1. Log in as an **Administrator**.
2. Click **Agents** in the left sidebar navigation.
3. Click the **Generate Token** button in the top right.
4. Specify the agent machine name (e.g., `hq-core-sensor`) and token expiry window (default: 60 minutes).
5. Copy the displayed one-time enrollment token.
6. On the target machine, configure `agent/.env` with `ENROLLMENT_TOKEN=<token>` and start the agent (`python main.py`).
7. Upon successful enrollment, the agent will appear in the **Agents** table with `ONLINE` status (indicated by a green badge).

### 2.2 Monitoring Agent Health
- The Agents table displays agent hostname, IP address, software version, CPU utilization, memory utilization, and the exact timestamp of the last received heartbeat.
- If an agent fails to send a heartbeat within 90 seconds (3 missed intervals), the system automatically transitions its status to `OFFLINE` (red badge).

### 2.3 Revoking an Agent
If a sensor machine is decommissioned or suspected of compromise:
1. Navigate to **Agents** and click on the target agent to open its detail view.
2. Click **Revoke Agent**.
3. Confirm the revocation dialog. The agent's credentials are immediately invalidated in the database, and future heartbeats will be rejected with HTTP 403.

---

## 3. Device Discovery

### 3.1 Initiating an Authorized Network Discovery Scan
> **WARNING**: Port scanning and network reconnaissance without explicit prior written authorization from the network owner is unlawful and unethical.

1. Navigate to **Devices** or **Network Monitoring** in the sidebar.
2. Click **Run Discovery Scan**.
3. A legal confirmation dialog will appear prompting you to verify that you are authorized to scan the target IP range/subnet.
4. Confirm authorization. The backend dispatches an asynchronous scan task to the local network agent.
5. The agent executes an authorized ping sweep (`nmap -sn`) or ARP table inspection and uploads discovered assets to the backend.

### 3.2 Reviewing Discovered Devices
- The **Devices** page lists all active hosts with IP address, MAC address, detected hostname, vendor, operating system, and reachability status.
- Clicking any device opens its asset card, showing its current multi-factor risk score, assigned risk band (`Low`, `Medium`, `High`, `Critical`), and identified vulnerabilities.

---

## 4. Vulnerability Management

### 4.1 Running a Vulnerability Scan
1. Navigate to **Vulnerability Management**.
2. Select a target device or subnet and initiate a service version scan.
3. The local agent performs deep banner grabbing and service detection (`nmap -sV`).
4. The backend automatically correlates detected service banners (e.g., `Apache 2.4.49`, `OpenSSH 8.2p1`) against the local Common Vulnerabilities and Exposures (CVE) database using deterministic version matching.

### 4.2 Triaging Vulnerabilities
- Identified vulnerabilities appear in the vulnerability matrix with CVSS score, severity badge, affected service, CVE description, and remediation recommendations.
- Click **Explain with AI** on any vulnerability item to generate an immediate, contextual explanation and step-by-step mitigation advice from the Local Security Explanation Engine.

---

## 5. Security Logs & Threat Detection

### 5.1 Viewing Logs
- Navigate to **Log Management** to view centralized authentication and system logs forwarded by agents.
- Filter logs in real time by event type (`login_failure`, `login_success`), log source, username, IP address, and date range.

### 5.2 Automated Threat Detection Rules
The CyberShield detection engine automatically evaluates incoming events against built-in security rules:
- **Rule 1 — Brute Force Attack**: Triggered when 5 or more failed login attempts (`login_failure`) originate from the same source IP within a 10-minute sliding window.
- **Rule 2 — Port Scan Reconnaissance**: Triggered when a device scan identifies 10 or more open ports on a single target within a scan execution.
- **Rule 3 — Suspicious Login**: Triggered when a successful login occurs from an IP address that generated 3 or more failed attempts in the preceding hour.
- **Rule 4 — Known Malicious IP**: Triggered when incoming traffic matches a registered Threat Intelligence Indicator.

---

## 6. Incident Alert Management

### 6.1 Alert Dashboard & Filtering
1. Navigate to **Alerts** to monitor real-time security alerts.
2. Filter alerts by status tabs: `All`, `Open`, `Acknowledged`, `Investigating`, `Resolved`, `False Positive`, or by severity (`Critical`, `High`, `Medium`, `Low`).

### 6.2 Managing the Alert Lifecycle
1. Click on an alert to view its complete incident detail panel, including triggering event details, affected device, source IP, and initial risk score.
2. Advance the status using the action buttons:
   - `Open` ➔ `Acknowledged` (Analyst acknowledges active triage)
   - `Acknowledged` ➔ `Investigating` (Incident response in progress)
   - `Investigating` ➔ `Resolved` (Threat mitigated and system patched)
   - Any stage ➔ `False Positive` (Verified benign activity)
3. Enter an optional reason note when changing status.
4. All status transitions are recorded with timestamps, user IDs, and transition notes in the **Alert History Timeline** and saved to the immutable compliance Audit Log.

---

## 7. AI Security Explanation Engine

CyberShield AI features a deterministic, offline-first **Local Security Explanation Engine** (`LocalRuleAI`) that requires zero external API keys, eliminates data exfiltration risks, and operates completely on-premise.

### 7.1 Contextual Alert & Vulnerability Explanation
- From any Alert or Vulnerability detail view, click **Explain with AI**.
- The engine synthesizes the raw security telemetry, CVE parameters, affected host details, and calculated risk factors into a structured human-readable assessment explaining:
  1. What happened.
  2. Potential business and operational impact.
  3. Immediate containment and long-term remediation steps.

### 7.2 Interactive Security Assistant Chat
- Navigate to **AI Assistant** in the sidebar.
- Security Analysts and Administrators can conduct multi-turn investigative chats.
- Ask questions regarding active alerts, CVE remediation advice, network risk scores, or incident triage procedures.

---

## 8. Compliance & Executive Reporting

### 8.1 Generating Reports
1. Navigate to **Reports**.
2. Click **Generate Report**.
3. Select report type:
   - **Security Overview Report**: High-level executive summary of security posture, fleet device counts, active agents, and alert statistics.
   - **Vulnerability Assessment Report**: Detailed breakdown of detected CVEs, affected software services, and remediation matrices.
   - **Incident & Alert Audit Report**: Chronological record of security alerts, trigger sources, resolution times, and responder actions.
4. Choose the target date range and click **Generate**.

### 8.2 Downloading Reports
- Generated reports appear in the archive table.
- Click **Download PDF** for an executive, print-ready PDF document featuring corporate headers, metadata tables, and incident summaries.
- Click **Download CSV** for raw data exports suitable for SIEM ingestion or spreadsheet analysis.

---

## 9. System Administration & Compliance Auditing

### 9.1 User Management (Administrator Only)
- Navigate to **Settings** ➔ **Users**.
- Create new user accounts, assign corporate emails, define passwords, and assign RBAC roles (`Administrator`, `Security Analyst`, `Viewer`).

### 9.2 Compliance Audit Trail (Administrator Only)
- Navigate to **Settings** ➔ **Audit Logs** or click **Audit Logs** in the sidebar.
- Inspect the immutable audit log recording all critical platform actions:
  - `user_login` / `user_login_failed`
  - `agent_enrolled` / `agent_revoked`
  - `scan_created`
  - `alert_status_changed`
  - `report_generated`
  - `setting_updated`
- Filter records by action, date range, or actor ID for compliance readiness (SOC 2, ISO 27001).
