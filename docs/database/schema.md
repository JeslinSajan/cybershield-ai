# Schema Definition

This schema is the MVP baseline for the local-first CyberShield AI platform. It is kept intentionally narrow and traces directly to the corrected SRS and architecture requirements.

## Conventions

- PostgreSQL 14+ local database
- UUID primary keys for cross-table identity
- TIMESTAMPTZ for time values
- `organization_id` present on every organization-scoped table
- `created_at` and `updated_at` on all main tables
- `deleted_at` on business entities for soft-delete semantics when needed
- Default-deny RBAC is enforced in the application layer; this document records data ownership, not endpoint permissions

## 1. organizations

Purpose: root tenant scope for all project data.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | Stable internal identity |
| name | VARCHAR(150) | NOT NULL | Organization name |
| slug | VARCHAR(80) | UNIQUE, NOT NULL | For stable references |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_organizations_slug` on slug.

## 2. roles

Purpose: global role catalog used by application authorization.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| name | VARCHAR(50) | UNIQUE, NOT NULL | Administrator, Security Analyst, Viewer |
| description | TEXT | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

## 3. permissions

Purpose: named permissions used in role-based access control.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| resource | VARCHAR(80) | NOT NULL | e.g. users, agents, scans |
| action | VARCHAR(50) | NOT NULL | e.g. read, write, manage |
| description | TEXT | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Unique: `(resource, action)`.

## 4. role_permissions

Purpose: many-to-many mapping between roles and permissions.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| role_id | UUID | FK -> roles.id, NOT NULL | |
| permission_id | UUID | FK -> permissions.id, NOT NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Unique: `(role_id, permission_id)`. Index: `idx_role_permissions_role_id`.

## 5. users

Purpose: human application accounts.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | Org ownership |
| role_id | UUID | FK -> roles.id, NOT NULL | Current role |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login identifier |
| username | VARCHAR(80) | NULL | Optional username |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | Deactivation instead of hard delete |
| failed_login_count | INTEGER | NOT NULL DEFAULT 0 | For lockout control |
| last_login_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| deleted_at | TIMESTAMPTZ | NULL | Soft-delete safeguard |

Indexes: `idx_users_org_email`, `idx_users_role_id`, `idx_users_org_active`.

## 6. agents

Purpose: authorized host-side agents.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | Org ownership |
| name | VARCHAR(120) | NOT NULL | Friendly label |
| hostname | VARCHAR(120) | NULL | Hostname from the machine; not unique by design |
| status | VARCHAR(20) | NOT NULL DEFAULT 'PENDING' | PENDING, ONLINE, OFFLINE |
| version | VARCHAR(50) | NULL | Agent version |
| last_heartbeat_at | TIMESTAMPTZ | NULL | |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |

Indexes: `idx_agents_org_status`, `idx_agents_last_heartbeat`, `idx_agents_active`.

Note: `hostname` is intentionally not unique. Hostnames can be reused, can change after a system rename, and are not a stable identity for an Agent. The stable identity is the UUID `id` on the `agents` table; all foreign-key references and audit records point to that agent_id.

## 7. agent_credentials

Purpose: separate credentials for the non-human Agent actor.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| agent_id | UUID | FK -> agents.id, NOT NULL | |
| credential_hash | VARCHAR(255) | NOT NULL | Stored secret hash or token hash |
| type | VARCHAR(30) | NOT NULL DEFAULT 'token' | token, api_key, or password-like secret |
| issued_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| expires_at | TIMESTAMPTZ | NULL | Time-limited token support |
| revoked_at | TIMESTAMPTZ | NULL | Revoke/rotate without full re-enrollment |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_agent_credentials_agent_active`, `idx_agent_credentials_expires_at`.

## 8. agent_heartbeats

