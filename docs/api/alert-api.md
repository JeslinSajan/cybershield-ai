# Alert API Contract

Base path: `/api/v1`

This contract covers alert retrieval, investigation, summary statistics, and status transitions. It is derived from the `alerts` table and `alert_events` lifecycle tracking described in FR-12.1 through FR-12.3 and FR-16.1.

## FR Traceability
- FR-12.1: The alert record stores ID, timestamp, agent, device, type, severity, risk score, description, and status.
- FR-12.2: Analyst or Administrator may transition an alert through:
  - Open → Acknowledged, Investigating, False Positive
  - Acknowledged → Investigating, Resolved, False Positive
  - Investigating → Resolved, False Positive
- FR-12.3: Status change timeline is maintained in `alert_events` with actor user ID, previous status, new status, reason, and timestamp.
- FR-16.1: Alert lifecycle transitions are auditable and generate an `AuditLog` entry (`action='alert_status_changed'`).

## Authorization Matrix
- Administrator: Read, investigate, and change state (`PATCH /alerts/{alert_id}`).
- Security Analyst: Read, investigate, and change state (`PATCH /alerts/{alert_id}`).
- Viewer: Read only (`GET` endpoints). `PATCH /alerts/{alert_id}` returns `403 Forbidden` (`FORBIDDEN`).
- Agent: Emits telemetry/evidence; does not manage alert triage state.

## Common Error Envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid status transition from 'Open' to 'Resolved'.",
    "details": []
  }
}
```

Standard error codes:
- `NOT_AUTHENTICATED` (HTTP 401): Missing or expired JWT.
- `FORBIDDEN` (HTTP 403): User lacks required role permissions.
- `NOT_FOUND` (HTTP 404): Specified alert does not exist in the caller's organization.
- `VALIDATION_ERROR` (HTTP 400): Disallowed transition or unrecognized status value.

---

## Endpoints

### GET /alerts/summary

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer (`get_any_authenticated_user`)
- Request schema: none
- Response schema:

```json
{
  "open": 5,
  "acknowledged": 2,
  "investigating": 1,
  "resolved": 12,
  "false_positive": 3,
  "critical": 1,
  "high": 4,
  "medium": 8,
  "low": 10
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`

---

### GET /alerts/

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer (`get_any_authenticated_user`)
- Query parameters:
  - `status` (string, optional): Filter by status (e.g. `open`, `acknowledged`, `false_positive`).
  - `severity` (string, optional): Filter by severity (e.g. `critical`, `high`, `medium`, `low`).
  - `alert_type` (string, optional): Filter by detection rule / alert type (`brute_force`, `port_scan`, `suspicious_login`, `malware_indicator`).
  - `limit` (integer, default 50, min 1, max 200): Maximum results to return.
  - `offset` (integer, default 0, min 0): Number of results to skip.
- Response schema:

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "agent_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "device_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "alert_type": "brute_force",
    "severity": "High",
    "status": "Open",
    "description": "5 failed login attempts detected from IP 192.168.1.100 within 10 minutes.",
    "risk_score": 40.0,
    "triggered_at": "2026-10-09T12:00:00Z",
    "created_at": "2026-10-09T12:00:00Z",
    "updated_at": "2026-10-09T12:00:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`

---

### GET /alerts/{alert_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer (`get_any_authenticated_user`)
- Request schema: none
- Response schema:

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "agent_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "device_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "alert_type": "brute_force",
  "severity": "High",
  "status": "Acknowledged",
  "description": "5 failed login attempts detected from IP 192.168.1.100 within 10 minutes.",
  "risk_score": 40.0,
  "triggered_at": "2026-10-09T12:00:00Z",
  "created_at": "2026-10-09T12:00:00Z",
  "updated_at": "2026-10-09T12:05:00Z",
  "history": [
    {
      "id": "e4f8d67a-1122-3344-5566-778899aabbcc",
      "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "alert_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "actor_user_id": "77bb3322-9988-4433-2211-001122334455",
      "from_status": "Open",
      "to_status": "Acknowledged",
      "reason": "SOC triage in progress",
      "changed_at": "2026-10-09T12:05:00Z"
    }
  ]
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `404 Not Found`

---

### GET /alerts/{alert_id}/history

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer (`get_any_authenticated_user`)
- Request schema: none
- Response schema:

```json
[
  {
    "id": "e4f8d67a-1122-3344-5566-778899aabbcc",
    "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "alert_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "actor_user_id": "77bb3322-9988-4433-2211-001122334455",
    "from_status": "Open",
    "to_status": "Acknowledged",
    "reason": "SOC triage in progress",
    "changed_at": "2026-10-09T12:05:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `404 Not Found`

---

### PATCH /alerts/{alert_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst (`get_current_analyst_or_admin`)
- Request schema:

```json
{
  "status": "Acknowledged",
  "reason": "Investigation initiated by SOC analyst."
}
```

- Allowed status transitions:
  - `Open` → `Acknowledged`, `Investigating`, `False Positive`
  - `Acknowledged` → `Investigating`, `Resolved`, `False Positive`
  - `Investigating` → `Resolved`, `False Positive`

- Response schema:

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "Acknowledged",
  "from_status": "Open",
  "reason": "Investigation initiated by SOC analyst.",
  "updated_at": "2026-10-09T12:05:00Z"
}
```

- Success status: `200 OK`
- Error statuses:
  - `400 Bad Request` (`VALIDATION_ERROR`): Invalid transition or unrecognized status value.
  - `401 Unauthorized` (`NOT_AUTHENTICATED`): Missing or invalid token.
  - `403 Forbidden` (`FORBIDDEN`): Viewer role attempted status transition.
  - `404 Not Found` (`NOT_FOUND`): Alert ID not found in organization.
- Side effects:
  - Inserts row into `alert_events` with transition actor and reason.
  - Inserts row into `audit_logs` with action `alert_status_changed`.
