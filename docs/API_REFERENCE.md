# CyberShield AI — Complete API Reference

This document provides a concise, structured reference of all live REST endpoints available in the **CyberShield AI** platform (`/api/v1`).

---

## Authentication & Canonical Standards

- **Base URL (Local)**: `http://localhost:8000/api/v1`
- **Base URL (Production)**: `https://cybershield-ai-xnn7.onrender.com/api/v1`
- **User Authentication**: HTTP Bearer Header containing HS256 JWT:
  ```http
  Authorization: Bearer <access_token>
  ```
- **Agent Authentication**: HTTP Bearer Header containing SHA-256 token:
  ```http
  Authorization: Bearer <agent_credential_token>
  ```
- **Canonical Error Envelope**:
  All non-2xx responses adhere to the standard error structure:
  ```json
  {
    "error": {
      "code": "ERROR_CODE_STRING",
      "message": "Human-readable explanation of error.",
      "details": []
    }
  }
  ```
- **Pagination Convention**:
  All collection endpoints accept query parameters:
  - `limit`: Integer (default: 50, maximum: 200)
  - `offset`: Integer (default: 0)

---

## 1. System Health & Probes

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/health` | None | Public | Liveness probe; returns `{"status":"healthy"}` |
| `GET` | `/health/db` | None | Public | Neon PostgreSQL readiness probe; verifies connection pool |

---

## 2. Authentication & User Profile (`/auth`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `POST` | `/auth/login` | None | Public | Authenticates user credentials (rate-limited: 10/min per IP); returns JWT |
| `GET` | `/auth/me` | JWT | All Roles | Returns profile of currently authenticated user including role & org ID |

---

## 3. User Administration (`/users`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/users/` | JWT | Administrator | Lists all users within the administrator's organization |
| `POST` | `/users/` | JWT | Administrator | Creates a new user with specified role in the tenant organization |

---

## 4. Monitoring Agents (`/agents`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `POST` | `/agents/enrollment-token` | JWT | Administrator | Generates a one-time enrollment token for new agent registration |
| `POST` | `/agents/register` | None | Enrollment Token | Registers agent and returns permanent SHA-256 bearer credential |
| `POST` | `/agents/heartbeat` | Agent Cred | Authenticated Agent | Ingests telemetry heartbeat, updates agent status to `ONLINE` |
| `GET` | `/agents/` | JWT | Admin, Analyst | Lists all registered agents for organization with status and last heartbeat |
| `GET` | `/agents/tasks` | Agent Cred | Authenticated Agent | Agent polls for pending scan tasks assigned to its organization |
| `POST` | `/agents/tasks/{id}/status` | Agent Cred | Authenticated Agent | Updates dispatched task execution status (`RUNNING`, `COMPLETED`, `FAILED`) |
| `POST` | `/agents/results` | Agent Cred | Authenticated Agent | Ingests scan results with unique `upload_id` for idempotent processing |
| `POST` | `/agents/logs` | Agent Cred | Authenticated Agent | Forwards collected host authentication and security event logs |
| `GET` | `/agents/{id}` | JWT | Admin, Analyst | Returns specific agent details and recent 10 heartbeat snapshots |
| `POST` | `/agents/{id}/revoke` | JWT | Administrator | Immediately revokes agent credential and marks agent `OFFLINE` |
| `POST` | `/agents/{id}/rotate-credential` | JWT | Administrator | Rotates agent credential and returns new token |
| `GET` | `/agents/{id}/network-stats` | JWT | Admin, Analyst | Returns recent 10 network performance snapshots for agent |

---

## 5. Network Devices & Assets (`/devices`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/devices/` | JWT | All Roles | Lists discovered devices with IP, MAC, hostname, vendor, OS, reachability |
| `GET` | `/devices/{id}` | JWT | All Roles | Returns single device details |
| `GET` | `/devices/{id}/vulnerabilities` | JWT | All Roles | Returns all detected vulnerabilities for a specific device |
| `GET` | `/devices/{id}/risk` | JWT | All Roles | Returns latest multi-factor risk score (0-100) and factor breakdown |

---

## 6. Security Scans (`/scans`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/scans/` | JWT | Admin, Analyst | Lists security scan jobs with status, target, and completion times |
| `POST` | `/scans/` | JWT | Admin, Analyst | Dispatches a new discovery or vulnerability scan task to network agents |
| `GET` | `/scans/{id}` | JWT | Admin, Analyst | Returns detailed status and configuration of a specific scan |

