# Relationships, Cardinality, and Cascading Rules

This document defines the MVP relationship model used by the schema. It is aligned to the architecture documents and the corrected SRS, particularly the Agent restrictions and the need for transparent, auditable risk scoring.

## Core Relationship Model

### organization ownership

- organizations 1:N users
- organizations 1:N agents
- organizations 1:N devices
- organizations 1:N scans
- organizations 1:N logs
- organizations 1:N alerts
- organizations 1:N threat_indicators
- organizations 1:N reports
- organizations 1:N ai_conversations
- organizations 1:N notifications
- organizations 1:N audit_logs
- organizations 1:N system_settings

Rule: every table with organization-scoped data includes `organization_id`, even in a single-organization MVP. This prevents future retrofitting.

### user and RBAC model

- roles 1:N users
- roles N:M permissions through role_permissions
- users 1:N reports created_by_user_id
- users 1:N ai_conversations
- users 1:N audit_logs actor records

Rule: users are human actors only. Agent identity is stored separately and never conflated with user auth.

### Agent model and isolation

- agents 1:N agent_credentials
- agents 1:N agent_heartbeats
- agents 1:N scans
- agents 1:N logs
- agents 1:N alerts
- agents 1:N devices (optional source-agent relation)

Rule: Agent credential storage is a separate table from the user table. This matches the SRS requirement that the Agent is not a user role and cannot access user endpoints or the database directly.

Identity rule: the stable Agent identity is `agents.id`; `hostname` is not unique and is treated as mutable metadata. This avoids accidental collisions when multiple authorized hosts share a hostname, when a machine is renamed, or when a VM is cloned.

### Discovery and vulnerability pipeline

- scans 1:N scan_results
- scans 1:N vulnerabilities
- scans 1:N reports (report may summarize a timeframe that includes multiple scans)
- devices 1:N scan_results
- devices 1:N vulnerabilities
- devices 1:N logs
- devices 1:N alerts
- devices 1:N risk_scores
- devices 1:N device_interfaces

Rule: the scan result is stored as raw evidence; the vulnerability table is the normalized interpretation of the evidence.

### Alert and risk model

- alerts 1:N alert_events
- alerts 1:N notifications
- alerts 1:N risk_scores
- device risk and alert risk use the same risk_scores table with `entity_type` and `entity_id` values.

Rule: risk_scores stores both the final numeric result and the full factor breakdown in JSONB, so FR-11.1 to FR-11.3 remain auditable.

### AI explanation model

- ai_conversations 1:N ai_messages
- ai_conversations references the subject entity via `(subject_type, subject_id)` rather than a direct FK to specific alert or vulnerability tables because the explanation can be generated for alerts, vulnerabilities, or risk scores.

Rule: provider type is generic, not tied to any specific vendor. The provider field remains provider-agnostic and supports future implementations behind the AIService abstraction.

## Cascading Rules

### Soft-delete as the default pattern

The MVP uses soft-delete semantics on operational business records rather than hard deletes. Tables with `deleted_at` or `is_active` do not physically remove the row unless an explicit data-retention cleanup is implemented later.

This preserves historical evidence and keeps audit timelines valid.

### Specific cascade and delete behavior

- Organization delete: CASCADE to all child organization-scoped tables. There is no meaningful orphaned data if the owner organization is removed.
- User delete: prefer soft-delete; do not hard-delete if the user is referenced by audit logs or report ownership. The application should mark `is_active = false` or set `deleted_at`.
- Agent delete: soft-delete rather than hard delete. A deleted or revoked Agent must remain visible in audit history and heartbeat records.
- Device delete: soft-delete. `scan_results`, `vulnerabilities`, `logs`, and `alerts` remain stored for historical evidence; the device is logically retired without destroying the record trail.
- Scan delete: soft-delete; keep raw results and derived findings for audit. The application may prevent hard delete in production.
- Alert delete: avoid physical delete in MVP; maintain alert history and timeline. Only status changes should update state.
- Report delete: soft-delete, unless retention rules later say otherwise.
- Conversation delete: cascade delete its message rows, because a conversation is meaningless without its message history.
- Notification delete: since dashboard notifications are transient, a hard delete is acceptable after read expiry, but the alert history remains in `alerts` and `alert_events`.

## Organization Isolation Notes

- A user can view only records for their own `organization_id`.
- The same rule is enforced for Agents, devices, logs, alerts, threat indicators, reports, and audit logs.
- Even though the MVP may run with one organization only, the schema already embeds `organization_id` in all org-scoped tables to prevent a later multi-tenant retrofit from becoming a data migration problem.

## Indexing and Query Patterns

The schema aims for fast access on the main MVP filters and join paths:

- `organization_id` on all org-scoped tables
- `agent_id`, `device_id`, and `status` on alert and log queries
- `timestamp` or `created_at` for activity feeds and dashboards
- `scan_id` and `device_id` on scan result lookups
- `risk_band`, `severity`, and `entity_id` on risk analysis pages
- `status` and `triggered_at` on alert and report views

## Data Integrity Notes

- `users.password_hash` stores only the bcrypt hash, never plaintext.
- `agent_credentials` are separate from `users` to enforce the Agent-only auth boundary.
- `risk_scores.factor_breakdown` is required to preserve transparent formula auditability.
- `audit_logs` is the canonical record of state changes, especially role changes, scan lifecycle, alert transitions, and report generation.
- `system_settings` stores thresholds like heartbeat intervals or scan config values without turning them into hard-coded constants.

## Future-Proofing Without Violating MVP

This relationship model does not assume read replicas, sharding, Kubernetes, or cloud-managed services. It is intentionally local-first and compatible with a later single-VM Docker Compose phase, while still embedding the organization boundary needed for eventual multi-organization expansion.
