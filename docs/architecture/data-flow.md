# CyberShield AI - Data Flow

**Version:** 2.0  
**Phase:** 2 of 27 - System Architecture Design  
**Scope:** Current local-first MVP

All flows below stay on the local laptop or authorized local network. The Frontend and Agent never connect to PostgreSQL directly.

## Agent -> Backend

```text
Agent module -> API Client -> FastAPI Agent route -> validation/RBAC -> domain service -> PostgreSQL
```

1. The Agent registers with an Administrator-issued, time-limited enrollment token.
2. The Backend returns a distinct Agent credential; the Agent stores it securely.
3. The Agent sends heartbeats with identity, timestamp, version, status, and CPU/RAM health.
4. It uploads authorized metrics, discovery results, vulnerability results, and log data.
5. It fetches pending scan tasks and reports accepted, running, completed, or failed status.
6. The Backend validates Agent ownership and organization scope, normalizes data, runs detection rules, and persists accepted records.

The Agent cannot call human-user endpoints, read other organizations' data, or connect to the database.

## Backend -> Database

```text
FastAPI route -> service/rule -> SQLAlchemy repository -> local PostgreSQL
```

The Backend is the sole database client. It stores users and roles, Agent state, devices, scans, vulnerabilities, normalized logs, threat indicators, alerts and status timelines, reports, and audit logs. Transactions preserve related scan, alert, and audit updates.

## Frontend -> Backend

```text
React route/component -> typed REST client -> FastAPI user route -> JWT + RBAC -> response JSON
```

The Frontend sends user JWTs for authenticated requests. The Backend enforces Administrator, Security Analyst, and Viewer permissions regardless of UI visibility. Query/cache state is refetched after mutations; no frontend request bypasses the Backend.

## Scan Workflow

```text
Administrator/Analyst
  -> Frontend authorization notice + scan request
  -> Backend validates JWT, role, target authorization, and online Agent
  -> Backend creates scan task
  -> Agent fetches task
  -> Agent runs Nmap discovery or port/service scan
  -> Agent reports task status and results
  -> Backend normalizes and matches local/cached CVE data
  -> Backend stores devices/findings, calculates risk, audits completion
  -> Frontend refetches scan, device, vulnerability, and dashboard data
```

The system performs discovery and service/version matching only; it does not exploit vulnerabilities. A Viewer receives 403 for scan actions.

## Alert Workflow

```text
normalized logs / scan results
  -> Backend detection rules
  -> alert + transparent risk score
  -> PostgreSQL alert timeline and audit log
  -> Frontend alert view and in-dashboard notification
  -> Analyst/Administrator status transition
```

MVP rules cover brute force, port scan, suspicious login, and malware-indicator matches. Alert status follows Open -> Acknowledged -> Investigating -> Resolved, or False Positive. Each transition records actor and timestamp.

## AI Explanation Workflow

```text
Frontend selected alert/vulnerability/risk
  -> Backend AI endpoint + JWT/RBAC
  -> AIService interface
  -> LocalRuleAI deterministic templates
  -> Backend returns labeled explanation
  -> Frontend displays Local Security Explanation Engine output
```

`LocalRuleAI` uses the selected record and documented risk factors without external calls. Future providers may implement the same interface, but no future provider is used in the MVP.
