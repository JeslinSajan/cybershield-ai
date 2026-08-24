# Table-by-Table Design

Each table below is justified from the corrected SRS and architecture documents. The design is intentionally narrow; tables without clear requirement traceability are excluded.

## 1. organizations

Purpose: tenant boundary for all organization-scoped data.

FR support: FR-2.1, FR-4.1, FR-5.1, FR-8.1, FR-16.1, notes in user-roles.md about cross-organization access.

Roles: Administrator can view/manage; Security Analyst and Viewer read only within their org.

## 2. roles

Purpose: global RBAC catalog (Administrator, Security Analyst, Viewer).

FR support: FR-2.2, FR-3.1, FR-3.2, FR-3.3.

Roles: Administrator manages roles and permissions; Security Analyst and Viewer are constrained by their assigned role.

## 3. permissions

Purpose: individual authorizations used in default-deny access checks.

FR support: FR-3.1, FR-3.2, FR-3.3.

Roles: Administrator manages the set; read-only for the rest.

## 4. role_permissions

Purpose: maps role to permission pairs.

FR support: FR-3.1.

Roles: Administrator only.

## 5. users

Purpose: human accounts and their role assignment.

FR support: FR-1.1 to FR-1.5, FR-2.1 to FR-2.3, FR-16.1.

Roles: Administrator can create/update/deactivate; Security Analyst and Viewer are not allowed to manage users.

## 6. agents

Purpose: host-level Agent inventory with online/offline state.

FR support: FR-4.1 to FR-4.6, FR-5.1, FR-12.1, FR-16.1.

Roles: Administrator can register/revoke; Security Analyst can view.

## 7. agent_credentials

Purpose: separate credential storage for the non-human Agent actor.

FR support: FR-4.2, FR-4.5, FR-4.6.

Roles: Administrator manages; Agent uses the credential only through its API boundary.

## 8. agent_heartbeats

Purpose: historical health and status timeline.

FR support: FR-4.3, FR-4.4, FR-7.2, FR-17.3.

Roles: Administrator can view; Security Analyst can read; Viewer reads only.

## 9. devices

Purpose: discovered devices and current online/offline state.

FR support: FR-5.2, FR-5.3, FR-17.1, FR-17.3.

Roles: Administrator and Security Analyst can view/read; only Administrators and Analysts trigger scans.

## 10. device_interfaces

Purpose: network interface-level data for recent network activity and device inventory.

FR support: FR-5.2, FR-7.1.

Roles: Administrators and Analysts can view.

## 11. scans

Purpose: scheduled/triggered discovery and vulnerability work items.

FR support: FR-5.1, FR-6.1, FR-16.1.

Roles: Administrator and Security Analyst can start; Viewer cannot.

## 12. scan_results

Purpose: raw result payloads from a scan, preserving evidence for later audit and dashboard review.

FR support: FR-5.2, FR-6.1, FR-6.2.

Roles: Administrator and Security Analyst can review; Viewers can read.

## 13. cves

Purpose: local or cached CVE reference data for vulnerability matching.

FR support: FR-6.2, FR-6.3, FR-6.4.

Roles: Administrator and Security Analyst can view and manage seeded data; Viewers read only.

## 14. vulnerabilities

Purpose: normalized findings after service/version matching.

FR support: FR-6.2, FR-6.3, FR-17.1, FR-17.2.

Roles: Administrator and Security Analyst can read; Viewer can read only.

## 15. logs

Purpose: normalised SSH/auth log and system log events.

FR support: FR-8.1, FR-8.2, FR-8.3, FR-9.1 to FR-9.4.

Roles: Administrator and Security Analyst can read filtered data; Viewer can read only, subject to settings.

## 16. threat_indicators

Purpose: local IP/domain/hash indicators used by detection.

FR support: FR-9.4, FR-10.1, FR-10.2.

Roles: Administrator and Security Analyst can search and manage; Viewer can read only.

## 17. alerts

Purpose: security alert records and their status.

FR support: FR-9.1 to FR-9.4, FR-12.1 to FR-12.3, FR-17.1 to FR-17.3.

Roles: Administrator and Security Analyst can investigate and change status; Viewer can read.

## 18. alert_events

Purpose: alert lifecycle timeline and audit trail.

FR support: FR-12.3, FR-16.1.

Roles: Administrator and Security Analyst can read; Viewer can read only.

## 19. risk_scores

Purpose: transparent formula outputs for device/alert risk calculations.

FR support: FR-11.1 to FR-11.3, FR-17.1, FR-17.2.

Roles: Administrator and Security Analyst can view; Viewer reads only.

## 20. reports

Purpose: generated downloadable PDF/CSV reports.

FR support: FR-14.1, FR-14.2, FR-16.1.

Roles: Administrator, Security Analyst, and Viewer can view/download if permitted by report access rules.

## 21. ai_conversations

Purpose: conversation records for Local Security Explanation Engine usage.

FR support: FR-13.1, FR-13.2, FR-13.4.

Roles: Administrator and Security Analyst can use; Viewer cannot.

## 22. ai_messages

Purpose: message payloads in AI explanation conversations.

FR support: FR-13.1, FR-13.2.

Roles: Administrator and Security Analyst are owners of the conversation; Viewer cannot access.

## 23. notifications

Purpose: in-dashboard notifications for new critical/high alerts.

FR support: FR-15.1, FR-15.2.

Roles: Administrator and Security Analyst receive and read; Viewer can read only if configured.

## 24. audit_logs

Purpose: immutable activity trail for critical system events.

FR support: FR-16.1, FR-16.2.

Roles: Administrator can view; Security Analyst and Viewer cannot.

## 25. system_settings

Purpose: local configuration values such as thresholds, scan intervals, and operational default parameters.

FR support: FR-4.3, FR-9.1, FR-9.2, FR-16.1.

Roles: Administrator manages; Security Analyst and Viewer cannot change system settings.

## Proposed table intentionally excluded

The following is not included in the MVP schema because it is not directly justified by the corrected FR set:

- message_queue or task_queue tables: the SRS and architecture documents do not require a distributed broker; the MVP is a single local FastAPI process and an Agent may queue retry data locally, not via a central broker table.
- managed_backup_history: not required in the local laptop MVP and not called out in FRs.
- multi_region_geo tables: forbidden by the local-first constraints.
- dedicated oauth_provider or mfa tables: no MFA requirement in the MVP.
