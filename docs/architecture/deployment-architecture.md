# CyberShield AI - Deployment Architecture

**Version:** 2.0  
**Phase:** 2 of 27 - System Architecture Design

## Current - Local Development MVP

The complete demonstrable pipeline runs on one developer laptop. Components may be started directly from their native runtimes or packaged for a reproducible local run, but the topology remains the same four components.

```text
Developer laptop
+----------------------------------------------------------------+
| React dev server       localhost:5173                          |
| FastAPI process        localhost:8000                          |
| PostgreSQL             localhost:5432                          |
| CyberShield Agent      local process / authorized host process |
+----------------------------------------------------------------+
```

- React is served by Vite and calls FastAPI over local HTTP/HTTPS REST.
- FastAPI is one application process and calls one local PostgreSQL instance.
- The Agent calls FastAPI using its separate Agent credential.
- No reverse proxy, orchestration layer, or distributed service is required.
- No external AI service is required; the Backend constructs `LocalRuleAI` through `AIService`.
- PostgreSQL backups, migrations, and seeded/local CVE data are handled as local development operations.

The local environment assumes Python, Node.js, PostgreSQL 14+, and Nmap are available. The Agent may run on an authorized Linux host reachable from the laptop when that is needed for a demonstration.

## Future - Phase 24+

This is a packaging and hosting option, not the current MVP topology. A future cloud phase will deploy the same four application components with Docker Compose on a single Microsoft Azure VM (12-month free tier, B1S instance, Linux). An optional Nginx reverse proxy may then provide a public entry point and TLS termination.

```text
Future Azure VM deployment (Phase 24+)
+---------------------------------------------------------------+
| Azure VM (B1S, Linux)                                         |
|   Nginx (optional edge entry point)                           |
|     |                                                         |
|     +--> React static assets                                  |
|     +--> FastAPI application --> PostgreSQL                   |
|                                                               |
|   CyberShield Agent connects to the FastAPI Agent API         |
+---------------------------------------------------------------+
```

Future work may also add an external AI provider behind `AIService`, but `LocalRuleAI` remains the baseline implementation. Any later hosting, networking, or scaling decision must be documented as a future phase and must not be read back into the MVP architecture.

## Operational Boundary

The deployment does not grant the Agent database credentials. User and Agent credentials remain separate, and Backend authorization remains the controlling boundary in every environment. Only authorized systems and networks may be scanned.