Purpose: periodic health state for each Agent.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| agent_id | UUID | FK -> agents.id, NOT NULL | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | Denormalized for org-scoped filtering |
| timestamp | TIMESTAMPTZ | NOT NULL | Heartbeat time |
| status | VARCHAR(20) | NOT NULL | ONLINE/OFFLINE/ERROR |
| version | VARCHAR(50) | NULL | |
| cpu_percent | NUMERIC(5,2) | NULL | |
| memory_percent | NUMERIC(5,2) | NULL | |
| details | JSONB | NULL | Flexible health payload |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_agent_heartbeats_agent_time`, `idx_agent_heartbeats_org_time`.

## 9. devices

Purpose: discovered and observed network devices.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | Org ownership |
| agent_id | UUID | FK -> agents.id, NULL | Source agent |
| ip_address | INET | NOT NULL | Device IP |
| mac_address | VARCHAR(17) | NULL | Device MAC where available |
| hostname | VARCHAR(120) | NULL | |
| vendor | VARCHAR(120) | NULL | |
| device_type | VARCHAR(40) | NULL | workstation, server, router, iot |
| status | VARCHAR(20) | NOT NULL DEFAULT 'unknown' | online/offline/unknown |
| last_seen_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |

Unique: `(organization_id, ip_address)` when ip_address value is present. Indexes: `idx_devices_org_status`, `idx_devices_agent_id`, `idx_devices_last_seen`.

## 10. device_interfaces

Purpose: network interfaces associated with a device.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| device_id | UUID | FK -> devices.id, NOT NULL | |
| name | VARCHAR(80) | NOT NULL | eth0, wlan0 |
| mac_address | VARCHAR(17) | NULL | |
| ip_address | INET | NULL | Virtual interface IP |
| bytes_sent | BIGINT | NOT NULL DEFAULT 0 | |
| bytes_received | BIGINT | NOT NULL DEFAULT 0 | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_device_interfaces_device_id`, `idx_device_interfaces_org_device`.

## 11. scans

Purpose: discovery and vulnerability scan tasks initiated by user actions.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| agent_id | UUID | FK -> agents.id, NULL | Agent assigned to run the scan |
| created_by_user_id | UUID | FK -> users.id, NOT NULL | Initiator |
| scan_type | VARCHAR(30) | NOT NULL | discovery, vulnerability |
| status | VARCHAR(20) | NOT NULL DEFAULT 'PENDING' | PENDING, RUNNING, COMPLETED, FAILED |
| target_scope | TEXT | NOT NULL | Authorized network or target description |
| started_at | TIMESTAMPTZ | NULL | |
| completed_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_scans_org_status`, `idx_scans_agent_id`, `idx_scans_created_by_user`.

## 12. scan_results

Purpose: per-device output captured during a scan.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| scan_id | UUID | FK -> scans.id, NOT NULL | Parent scan |
| device_id | UUID | FK -> devices.id, NOT NULL | Result for this device |
| result_type | VARCHAR(30) | NOT NULL | ports, services, system, logs |
| raw_payload | JSONB | NOT NULL | Agent-provided structured data |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_scan_results_scan_id`, `idx_scan_results_device_id`, `idx_scan_results_org_scan`.

## 13. cves

Purpose: local or cached CVE dataset used for service/version matching.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | Allows local organizational seeding |
| cve_id | VARCHAR(50) | UNIQUE, NOT NULL | e.g. CVE-2023-1234 |
| severity | VARCHAR(15) | NOT NULL | Low/Medium/High/Critical |
| cvss_score | NUMERIC(4,1) | NULL | |
| affected_service | VARCHAR(80) | NULL | |
| affected_version | VARCHAR(120) | NULL | |
| summary | TEXT | NOT NULL | Human-readable summary |
| recommendation | TEXT | NULL | |
| source | VARCHAR(40) | NOT NULL DEFAULT 'local_seed' | local_seed or cached_feed |
| is_demo_data | BOOLEAN | NOT NULL DEFAULT TRUE | Must remain clearly labeled |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_cves_org_severity`, `idx_cves_service_version`, `idx_cves_cve_id`.

## 14. vulnerabilities

Purpose: identified weaknesses for a device, tied back to scan results and CVE data.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| device_id | UUID | FK -> devices.id, NOT NULL | |
| scan_id | UUID | FK -> scans.id, NULL | Optional associated scan |
| cve_id | UUID | FK -> cves.id, NULL | |
| severity | VARCHAR(15) | NOT NULL | Low/Medium/High/Critical |
| score | NUMERIC(5,2) | NULL | Base CVSS or derived score |
| description | TEXT | NOT NULL | |
| recommendation | TEXT | NULL | |
| status | VARCHAR(25) | NOT NULL DEFAULT 'open' | open/resolved/ignored |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_vulnerabilities_org_device`, `idx_vulnerabilities_severity`, `idx_vulnerabilities_scan_id`.

