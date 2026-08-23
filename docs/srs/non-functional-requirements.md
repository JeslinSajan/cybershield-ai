# CyberShield AI — Non-Functional Requirements

Version 1.0 | Companion to SRS.md

Scoped realistically for a single-laptop MVP built by a small
final-year student team — not enterprise SLAs.

---

## NFR-1: Security

- NFR-1.1: All user passwords shall be hashed with bcrypt; plaintext
  passwords shall never be stored or logged.
- NFR-1.2: All API endpoints (except login/register/health) shall
  require a valid JWT.
- NFR-1.3: All write operations shall be authorized against the RBAC
  model with a default-deny policy.
- NFR-1.4: Agent credentials shall be distinct from user credentials
  and scoped to Agent-only operations (register, heartbeat, upload
  data, receive tasks) — an Agent credential shall never grant access
  to user management, role management, or direct database access.
- NFR-1.5: No secrets (JWT signing key, database password, Agent
  credentials) shall be committed to the repository; all secrets
  shall be provided via `.env`, excluded via `.gitignore`.
- NFR-1.6: All database queries shall use the SQLAlchemy ORM or
  parameterized queries — no raw string-concatenated SQL.
- NFR-1.7: CORS shall be explicitly configured to allow only the
  known local frontend origin(s) during development.

## NFR-2: Performance

- NFR-2.1: Typical API endpoints shall respond within 500ms on local
  hardware under normal development load (single user, small dataset)
  — not a distributed-system SLA.
- NFR-2.2: A device discovery scan of a small local network (≤ 50
  hosts) shall complete within a few minutes, acknowledging that Nmap
  scan time is inherently variable.
- NFR-2.3: The dashboard shall load its primary view within 3 seconds
  on local network conditions.

## NFR-3: Reliability

- NFR-3.1: If the Agent loses connectivity to the Backend, it shall
  retry with backoff rather than crash, and shall resume normal
  operation once connectivity is restored.
- NFR-3.2: If an external CVE lookup service is unreachable, the
  system shall continue functioning using local/seeded CVE data
  rather than failing the scan entirely.
- NFR-3.3: A single Agent or scan failure shall not crash the Backend
  or affect unrelated Agents/devices.

## NFR-4: Usability

- NFR-4.1: The dashboard shall use a consistent dark SOC-style theme
  with color meaning reserved for status/severity (not decorative use).
- NFR-4.2: Every scan/discovery action shall visibly state the
  authorized-use requirement before execution.
- NFR-4.3: Error states (failed scan, offline Agent, failed report
  generation) shall be shown to the user with a clear, non-technical
  message, with technical detail available on request (e.g. expandable
  detail or logs).

## NFR-5: Maintainability

- NFR-5.1: Backend code shall follow a layered structure (API routes /
  services / models) so business logic is not embedded directly in
  route handlers.
- NFR-5.2: The `AIService` interface shall be the only integration
  point for AI-labeled features, so swapping `LocalRuleAI` for a
  future provider requires no changes outside that boundary.
- NFR-5.3: Database schema changes shall be managed through Alembic
  migrations, not manual schema edits.

## NFR-6: Privacy

- NFR-6.1: The system shall only process data from systems the
  operating organization is authorized to monitor.
- NFR-6.2: Collected log data (e.g. usernames in auth logs) shall be
  accessible only to authenticated users with an appropriate role, not
  exposed via any public/unauthenticated endpoint.

## NFR-7: Portability / Deployment

- NFR-7.1: The full stack (frontend, backend, database) shall run via
  a single `docker-compose up` command for local development.
- NFR-7.2: No component shall hard-code `localhost`-only assumptions
  in a way that would require code changes (not just configuration
  changes) to deploy to a cloud VM later.

---

**Explicitly not required for the MVP** (see SRS.md Section 5 for the
full list): 1,000+ concurrent users, horizontal scaling, load
balancing, database sharding, 99.9% uptime guarantees, automated
failover/disaster recovery, GDPR/ISO 27001 operational compliance,
multi-factor authentication.
