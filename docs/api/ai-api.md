# AI API Contract

Base path: `/api/v1`

This contract documents the Local Security Explanation Engine and its provider-agnostic `AIService` abstraction. It traces to FR-13.1 through FR-13.4 and to the backend architecture requirement that the provider must remain generic and not imply a specific external AI vendor.

## FR Traceability
- FR-13.1: chat-style explanation interface for alert, vulnerability, or risk score
- FR-13.2: LocalRuleAI explains using deterministic templates tied to underlying data
- FR-13.3: UI label is Local Security Explanation Engine, not a generic AI label
- FR-13.4: AIService is provider-agnostic and future implementations are allowed behind the interface

## Authorization Matrix
- Administrator: may use the AI explanation interface
- Security Analyst: may use the AI explanation interface
- Viewer: may not use the AI assistant
- Agent: not allowed; Agent endpoints are separate and do not expose user-facing AI functions

## Common Error Envelope

```json
{
  "error": {
    "code": "AI_EXPLANATION_UNAVAILABLE",
    "message": "An explanation could not be generated for the selected record.",
    "details": []
  }
}
```

## Endpoints

### POST /ai/explain

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema:

```json
{
  "subject_type": "alert",
  "subject_id": "uuid",
  "user_prompt": "Why is this alert high risk?"
}
```

- Response schema:

```json
{
  "conversation_id": "uuid",
  "subject_type": "alert",
  "subject_id": "uuid",
  "provider_type": "local_rule_ai",
  "messages": [
    {
      "role": "user",
      "content": "Why is this alert high risk?"
    },
    {
      "role": "assistant",
      "content": "This alert is high risk because the device shows 6 failed logins from a single source and a matching port-scan signature. The risk formula weights failed logins and suspicious activity heavily."
    }
  ],
  "created_at": "2026-08-24T12:25:00Z"
}
```

- Success status: `200 OK`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity`
- Notes: The provider is intentionally generic (`provider_type`) and not tied to a specific external AI vendor. The concrete implementation remains `LocalRuleAI` in the MVP.

### GET /ai/conversations

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema: none
- Response schema:

```json
[
  {
    "id": "uuid",
    "organization_id": "uuid",
    "user_id": "uuid",
    "subject_type": "vulnerability",
    "subject_id": "uuid",
    "provider_type": "local_rule_ai",
    "created_at": "2026-08-24T12:20:00Z"
  }
]
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`

### GET /ai/conversations/{conversation_id}

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema: none
- Response schema:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "user_id": "uuid",
  "subject_type": "alert",
  "subject_id": "uuid",
  "provider_type": "local_rule_ai",
  "messages": [
    {
      "role": "user",
      "content": "Explain alert 123"
    },
    {
      "role": "assistant",
      "content": "This alert is high risk because ..."
    }
  ]
}
```

- Success status: `200 OK`
- Error statuses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### POST /ai/explain/risk

- Auth requirement: JWT required
- Authorization: Administrator, Security Analyst
- Request schema:

```json
{
  "risk_score": 82.5,
  "factors": {
    "vulnerability_severity": "High",
    "failed_logins": 6,
    "threat_indicator_match": true
  }
}
```

- Response schema:

```json
{
  "provider_type": "local_rule_ai",
  "explanation": "This device's risk score is 82.5 because it combines a high-severity vulnerability with multiple failed logins and a threat-indicator match."
}
```

- Success status: `200 OK`
- Error statuses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`
- Notes: This is a focused explanation endpoint for risk scoring, justified by FR-11.1 and FR-13.1; it does not imply an external provider.
