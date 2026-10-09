# Risk Score API Contract

Base path: `/api/v1`

This contract covers dynamic risk quantification and asset exposure scoring for discovered network devices. It is derived from the `risk_scores` table, dynamic calculation engine, and lifecycle triggers described in FR-13.1 through FR-13.3 and Phase 17.

## FR Traceability
- FR-13.1: Deterministic risk quantification combining vulnerabilities, active alerts, and network exposure.
- FR-13.2: Formula specification v1:
  - Vulnerability component:
    - Critical severity CVE: +30 (subtotal capped at 30)
    - High severity CVE: +15 (subtotal capped at 30)
    - Medium severity CVE: +5 (subtotal capped at 15)
    - Low severity CVE: +2 (subtotal capped at 5)
    - Maximum vulnerability component: 80.0
  - Alert component:
    - Active (Open) Brute Force alert: +20
    - Active (Open) Suspicious Login alert: +15
    - Active (Open) Port Scan alert: +10
  - Exposure component:
    - &ge; 10 open ports in the device's latest scan result: +10 (otherwise 0)
  - Aggregation:
    - Total score = min(100.0, vulnerability_score + alert_score + exposure_score)
  - Risk Bands:
    - 0 – 24: Low
    - 25 – 49: Medium
    - 50 – 74: High
    - 75 – 100: Critical
- FR-13.3: Storage format:
  - `RiskScore.factor_breakdown` is persisted as a JSON string in `Column(Text)` for explainability.
  - Open alerts with unassigned risk scores on the device are backfilled.

## Authorization Matrix
- Administrator: Read all risk scores (`get_any_authenticated_user`).
- Security Analyst: Read all risk scores (`get_any_authenticated_user`).
- Viewer: Read all risk scores (`get_any_authenticated_user`).
- Agent: Does not query risk scores directly; reports scans and logs that trigger recalculation.

---

## Endpoints

### GET /devices/{device_id}/risk

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer (`get_any_authenticated_user`)
- Request schema: none
- Path parameters:
  - `device_id` (UUID): ID of target device in caller's organization.
- Response schema:

```json
{
  "id": "c6204c6a-c454-46f9-aa2f-376046e7f226",
  "organization_id": "8bb38f28-2b81-4fe6-a9ea-72216503c2ff",
  "entity_type": "device",
  "entity_id": "97e7482d-1eb9-40cb-ba14-1e5b88ab8972",
  "device_id": "97e7482d-1eb9-40cb-ba14-1e5b88ab8972",
  "score": 65.0,
  "risk_band": "High",
  "factor_breakdown": {
    "vulnerabilities": {
      "critical_count": 1,
      "critical_score": 30.0,
      "high_count": 1,
      "high_score": 15.0,
      "medium_count": 0,
      "medium_score": 0.0,
      "low_count": 0,
      "low_score": 0.0,
      "subtotal": 45.0
    },
    "alerts": {
      "brute_force_count": 1,
      "brute_force_score": 20.0,
      "suspicious_login_count": 0,
      "suspicious_login_score": 0.0,
      "port_scan_count": 0,
      "port_scan_score": 0.0,
      "subtotal": 20.0
    },
    "exposure": {
      "open_ports_count": 4,
      "exposure_score": 0.0
    },
    "raw_total": 65.0,
    "total_score": 65.0,
    "risk_band": "High",
    "formula_version": "v1"
  },
  "formula_version": "v1",
  "created_at": "2026-10-09T18:00:00Z",
  "updated_at": "2026-10-09T18:05:00Z"
}
```

- Success status: `200 OK`
- Error statuses:
  - `401 Unauthorized`: Missing or invalid token.
  - `404 Not Found`: Device not found or does not belong to caller's organization.

---

### GET /risk-scores/

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer (`get_any_authenticated_user`)
- Query parameters:
  - `risk_band` (string, optional): Filter by risk band (`Critical`, `High`, `Medium`, `Low`).
  - `limit` (integer, default 50, min 1, max 200): Pagination limit.
  - `offset` (integer, default 0, min 0): Pagination offset.
- Response schema: Array of device risk objects, ordered by `score` descending.

```json
[
  {
    "id": "c6204c6a-c454-46f9-aa2f-376046e7f226",
    "device_id": "97e7482d-1eb9-40cb-ba14-1e5b88ab8972",
    "device_ip": "192.168.1.100",
    "device_hostname": "core-db-server",
    "device_type": "server",
    "organization_id": "8bb38f28-2b81-4fe6-a9ea-72216503c2ff",
    "score": 65.0,
    "risk_band": "High",
    "factor_breakdown": {
      "vulnerabilities": { ... },
      "alerts": { ... },
      "exposure": { ... },
      "total_score": 65.0,
      "risk_band": "High",
      "formula_version": "v1"
    },
    "formula_version": "v1",
    "created_at": "2026-10-09T18:00:00Z",
    "updated_at": "2026-10-09T18:05:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses:
  - `401 Unauthorized`: Missing or invalid token.

---

## Recalculation Triggers
Risk calculation is triggered automatically upon:
1. Vulnerability ingestion: when new vulnerabilities are added for a device in `vulnerability_service.py`.
2. Alert generation: when an alert linked to a device is generated in `detection_service.py`.
3. Alert triage status change: when an alert transitions to `Resolved` or `False Positive` in `alerts.py`.
