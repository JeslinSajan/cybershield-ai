# CyberShield AI — Functional Requirements

Version 1.0 | Companion to SRS.md

Each requirement is numbered and written to be testable. Requirements
marked **(MVP)** are required for the graded minimum pipeline. Others
are still Phase 1–22 scope but lower priority if time runs short.

---

## 1. Authentication

- **FR-1.1 (MVP):** The system shall allow a user to log in with
  email/username and password.
- **FR-1.2 (MVP):** The system shall hash passwords using bcrypt; no
  password shall be stored or logged in plaintext.
- **FR-1.3 (MVP):** The system shall issue a JWT on successful login
  and reject requests with missing, invalid, or expired tokens.
- **FR-1.4:** The system shall support logout by invalidating the
  client-side token (and, if implemented, a server-side denylist).
- **FR-1.5:** The system shall lock or throttle an account after 5
  consecutive failed login attempts within 10 minutes.

## 2. User Management

- **FR-2.1 (MVP):** An Administrator shall be able to create, view,
  update, and deactivate user accounts.
- **FR-2.2 (MVP):** An Administrator shall be able to assign one of
  three roles (Administrator, Security Analyst, Viewer) to a user.
- **FR-2.3:** The system shall prevent a user from deleting or
  demoting their own Administrator account if they are the sole
  remaining Administrator.

## 3. RBAC / Authorization

- **FR-3.1 (MVP):** The system shall enforce role-based access control
  on every API endpoint; the default for any unmatched rule shall be
  **deny**.
- **FR-3.2 (MVP):** A Viewer shall receive HTTP 403 when attempting
  any write operation (scan, alert status change, user management).
- **FR-3.3 (MVP):** A Security Analyst shall receive HTTP 403 when
  attempting user management or system settings changes.

## 4. Agent Management

- **FR-4.1 (MVP):** An Administrator shall be able to generate a
  time-limited enrollment token for a new Agent.
- **FR-4.2 (MVP):** An Agent shall register itself using a valid
  enrollment token and receive a unique Agent credential.
- **FR-4.3 (MVP):** An Agent shall send a heartbeat at a configurable
  interval containing agent ID, timestamp, status, version, and basic
  system health (CPU/RAM).
- **FR-4.4 (MVP):** The system shall mark an Agent as OFFLINE if no
  heartbeat is received within a configurable timeout.
- **FR-4.5:** An Administrator shall be able to revoke an Agent's
  credential, immediately preventing further authenticated requests
  from that Agent.
- **FR-4.6:** The system shall support Agent credential rotation
  without requiring full re-enrollment.

## 5. Device Discovery

- **FR-5.1 (MVP):** An authorized user (Administrator or Analyst)
  shall be able to trigger a network discovery scan via an online
  Agent.
- **FR-5.2 (MVP):** The Agent shall use Nmap to discover devices on
  the authorized local network and report IP, MAC (where available),
  hostname, vendor (where available), open ports, and services.
- **FR-5.3 (MVP):** The system shall store discovered devices and
  display them in a Device List view with status (online/offline/
  unknown) and last-seen timestamp.
- **FR-5.4:** The UI shall display a visible authorization notice
  before any scan or discovery action: "Only scan networks and
  systems you own or are explicitly authorized to assess."

## 6. Vulnerability Scanning

- **FR-6.1 (MVP):** The system shall perform port scanning and
  service/version detection on discovered devices via the Agent.
- **FR-6.2 (MVP):** The system shall match detected service/version
  combinations against a local or cached CVE dataset to identify
  known vulnerabilities.
- **FR-6.3 (MVP):** Each identified vulnerability shall be assigned a
  severity (Low/Medium/High/Critical) and a recommendation.
- **FR-6.4:** If no external CVE service is reachable, the system
  shall continue functioning using local/seeded CVE data, clearly
  labeled as development/demo data in the UI.
- **FR-6.5:** The system shall explicitly not perform exploitation of
  any identified vulnerability.

## 7. Network Monitoring

- **FR-7.1:** The Agent shall report network interface statistics
  (bytes sent/received) at a configurable interval.
- **FR-7.2:** The Agent shall report basic system health metrics
  (CPU, RAM, disk usage).
- **FR-7.3:** The dashboard shall display recent network/system
  utilization for online Agents.

## 8. Log Management

- **FR-8.1 (MVP):** The Agent shall collect authorized SSH
  authentication logs and Linux syslog entries.
