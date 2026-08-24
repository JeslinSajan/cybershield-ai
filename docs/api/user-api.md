# User API Contract

Base path: `/api/v1`

This contract covers human-user administration and role assignment. It maps to `users` and `roles` in the MVP schema and to FR-2.1 through FR-2.3 and FR-3.1 to FR-3.3.

## FR Traceability
- FR-2.1: Administrator manages users
- FR-2.2: Administrator assigns roles
- FR-2.3: protect the sole remaining Administrator from self-demotion or deletion
- FR-3.1: default deny and RBAC enforcement
- FR-3.2: Viewer cannot write
- FR-3.3: Security Analyst cannot manage users

## Authorization Matrix
- Administrator: create, list, read, update, deactivate
- Security Analyst: no user-management access
- Viewer: no user-management access
- Agent: not permitted

## Common Response Envelope

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You are not allowed to perform this action.",
    "details": []
  }
}
```

## Endpoints

### GET /users

- Auth requirement: JWT required
- Authorization: Administrator only
- Request schema: none
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "role_id": "uuid",
    "email": "user@example.com",
    "username": "analyst01",
    "is_active": true,
    "failed_login_count": 0,
    "last_login_at": "2026-08-24T12:00:00Z",
    "created_at": "2026-08-24T10:00:00Z",
    "updated_at": "2026-08-24T12:00:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### POST /users

- Auth requirement: JWT required
- Authorization: Administrator only
- Request schema:

```json
{
  "organization_id": "uuid",
  "email": "new.user@example.com",
  "username": "newuser",
  "password": "StrongPass!123",
  "role_id": "uuid"
}
```

- Response schema:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "role_id": "uuid",
  "email": "new.user@example.com",
  "username": "newuser",
  "is_active": true,
  "created_at": "2026-08-24T14:00:00Z",
  "updated_at": "2026-08-24T14:00:00Z"
}
```

- Success status: `201 Created`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `409 Conflict`
- Notes: `users.password_hash` is stored as bcrypt hash only; plaintext password is never returned.

### GET /users/{user_id}

- Auth requirement: JWT required
- Authorization: Administrator only
- Request schema: none
- Response schema: single user object matching the `users` table fields above
- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### PATCH /users/{user_id}

- Auth requirement: JWT required
- Authorization: Administrator only
- Request schema:

```json
{
  "email": "updated.user@example.com",
  "username": "updateduser",
  "role_id": "uuid",
  "is_active": true
}
```

- Response schema: updated user object
- Success status: `200 OK`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`
- Notes: The service must reject any change that would leave the system without an Administrator or that violates the self-protection rule in FR-2.3.

### POST /users/{user_id}/deactivate

- Auth requirement: JWT required
- Authorization: Administrator only
- Request schema: none
- Response schema:

```json
{
  "id": "uuid",
  "is_active": false,
  "updated_at": "2026-08-24T15:00:00Z"
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`
- Notes: The MVP uses soft-deactivate semantics (`is_active = false` / `deleted_at` when applicable), not a hard delete.
