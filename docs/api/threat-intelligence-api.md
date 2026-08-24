# Threat Intelligence API Contract

Base path: `/api/v1`

This contract covers local threat-indicator lookup and alert linkage. It maps to the `threat_indicators` table and to FR-9.4, FR-10.1, and FR-10.2.

## FR Traceability
- FR-9.4: malware indicator alert generation when observed data matches a stored threat indicator
- FR-10.1: the system maintains a local table of threat indicators (IP, domain, hash)
- FR-10.2: Administrators and Analysts can search indicators and view which alerts referenced them

## Authorization Matrix
- Administrator: full read and management access
- Security Analyst: read and search access
- Viewer: read-only access
- Agent: no access to human indicator management routes

## Endpoints

### GET /threat-intelligence

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Query parameters: `indicator_type`, `value`, `source`, `limit`, `offset`
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "indicator_type": "ip",
    "value": "203.0.113.44",
    "description": "Known malicious scanning host",
    "source": "local",
    "created_at": "2026-08-24T12:00:00Z",
    "updated_at": "2026-08-24T12:00:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### GET /threat-intelligence/{indicator_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "indicator_type": "hash",
  "value": "abc123...",
  "description": "Known malware sample hash",
  "source": "local",
  "created_at": "2026-08-24T12:00:00Z",
  "updated_at": "2026-08-24T12:00:00Z"
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### POST /threat-intelligence

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema:

```json
{
  "indicator_type": "domain",
  "value": "malware.example",
  "description": "Known phishing domain",
  "source": "local"
}
```

- Response schema:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "indicator_type": "domain",
  "value": "malware.example",
  "description": "Known phishing domain",
  "source": "local",
  "created_at": "2026-08-24T12:02:00Z",
  "updated_at": "2026-08-24T12:02:00Z"
}
```

- Success status: `201 Created`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`
- Notes: This is the management path for local indicators and is intentionally limited to the local indicator table.
