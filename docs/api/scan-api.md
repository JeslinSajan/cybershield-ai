# Scan API Contract

Base path: `/api/v1`

This contract covers the scan lifecycle initiated by a human user and coordinated with an online Agent. It maps directly to `scans`, `scan_results`, and the scanning logic in FR-5.1, FR-5.2, FR-6.1, FR-6.2, and FR-16.1.

## FR Traceability
- FR-5.1: authorized user triggers discovery or vulnerability scan
- FR-6.1: port scanning and service/version detection
- FR-6.2: vulnerability matching against local/cached CVE data
- FR-16.1: audit log for scan started/completed
- FR-17.1 and FR-17.3: dashboard uses scan results and recent activity

## Authorization Matrix
- Administrator: can start scans and view results
- Security Analyst: can start scans and view results
- Viewer: no write access, read-only if explicitly allowed by the application
- Agent: uses separate Agent credentials for task retrieval and status reporting; not a human user route

## Endpoints

### POST /scans

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema:

```json
{
  "agent_id": "uuid",
  "scan_type": "discovery",
  "target_scope": "192.168.1.0/24",
  "notes": "Authorized internal subnet assessment"
}
```

- Response schema:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "agent_id": "uuid",
  "created_by_user_id": "uuid",
  "scan_type": "discovery",
  "status": "PENDING",
  "target_scope": "192.168.1.0/24",
  "started_at": null,
  "completed_at": null,
  "created_at": "2026-08-24T12:00:00Z",
  "updated_at": "2026-08-24T12:00:00Z"
}
```

- Success status: `201 Created`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
- Notes: Before execution, the backend must validate the target is authorized and an online Agent is available. This is the user-visible start-scan action described in FR-5.1.

### GET /scans

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Query parameters: `status`, `agent_id`, `created_by_user_id`, `limit`, `offset`
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "agent_id": "uuid",
    "created_by_user_id": "uuid",
    "scan_type": "vulnerability",
    "status": "COMPLETED",
    "target_scope": "192.168.1.0/24",
    "started_at": "2026-08-24T12:05:00Z",
    "completed_at": "2026-08-24T12:20:00Z",
    "created_at": "2026-08-24T12:00:00Z",
    "updated_at": "2026-08-24T12:20:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### GET /scans/{scan_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema: a single scan object matching `scans`
- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### GET /scans/{scan_id}/results

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "scan_id": "uuid",
    "device_id": "uuid",
    "result_type": "services",
    "raw_payload": {
      "open_ports": [22, 80, 443],
      "services": [
        { "port": 22, "name": "ssh" },
        { "port": 80, "name": "http" }
      ]
    },
    "created_at": "2026-08-24T12:18:00Z",
    "updated_at": "2026-08-24T12:18:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
- Notes: This read endpoint supports evidence review and forensic traceability for scan results.

### PATCH /scans/{scan_id}/status

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema:

```json
{
  "status": "FAILED",
  "reason": "Agent unreachable"
}
```

- Response schema:

```json
{
  "id": "uuid",
  "status": "FAILED",
  "updated_at": "2026-08-24T12:24:00Z"
}
```

- Success status: `200 OK`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
- Notes: This is the backend-side status override path and is consistent with the `scans.status` model; actual Agent task reporting is handled in [agent-api.md](agent-api.md).
