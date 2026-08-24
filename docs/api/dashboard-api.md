# Dashboard API Contract

Base path: `/api/v1`

This contract covers the summary data required by the dashboard, derived from FR-17.1 through FR-17.3. It is intentionally read-only and does not create new business entities.

## FR Traceability
- FR-17.1: summary cards for online agents, online devices, critical vulnerabilities, open alerts, average risk score
- FR-17.2: charts for alert trend, vulnerability severity distribution, and risk trend over time
- FR-17.3: recent activity feed with device discovery, vulnerability findings, alert generation, agent heartbeat, and scan completion

## Authorization Matrix
- Administrator: read
- Security Analyst: read
- Viewer: read
- Agent: no access

## Endpoints

### GET /dashboard/summary

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema:

```json
{
  "online_agents": 3,
  "online_devices": 27,
  "critical_vulnerabilities": 6,
  "open_alerts": 2,
  "average_risk_score": 41.7
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### GET /dashboard/charts

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Query parameters: `period_days`, `granularity`
- Response schema:

```json
{
  "alert_trend": [
    { "date": "2026-08-01", "count": 2 },
    { "date": "2026-08-02", "count": 5 }
  ],
  "vulnerability_severity_distribution": {
    "Low": 3,
    "Medium": 8,
    "High": 4,
    "Critical": 2
  },
  "risk_trend": [
    { "date": "2026-08-01", "score": 35.0 },
    { "date": "2026-08-02", "score": 42.2 }
  ]
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `400 Bad Request`

### GET /dashboard/activity

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Query parameters: `limit`, `offset`
- Response schema:

```json
[
  {
    "event_type": "device_discovered",
    "message": "New device 192.168.1.44 discovered by agent 784f5b",
    "timestamp": "2026-08-24T12:45:00Z"
  },
  {
    "event_type": "alert_generated",
    "message": "High-severity brute-force alert triggered",
    "timestamp": "2026-08-24T12:10:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`
