# Authentication API Contract

Base path: `/api/v1`

This contract covers the human login/logout flow only. It is intentionally narrow and aligns to the corrected SRS and schema: the user account model is in `users`, the JWT requirement is in FR-1.3, and password hashing is required in FR-1.2.

## FR Traceability
- FR-1.1: user login with email/username and password
- FR-1.2: bcrypt password hashing, no plaintext password storage or logging
- FR-1.3: JWT issuance and validation
- FR-1.4: logout/invalidate client token
- FR-1.5: lock/throttle policy after repeated failures

## Common Conventions
- Human auth uses a JWT bearer token.
- Agent auth is not handled here; Agent-only routes are defined in [agent-api.md](agent-api.md).
- Default authorization is deny.
- Errors use a consistent envelope:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "The provided credentials are invalid.",
    "details": []
  }
}
```

## Endpoints

### POST /auth/login

- Auth requirement: none
- Authorization: public endpoint; no role required
- Request schema:

```json
{
  "email": "user@example.com",
  "password": "StrongPass!123"
}
```

- Response schema:

```json
{
  "user": {
    "id": "uuid",
    "organization_id": "uuid",
    "role_id": "uuid",
    "email": "user@example.com",
    "username": "analyst01",
    "is_active": true,
    "last_login_at": "2026-08-24T12:00:00Z"
  },
  "token": "jwt"
}
```

- Success status: `200 OK`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `423 Locked`, `429 Too Many Requests`
- Notes: On success, a JWT must be issued. Passwords are never returned; stored value is `users.password_hash` only.

### POST /auth/logout

- Auth requirement: JWT required
- Authorization: any authenticated human user
- Request schema: none
- Response schema: none (empty body or `204 No Content`)
- Success status: `204 No Content`
- Error statuses: `401 Unauthorized`
- Notes: The implementation may invalidate a client-side token and optionally enforce a server-side denylist.

### GET /auth/me

- Auth requirement: JWT required
- Authorization: any authenticated human user
- Request schema: none
- Response schema:

```json
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
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`
- Notes: This route is used for current identity lookup and is not a user-management endpoint.
