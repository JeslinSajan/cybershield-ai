# Device API Contract

Base path: `/api/v1`

This contract documents the device inventory and network identity model. It traces to the `devices` table and the discovery workflow in FR-5.2 and FR-5.3.

## FR Traceability
- FR-5.2: discovery data includes IP, MAC, hostname, vendor, open ports, services
- FR-5.3: device list view with status and last-seen
- FR-7.1: interface statistics may attach to a device
- FR-17.1: summary cards include online devices
- FR-17.3: recent activity feed includes device discovery

## Authorization Matrix
- Administrator: read and trigger discovery/scan actions
- Security Analyst: read and trigger discovery/scan actions
- Viewer: read only
- Agent: not used for device CRUD; only the scan workflow is Agent-driven

## Endpoints

### GET /devices

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Query parameters: `status`, `organization_id`, `agent_id`, `limit`, `offset`
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "agent_id": "uuid",
    "ip_address": "192.168.1.44",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "hostname": "workstation-4",
    "vendor": "Dell",
    "device_type": "workstation",
    "status": "online",
    "last_seen_at": "2026-08-24T12:45:00Z",
    "created_at": "2026-08-24T11:00:00Z",
    "updated_at": "2026-08-24T12:45:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### GET /devices/{device_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema: a single device object with the same fields as `devices`
- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### GET /devices/{device_id}/interfaces

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema:

```json
[
  {
    "id": "uuid",
    "device_id": "uuid",
    "organization_id": "uuid",
    "name": "eth0",
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.1.44",
    "bytes_sent": 123456,
    "bytes_received": 654321,
    "created_at": "2026-08-24T11:05:00Z",
    "updated_at": "2026-08-24T11:05:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
- Notes: This is a read-only view of the `device_interfaces` table and supports network telemetry and recent activity review.

### GET /devices/{device_id}/vulnerabilities

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema:

```json
[
  {
    "id": "uuid",
    "device_id": "uuid",
    "severity": "High",
    "summary": "OpenSSH vulnerability",
    "recommendation": "Upgrade to 9.0 or later"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
- Notes: This route is a convenience read exposure for a device's vulnerability findings; it is consistent with the `vulnerabilities` table and report-generation needs.