## 15. logs

Purpose: normalized log entries from authorized system logs.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| agent_id | UUID | FK -> agents.id, NOT NULL | |
| device_id | UUID | FK -> devices.id, NULL | Optional linked device |
| source | VARCHAR(80) | NOT NULL | auth.log, syslog |
| event_type | VARCHAR(80) | NOT NULL | ssh_login, port_scan_signal |
| severity | VARCHAR(20) | NOT NULL | info, warning, error |
| message | TEXT | NOT NULL | Raw normalized message |
| source_ip | INET | NULL | |
| username | VARCHAR(120) | NULL | |
| timestamp | TIMESTAMPTZ | NOT NULL | Event time |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_logs_org_time`, `idx_logs_agent_id`, `idx_logs_device_id`, `idx_logs_severity`.

## 16. threat_indicators

Purpose: local indicator base used for malware and suspicious-activity matching.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| indicator_type | VARCHAR(20) | NOT NULL | ip, domain, hash |
| value | VARCHAR(255) | NOT NULL | |
| description | TEXT | NULL | |
| source | VARCHAR(50) | NOT NULL DEFAULT 'local' | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Unique: `(organization_id, indicator_type, value)`. Indexes: `idx_threat_indicators_type_value`.

## 17. alerts

Purpose: generated security events and their lifecycle state.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| agent_id | UUID | FK -> agents.id, NULL | Source agent |
| device_id | UUID | FK -> devices.id, NULL | Affected device |
| alert_type | VARCHAR(40) | NOT NULL | brute_force, port_scan, suspicious_login, malware_indicator |
| severity | VARCHAR(15) | NOT NULL | Low/Medium/High/Critical |
| status | VARCHAR(25) | NOT NULL DEFAULT 'Open' | Open, Acknowledged, Investigating, Resolved, False Positive |
| description | TEXT | NOT NULL | |
| risk_score | NUMERIC(5,2) | NOT NULL | Final score |
| triggered_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_alerts_org_status`, `idx_alerts_severity`, `idx_alerts_device_id`, `idx_alerts_triggered_at`.

## 18. alert_events

Purpose: complete status timeline for each alert.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| alert_id | UUID | FK -> alerts.id, NOT NULL | |
| actor_user_id | UUID | FK -> users.id, NULL | Who changed status |
| from_status | VARCHAR(25) | NULL | |
| to_status | VARCHAR(25) | NOT NULL | |
| reason | TEXT | NULL | Optional explanation |
| changed_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_alert_events_alert_changed_at`.

## 19. risk_scores

Purpose: transparent formula records for risk score calculation.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| entity_type | VARCHAR(30) | NOT NULL | device, alert |
| entity_id | UUID | NOT NULL | Linked device or alert |
| score | NUMERIC(5,2) | NOT NULL | Final 0-100 score |
| risk_band | VARCHAR(20) | NOT NULL | Low, Medium, High, Critical |
| factor_breakdown | JSONB | NOT NULL | Formula inputs and weights |
| formula_version | VARCHAR(40) | NOT NULL DEFAULT 'v1' | For auditability |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_risk_scores_org_entity`, `idx_risk_scores_band`.

## 20. reports

