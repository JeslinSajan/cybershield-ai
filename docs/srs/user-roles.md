# CyberShield AI — User Roles & Permissions

Version 1.0 | Companion to SRS.md

Three roles exist in the MVP. The default authorization policy is
**deny** — any action not explicitly listed as allowed for a role is
forbidden for that role.

---

## Role Summary

| Role | Description |
|---|---|
| **Administrator** | Full control of the platform, including users, roles, agents, and system settings |
| **Security Analyst** | Day-to-day operator: runs scans, investigates alerts, uses the AI assistant, generates reports |
| **Viewer** | Read-only access for oversight/reporting purposes |

A fourth actor, the **CyberShield Agent**, is not a user role — it
authenticates with its own Agent credential and can only perform
Agent-scoped actions (register, heartbeat, upload authorized data,
receive scan tasks, report task status). It cannot log into the
dashboard and has no access to user, role, or settings endpoints.

---

## Permission Matrix

| Module / Action | Administrator | Security Analyst | Viewer |
|---|:---:|:---:|:---:|
| View Dashboard | ✅ | ✅ | ✅ |
| View Agents | ✅ | ✅ | ✅ |
| Register / Revoke Agents | ✅ | ❌ | ❌ |
| View Devices | ✅ | ✅ | ✅ |
| Run Discovery / Scans | ✅ | ✅ | ❌ |
| View Vulnerabilities | ✅ | ✅ | ✅ |
| View Logs | ✅ | ✅ | ✅ (read-only, may be restricted per settings) |
| Investigate / Update Alerts | ✅ | ✅ | ❌ |
| View Alerts | ✅ | ✅ | ✅ |
| Use AI Security Assistant | ✅ | ✅ | ❌ |
| Generate / View Reports | ✅ | ✅ | ✅ (view only) |
| View Threat Intelligence | ✅ | ✅ | ✅ |
| Manage Users | ✅ | ❌ | ❌ |
| Manage Roles / Permissions | ✅ | ❌ | ❌ |
| Manage Agent Settings | ✅ | ❌ | ❌ |
| Manage Notifications Config | ✅ | ❌ | ❌ |
| Manage System Settings | ✅ | ❌ | ❌ |
| View Audit Logs | ✅ | ❌ | ❌ |

---

## Notes

- A Security Analyst can operate the platform fully day-to-day but
  cannot alter who has access or how the system is configured.
- A Viewer exists for stakeholders (e.g. a project guide/evaluator)
  who need to see the system's state without being able to change
  anything — this also protects against accidental data changes
  during a demo.
- Cross-organization access is denied by default; a user shall only
  see agents/devices/data belonging to their own organization, even
  though the MVP may operate with a single organization for the
  academic demonstration.
