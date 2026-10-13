# Settings API Contract

Base path: `/api/v1`

This contract covers the system settings and threshold configuration required by the schema and by FR-4.3, FR-9.1, FR-9.2, and FR-16.1. It is strictly limited to Administration and does not expose user-facing configuration to Agent endpoints.

## FR Traceability
- FR-4.3: configurable heartbeat interval and health reporting
- FR-9.1: configurable brute-force threshold and window
- FR-9.2: configurable port-scan threshold and window
- FR-16.1: settings changes are audit logged

## Authorization Matrix
- Administrator: create, update, read settings
- Security Analyst: no settings management access
- Viewer: no settings management access
- Agent: no access

## Endpoints

### GET /settings

- Auth requirement: JWT required
- Authorization: Administrator only
- Request schema: none
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "key": "heartbeat_interval_seconds",
    "value": 60,
    "created_by_user_id": "uuid",
    "created_at": "2026-08-24T10:00:00Z",
    "updated_at": "2026-08-24T10:00:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### PUT /settings/{key} or PATCH /settings/{key}

- Auth requirement: JWT required
- Authorization: Administrator only
- Request schema:

```json
{
  "value": 120
}
```

- Response schema:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "key": "heartbeat_interval_seconds",
  "value": 120,
  "updated_at": "2026-08-24T12:30:00Z"
}
```

- Success status: `200 OK`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
- Notes: This is a system-configuration endpoint. Creates an AuditLog entry with action `setting_updated`.

### GET /settings/audit-logs (Alias: GET /audit-logs/)

- Auth requirement: JWT required
- Authorization: Administrator only (FR-16.1)
- Query parameters:
  - `action` (optional string): filter by audit log action
  - `actor_type` (optional string): filter by actor type (`user`, `agent`, `system`)
  - `limit` (optional integer, default: 50, max: 200)
  - `offset` (optional integer, default: 0)
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "actor_type": "user",
    "actor_id": "uuid",
    "action": "setting_updated",
    "target_type": "system_settings",
    "target_id": "uuid",
    "details": {
      "key": "heartbeat_interval_seconds"
    },
    "created_at": "2026-10-13T20:00:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

