# Notifications API Contract

Base path: `/api/v1`

This contract covers in-app notifications for security events, incidents, and threat detections across the platform.

## FR Traceability
- FR-10.4: in-app notification on high/critical alert generation
- FR-15.1: notification delivery to dashboard top bar

## Authorization Matrix
- Administrator: full read and mark-as-read access
- Security Analyst: full read and mark-as-read access
- Viewer: full read and mark-as-read access
- Agent: no access

## Endpoints

### GET /notifications/

- Auth requirement: JWT required
- Authorization: All authenticated roles (`Administrator`, `Security Analyst`, `Viewer`)
- Query parameters:
  - `is_read` (optional boolean): filter by read status (`true` / `false`)
  - `limit` (optional integer, default: 50, max: 100)
  - `offset` (optional integer, default: 0)
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "user_id": "uuid | null",
    "alert_id": "uuid | null",
    "notification_type": "alert",
    "channel": "dashboard",
    "title": "Brute Force Attack Detected",
    "body": "5+ failed logins detected from IP 192.168.1.50",
    "is_read": false,
    "created_at": "2026-10-13T20:00:00Z",
    "updated_at": "2026-10-13T20:00:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`

### GET /notifications/unread-count

- Auth requirement: JWT required
- Authorization: All authenticated roles (`Administrator`, `Security Analyst`, `Viewer`)
- Request schema: none
- Response schema:

```json
{
  "unread_count": 3
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`

### PATCH /notifications/{id}/read

- Auth requirement: JWT required
- Authorization: All authenticated roles (`Administrator`, `Security Analyst`, `Viewer`)
- Request schema: none
- Response schema: Notification object (marked as `is_read: true`)
- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `404 Not Found`

### POST /notifications/mark-all-read

- Auth requirement: JWT required
- Authorization: All authenticated roles (`Administrator`, `Security Analyst`, `Viewer`)
- Request schema: none
- Response schema:

```json
{
  "message": "All notifications marked as read."
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`