- **FR-8.2 (MVP):** The backend shall normalize incoming logs into a
  common schema (timestamp, agent_id, device_id, source, event_type,
  severity, message, source_ip, username).
- **FR-8.3:** The system shall provide a Log Explorer view with
  filtering by time range, severity, source, and free-text search.

## 9. Threat Detection

- **FR-9.1 (MVP):** The system shall generate a Brute Force alert when
  a configurable threshold of failed logins from one source occurs
  within a configurable time window.
- **FR-9.2 (MVP):** The system shall generate a Port Scan alert when
  one source contacts a configurable number of distinct ports on a
  device within a short time window.
- **FR-9.3:** The system shall generate a Suspicious Login alert for
  abnormal authentication patterns (e.g. login outside normal hours,
  from a new source).
- **FR-9.4:** The system shall generate a Malware Indicator alert when
  observed data matches a stored threat indicator (IP/domain/hash).

## 10. Threat Intelligence

- **FR-10.1:** The system shall maintain a local table of threat
  indicators (IP, domain, hash) usable for indicator matching.
- **FR-10.2:** An Administrator or Analyst shall be able to search
  indicators and view details, including which alerts referenced them.

## 11. Risk Scoring

- **FR-11.1 (MVP):** The system shall calculate a risk score (0–100)
  per device/alert using a documented, transparent rule-based formula
  combining vulnerability severity, open ports, failed logins,
  suspicious activity, and threat-intelligence matches.
- **FR-11.2 (MVP):** The system shall classify risk scores into bands:
  0–24 Low, 25–49 Medium, 50–74 High, 75–100 Critical.
- **FR-11.3:** The risk-scoring formula and its weighting shall be
  documented in `docs/database/` or `docs/architecture/` — no
  undocumented/black-box scoring is permitted.

## 12. Alerts

- **FR-12.1 (MVP):** The system shall create an alert record
  containing ID, timestamp, agent, device, type, severity, risk score,
  description, and status.
- **FR-12.2 (MVP):** An Analyst or Administrator shall be able to
  transition an alert through statuses: Open → Acknowledged →
  Investigating → Resolved, or mark it False Positive.
- **FR-12.3:** The system shall maintain a timeline of status changes
  per alert (who changed it, when, from what to what).

## 13. AI Assistant (Local Security Explanation Engine)

- **FR-13.1 (MVP):** The system shall provide a chat-style interface
  where a user can request an explanation of a selected alert,
  vulnerability, or risk score.
- **FR-13.2 (MVP):** Explanations shall be generated by `LocalRuleAI`
  using deterministic templates driven by the underlying data (not an
  external API call).
- **FR-13.3 (MVP):** The UI shall clearly label this feature "Local
  Security Explanation Engine," not "AI" alone, to avoid implying LLM
  capability it does not have.
- **FR-13.4:** The `AIService` interface shall be provider-agnostic so
  a future `OllamaAI` or `OpenAIProvider` implementation can replace
  `LocalRuleAI` without changing calling code.

## 14. Reports

- **FR-14.1 (MVP):** The system shall generate a report (PDF and/or
  CSV) summarizing agents, devices, vulnerabilities, alerts, and risk
  distribution for a selected time period.
- **FR-14.2:** Reports shall be downloadable from the Reports view.

## 15. Notifications

- **FR-15.1:** The system shall display in-dashboard notifications for
  new critical/high alerts.
- **FR-15.2:** The notification architecture shall be designed so
  email/Telegram/Slack channels can be added later without redesign
  (not required to be implemented in the MVP).

## 16. Audit Logging

- **FR-16.1 (MVP):** The system shall record an audit log entry for:
  login, failed login, user creation/deletion, role changes, agent
  registration/revocation, scan started/completed, alert status
  changes, report generation, and settings changes.
- **FR-16.2:** Audit logs shall be viewable by Administrators only.

## 17. Dashboard

- **FR-17.1 (MVP):** The dashboard shall display summary cards: Online
  Agents, Online Devices, Critical Vulnerabilities, Open Alerts,
  Average Risk Score.
- **FR-17.2:** The dashboard shall display charts for alert trend,
  vulnerability severity distribution, and risk trend over time.
- **FR-17.3:** The dashboard shall display a recent activity feed
  (device discovered, vulnerability found, alert generated, agent
  heartbeat, scan completed).
