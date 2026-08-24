# Log API Contract

Base path: `/api/v1`

This contract covers normalized log review and filtering. It traces directly to the `logs` table and FR-8.1 through FR-8.3, plus the alert correlation rules in FR-9.1 and FR-9.2.

## FR Traceability
- FR-8.1: authorized SSH/auth and syslog collection
- FR-8.2: normalized log schema (timestamp, agent_id, device_id, source, event_type, severity, message, source_ip, username)
- FR-8.3: filtering by time, severity, source, and text search
- FR-9.1, FR-9.2: logs feed detection logic for brute-force and port-scan events

## Authorization Matrix
- Administrator: read
- Security Analyst: read
- Viewer: read only (subject to settings if restrictions are configured)
- Agent: uploads logs via Agent endpoints only; does not access the human log explorer

## Common Error Envelope

```json
{
  "error": {
    "code": "LOG_QUERY_INVALID",
    "message": "The requested log query parameters are invalid.",
    "details": []
  }
}
```

## Endpoints

### GET /logs

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Query parameters: `start_time`, `end_time`, `severity`, `source`, `event_type`, `device_id`, `agent_id`, `search`, `limit`, `offset`
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "agent_id": "uuid",
    "device_id": "uuid",
    "source": "auth.log",
    "event_type": "ssh_login",
    "severity": "warning",
    "message": "Failed password for invalid user admin from 192.168.1.25 port 22",
    "source_ip": "192.168.1.25",
    "username": "admin",
    "timestamp": "2026-08-24T12:05:00Z",
    "created_at": "2026-08-24T12:05:00Z",
    "updated_at": "2026-08-24T12:05:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`
- Notes: This is the Log Explorer listing endpoint and supports the filter set described in FR-8.3.

### GET /logs/{log_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema: a single log object matching the `logs` table structure
- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