Purpose: generated PDF/CSV summaries for selected time windows.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| created_by_user_id | UUID | FK -> users.id, NOT NULL | |
| report_type | VARCHAR(30) | NOT NULL | summary, vulnerability, alert |
| period_start | TIMESTAMPTZ | NOT NULL | |
| period_end | TIMESTAMPTZ | NOT NULL | |
| file_name | VARCHAR(255) | NULL | Stored file reference |
| mime_type | VARCHAR(50) | NULL | application/pdf or text/csv |
| status | VARCHAR(20) | NOT NULL DEFAULT 'READY' | READY, GENERATING, FAILED |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_reports_org_time`, `idx_reports_created_by_user`.

## 21. ai_conversations

Purpose: provider-agnostic conversation records for Local Security Explanation Engine requests.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| user_id | UUID | FK -> users.id, NOT NULL | User who requested the explanation |
| subject_type | VARCHAR(30) | NOT NULL | alert, vulnerability, risk_score |
| subject_id | UUID | NOT NULL | Related record |
| provider_type | VARCHAR(30) | NOT NULL DEFAULT 'local_rule_ai' | provider-agnostic value |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_ai_conversations_user_id`, `idx_ai_conversations_org_subject`.

## 22. ai_messages

Purpose: message history for AI explanations.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| conversation_id | UUID | FK -> ai_conversations.id, NOT NULL | |
| role | VARCHAR(20) | NOT NULL | user, assistant, system |
| content | TEXT | NOT NULL | Prompt or explanation text |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_ai_messages_conversation_id`.

## 23. notifications

Purpose: dashboard notifications for new critical and high alerts.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| user_id | UUID | FK -> users.id, NULL | Target recipient |
| alert_id | UUID | FK -> alerts.id, NULL | Related alert |
| notification_type | VARCHAR(30) | NOT NULL | alert, report, info |
| channel | VARCHAR(20) | NOT NULL DEFAULT 'dashboard' | dashboard, email, telegram, slack |
| title | VARCHAR(200) | NOT NULL | |
| body | TEXT | NOT NULL | |
| is_read | BOOLEAN | NOT NULL DEFAULT FALSE | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_notifications_user_unread`, `idx_notifications_org_alert`.

## 24. audit_logs

Purpose: required audit trail for user and agent actions.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| actor_type | VARCHAR(20) | NOT NULL | user, agent, system |
| actor_id | UUID | NULL | User or agent ID |
| action | VARCHAR(80) | NOT NULL | login, role_change, scan_started |
| target_type | VARCHAR(80) | NULL | users, agents, alerts, reports |
| target_id | UUID | NULL | |
| details | JSONB | NULL | Structured payload |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Indexes: `idx_audit_logs_org_time`, `idx_audit_logs_actor_id`, `idx_audit_logs_action`.

## 25. system_settings

Purpose: configuration values for system-wide or per-organization settings.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| organization_id | UUID | FK -> organizations.id, NOT NULL | |
| key | VARCHAR(120) | NOT NULL | e.g. heartbeat_interval |
| value | JSONB | NOT NULL | Stored configuration value |
| created_by_user_id | UUID | FK -> users.id, NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

Unique: `(organization_id, key)`. Index: `idx_system_settings_org_key`.

## Migration Strategy Notes

This schema is designed to support Alembic migrations in a future Phase 7 baseline. A practical migration order is:

1. Create reference tables: organizations, roles, permissions, role_permissions.
2. Create users and agents plus their credential tables.
3. Create devices, device_interfaces, scans, scan_results, and cves.
4. Create logs and threat_indicators.
5. Create alerts, alert_events, risk_scores.
6. Create reports, ai_conversations, ai_messages, notifications.
7. Create audit_logs and system_settings.

The MVP should avoid managed cloud-only assumptions. No read replica, shard key, or multi-region configuration is modeled. Local PostgreSQL is the source of truth, and the database is intentionally simple enough to run on one developer laptop.
