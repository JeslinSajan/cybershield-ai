# CyberShield AI - High-Level Architecture

**Version:** 2.0  
**Phase:** 2 of 27 - System Architecture Design  
**Scope:** Current local-first MVP

## Purpose and Scope

CyberShield AI is a standalone, single-organization application for authorized environments such as college labs, schools, startups, and home labs. During MVP development, the React frontend, FastAPI backend, PostgreSQL database, and CyberShield Agent run on one laptop or on the same local network. The Backend is the only service boundary for application behavior and persistence.

The MVP has one local PostgreSQL instance, one FastAPI process, one React development server, and an Agent process on each authorized host used for demonstration. It does not require a reverse proxy, orchestration layer, or external AI service.

## Four-Component MVP

```text
+----------------------+       HTTP/HTTPS REST        +----------------------+
| React Frontend       | <--------------------------> | FastAPI Backend      |
| localhost:5173       |       JSON + user JWT        | localhost:8000       |
+----------------------+                              +----------+-----------+
                                                                    |
                                                    SQLAlchemy       | PostgreSQL
                                                                    v
                                                         +----------------------+
                                                         | PostgreSQL           |
                                                         | localhost:5432       |
                                                         +----------------------+
                                                                    ^
                                                                    | SQL only via Backend
                                                                    |
+----------------------+       HTTP/HTTPS REST        +-------------+--------+
| CyberShield Agent    | <--------------------------> | FastAPI Backend      |
| authorized host      | Agent credential + JSON      | Agent-scoped API     |
+----------------------+                              +----------------------+
```

All four components are local to the MVP environment. The Agent communicates with the Backend, never with PostgreSQL directly. The Frontend also communicates only with the Backend.

## Component Responsibilities

### React Frontend

The React + TypeScript + Vite single-page application provides the dashboard and role-aware views for Administrators, Security Analysts, and Viewers. It displays agents, devices, vulnerabilities, logs, alerts, threat intelligence, reports, and risk. Administrators manage users and settings; Administrators and Security Analysts run scans and investigate alerts; Viewers remain read-only.

The Frontend uses HTTP/HTTPS REST, JSON, and user JWT authentication. The MVP does not require WebSockets; screens refresh or refetch data through the REST API.

### FastAPI Backend

The Backend authenticates users, enforces default-deny RBAC, authenticates Agents with separate credentials, validates incoming data, coordinates scan tasks, normalizes logs, performs deterministic threat detection and risk scoring, manages alerts, invokes the AIService, generates reports, and writes application data to PostgreSQL.

### PostgreSQL

A single local PostgreSQL 14+ instance stores users and roles, Agents and heartbeats, devices, scans, vulnerabilities, normalized logs, threat indicators, alerts and timelines, reports, and audit events. The database is reached only through Backend data-access code.

### CyberShield Agent

The Python Agent runs on an authorized host. Its internal modules collect system and network data, discover devices with Nmap, scan ports and service versions, collect authorized Linux logs, and report results. It registers with an Administrator-issued enrollment token, then uses its Agent credential for heartbeat, upload, task retrieval, and task-status operations.

## Security and Authorization Boundary

Human users authenticate with email/username and password and receive JWTs. The three roles are Administrator, Security Analyst, and Viewer. Authorization is enforced per endpoint with deny as the default. The Agent is a non-human actor, not a dashboard user. It cannot access user management, role or permission management, system settings, other organizations' data, or PostgreSQL directly.

Only authorized networks and systems may be scanned. The scan workflow must show the SRS authorization notice before a scan or discovery action.

## AI Boundary

Application code depends on the provider-agnostic `AIService` interface. `LocalRuleAI` is the only implementation in the MVP and produces deterministic, template-based explanations for alerts, vulnerabilities, and risk scores without external calls. `OllamaAI` and `OpenAIProvider` are future implementations of the same interface and are not part of the current deployment.

## Related Documents

- [Backend Architecture](backend-architecture.md)
- [Frontend Architecture](frontend-architecture.md)
- [Agent Architecture](agent-architecture.md)
- [Data Flow](data-flow.md)
- [Deployment Architecture](deployment-architecture.md)
