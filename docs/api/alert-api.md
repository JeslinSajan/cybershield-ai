# Alert API Contract

Base path: `/api/v1`

This contract covers alert creation, investigation, and status transitions. It is derived from the `alerts` table and `alert_events` lifecycle tracking described in FR-12.1 through FR-12.3 and FR-16.1.

## FR Traceability
- FR-12.1: the alert record stores ID, timestamp, agent, device, type, severity, risk score, description, and status
- FR-12.2: Analyst or Administrator may transition an alert through Open -> Acknowledged -> Investigating -> Resolved or False Positive
- FR-12.3: status change timeline is maintained with actor and timestamp
- FR-16.1: alert lifecycle changes are auditable

## Authorization Matrix
- Administrator: read, investigate, and change state
- Security Analyst: read, investigate, and change state
- Viewer: read only
- Agent: not a user-facing endpoint; Agent emits alert evidence but does not manipulate alert state

## Common Error Envelope

```json
{
  "error": {
    "code": "INVALID_ALERT_TRANSITION",
    "message": "The requested status transition is not allowed.",
    "details": {
      "from_status": "Open",
      "to_status": "Resolved"
    }
  }
}
```

## Endpoints

### GET /alerts

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Query parameters: `status`, `severity`, `alert_type`, `device_id`, `agent_id`, `from`, `to`, `limit`, `offset`
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "agent_id": "uuid",
    "device_id": "uuid",
    "alert_type": "brute_force",
    "severity": "High",
    "status": "Open",
    "description": "6 failed logins from the same source within 10 minutes.",
    "risk_score": 74.5,
    "triggered_at": "2026-08-24T12:10:00Z",
    "created_at": "2026-08-24T12:10:00Z",
    "updated_at": "2026-08-24T12:10:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### GET /alerts/{alert_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema: a single alert object matching the `alerts` table fields
- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### GET /alerts/{alert_id}/timeline

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema:

```json
[
  {
    "id": "uuid",
    "alert_id": "uuid",
    "actor_user_id": "uuid",
    "from_status": "Open",
    "to_status": "Acknowledged",
    "reason": "Reviewed by analyst",
    "changed_at": "2026-08-24T12:15:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
- Notes: This is the human-readable audit trail of state transitions for the alert.

### PATCH /alerts/{alert_id}/status

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema:

```json
{
  "status": "Acknowledged",
  "reason": "Initial triage completed"
}
```

- Response schema:

```json
{
  "id": "uuid",
  "status": "Acknowledged",
  "updated_at": "2026-08-24T12:18:00Z"
}
```

- Success status: `200 OK`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`
- Notes: Valid transitions follow the allowed lifecycle and are recorded in `alert_events` with the user actor and timestamp.
