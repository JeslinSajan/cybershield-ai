# Report API Contract

Base path: `/api/v1`

This contract covers report generation and delivery. It is derived from `reports`, the report-generation workflow in FR-14.1 and FR-14.2, and the audit requirement in FR-16.1.

## FR Traceability
- FR-14.1: generate PDF and/or CSV summaries for selected time periods
- FR-14.2: downloadable reports from the Reports view
- FR-16.1: report generation is auditable

## Authorization Matrix
- Administrator: can generate, view, and download reports
- Security Analyst: can generate, view, and download reports
- Viewer: can view and download reports if allowed by report access rules
- Agent: no access to human report generation endpoints

## Common Error Envelope

```json
{
  "error": {
    "code": "REPORT_GENERATION_FAILED",
    "message": "The report could not be generated for the requested time window.",
    "details": []
  }
}
```

## Endpoints

### GET /reports

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Query parameters: `report_type`, `period_start`, `period_end`, `status`, `limit`, `offset`
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "created_by_user_id": "uuid",
    "report_type": "summary",
    "period_start": "2026-08-01T00:00:00Z",
    "period_end": "2026-08-31T23:59:59Z",
    "file_name": "cybershield-summary-2026-08.csv",
    "mime_type": "text/csv",
    "status": "READY",
    "created_at": "2026-08-24T12:00:00Z",
    "updated_at": "2026-08-24T12:00:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### POST /reports/generate

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema:

```json
{
  "report_type": "summary",
  "period_start": "2026-08-01T00:00:00Z",
  "period_end": "2026-08-31T23:59:59Z",
  "mime_type": "application/pdf"
}
```

- Response schema:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "created_by_user_id": "uuid",
  "report_type": "summary",
  "period_start": "2026-08-01T00:00:00Z",
  "period_end": "2026-08-31T23:59:59Z",
  "file_name": "cybershield-summary-2026-08.pdf",
  "mime_type": "application/pdf",
  "status": "GENERATING",
  "created_at": "2026-08-24T12:00:00Z",
  "updated_at": "2026-08-24T12:00:00Z"
}
```

- Success status: `201 Created`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`
- Notes: This is the report-generation trigger. The actual file may be available once background processing completes.

### GET /reports/{report_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema: the full report metadata object for the selected row in `reports`
- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### GET /reports/{report_id}/download

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst, Viewer
- Request schema: none
- Response schema: binary file payload (PDF or CSV)
- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`
- Notes: The response content type should match the stored `mime_type` and the file should be named as stored in `file_name`.
