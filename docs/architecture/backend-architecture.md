# CyberShield AI - Backend Architecture

**Version:** 2.0  
**Phase:** 2 of 27 - System Architecture Design  
**Scope:** Current local-first MVP

## Runtime Shape

The Backend is one FastAPI application running locally. It exposes a versioned REST API, applies authentication and default-deny RBAC, coordinates Agent work, applies domain rules, invokes `AIService`, and persists through SQLAlchemy/Alembic to one local PostgreSQL instance.

```text
HTTP/HTTPS REST
  |-- user JWT requests --------------------+
  |-- Agent credential requests ------------+--> FastAPI routes
                                             |--> auth and RBAC
                                             |--> domain services
                                             |--> SQLAlchemy repositories --> PostgreSQL
                                             |--> AIService --> LocalRuleAI
```

## Module Layout

```text
backend/
  app/
    main.py
    api/              # REST route registration and dependencies
    core/             # configuration, security, error handling
    db/               # SQLAlchemy session, models, Alembic integration
    schemas/          # Pydantic request and response contracts
    modules/
      authentication/
      users/
      agents/
      devices/
      scans/
      vulnerabilities/
      logs/
      alerts/
      threat_intelligence/
      reports/
      ai/
    services/         # shared orchestration and domain rules
```

### Authentication

Validates credentials, hashes passwords with bcrypt, issues and validates JWTs, throttles repeated failures, and separates user authentication from Agent credentials.

### Users

Implements Administrator-only user creation, update, deactivation, and role assignment for Administrator, Security Analyst, and Viewer.

### Agents

Handles enrollment-token generation, Agent registration, credential validation/revocation/rotation, heartbeats, online/offline state, and restricted Agent endpoints.

### Devices

Stores authorized discovered devices and their last-seen status, ownership, network identity, open ports, and services.

### Scans

Allows Administrators and Security Analysts to start authorized discovery and vulnerability scans. It creates task records, sends work to an online Agent, records status, and enforces the no-exploitation constraint.

### Vulnerabilities

Matches service/version observations against local or cached CVE data, records severity and recommendations, and supports device and report views.

### Logs

Validates and normalizes Agent log data into timestamp, Agent/device, source, event type, severity, message, source IP, and username fields.

### Alerts

Creates Brute Force, Port Scan, Suspicious Login, and Malware Indicator alerts; calculates transparent 0-100 risk scores; and records Open -> Acknowledged -> Investigating -> Resolved or False Positive transitions with an audit timeline.

### Threat Intelligence

Maintains local IP, domain, and hash indicators and supports Administrator/Analyst lookup and alert references.

### Reports

Builds PDF and/or CSV summaries of Agents, devices, vulnerabilities, alerts, and risk distribution for a selected period.

### AI

Exposes the `AIService` contract to the rest of the Backend and owns provider selection. It is the only place where explanation providers are constructed.

## AIService Abstraction

Calling modules depend on the interface, not a concrete provider:

```python
from abc import ABC, abstractmethod

class AIService(ABC):
    @abstractmethod
    async def explain_alert(self, alert: Alert) -> str:
        raise NotImplementedError

    @abstractmethod
    async def explain_vulnerability(self, vulnerability: Vulnerability) -> str:
        raise NotImplementedError

    @abstractmethod
    async def explain_risk_score(self, risk_score: int, factors: dict) -> str:
        raise NotImplementedError
```

The MVP dependency graph is `AIService -> LocalRuleAI`. `LocalRuleAI` uses deterministic templates and underlying alert, vulnerability, and risk data; it makes no external calls. `OllamaAI` and `OpenAIProvider` are explicitly future, optional implementations of `AIService`, not current dependencies. The UI labels the capability **Local Security Explanation Engine**.

## Authorization Rules

Every route defaults to deny. Administrator, Security Analyst, and Viewer permissions follow `docs/srs/user-roles.md`. Agent routes accept only Agent credentials and Agent-scoped operations: register, authenticate, heartbeat, authorized data upload, scan-task retrieval, and task-status reporting. Agent routes cannot reach user/role management, settings, or direct database access.