---

## 7. Vulnerability Management (`/vulnerabilities`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/vulnerabilities/` | JWT | All Roles | Lists detected vulnerabilities with severity, CVE ID, affected host & service |
| `GET` | `/vulnerabilities/{id}` | JWT | All Roles | Returns details of specific vulnerability finding and remediation advice |

---

## 8. Centralized Security Logs (`/logs`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/logs/` | JWT | Admin, Analyst | Queries security logs; filters by event type, source, IP, date range |
| `GET` | `/logs/{id}` | JWT | Admin, Analyst | Returns details of an individual security log entry |

---

## 9. Security Alerts & Incidents (`/alerts`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/alerts/summary` | JWT | All Roles | Returns summary counts by status (open, resolved) and severity |
| `GET` | `/alerts/` | JWT | All Roles | Lists alerts; filters by status, severity, alert type, and date |
| `GET` | `/alerts/{id}` | JWT | All Roles | Returns alert detail including triggering events and affected device |
| `PATCH` | `/alerts/{id}` | JWT | Admin, Analyst | Advances alert lifecycle (`Acknowledged`, `Investigating`, `Resolved`) |
| `GET` | `/alerts/{id}/history` | JWT | All Roles | Returns chronological timeline of status transitions and analyst notes |

---

## 10. Multi-Factor Risk Scores (`/risk-scores`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/risk-scores/` | JWT | All Roles | Returns risk scores for all monitored devices sorted by score descending |

---

## 11. Threat Intelligence Indicators (`/threat-intelligence`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/threat-intelligence/` | JWT | All Roles | Lists known malicious indicators (IPs, domains, hashes) |
| `POST` | `/threat-intelligence/` | JWT | Admin, Analyst | Creates a new threat indicator; triggers automated alert on match |
| `GET` | `/threat-intelligence/{id}` | JWT | All Roles | Returns specific threat indicator entry |
| `DELETE` | `/threat-intelligence/{id}` | JWT | Administrator | Removes indicator from active threat intelligence database |

---

## 12. Local AI Security Assistant (`/ai`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `POST` | `/ai/explain-alert` | JWT | Admin, Analyst | Generates deterministic explanation and mitigation guidance for an alert |
| `POST` | `/ai/explain-vulnerability` | JWT | Admin, Analyst | Generates vulnerability risk assessment and patch recommendations |
| `POST` | `/ai/explain-risk` | JWT | Admin, Analyst | Analyzes multi-factor risk score breakdown for a specific device |
| `POST` | `/ai/chat` | JWT | Admin, Analyst | Multi-turn security investigation chat with Local Security Explanation Engine |

---

## 13. Executive & Compliance Reporting (`/reports`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/reports/` | JWT | All Roles | Lists generated reports with generation timestamps, author, and status |
| `POST` | `/reports/` | JWT | Admin, Analyst | Generates a new Security Overview, Vulnerability, or Incident report |
| `GET` | `/reports/{id}/download` | JWT | Admin, Analyst | Streams generated PDF or CSV file download |

---

## 14. Real-time Notifications (`/notifications`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/notifications/` | JWT | All Roles | Lists security notifications with read status filter and pagination |
| `GET` | `/notifications/unread-count` | JWT | All Roles | Returns count of unread notifications for active user session |
| `PATCH` | `/notifications/{id}/read` | JWT | All Roles | Marks an individual notification as read |
| `POST` | `/notifications/mark-all-read` | JWT | All Roles | Marks all unread notifications for the active user as read |

---

## 15. System Settings & Compliance Audit (`/settings` & `/audit-logs`)

| Method | Endpoint | Auth | Allowed Roles | Description |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/settings/` | JWT | Administrator | Lists all tenant system configuration key-value settings |
| `PUT` | `/settings/{key}` | JWT | Administrator | Updates or creates a system configuration setting |
| `PATCH` | `/settings/{key}` | JWT | Administrator | Partially updates a configuration setting value |
| `GET` | `/settings/audit-logs` | JWT | Administrator | Retrieves immutable compliance audit log entries |
| `GET` | `/audit-logs/` | JWT | Administrator | Alias route for audit log querying with action and date filters |
