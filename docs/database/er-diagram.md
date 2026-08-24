# ER Diagram

This diagram shows the MVP database relationship model required by the corrected SRS and architecture documents. It is intentionally scoped to the local-first pipeline: Agent registration and heartbeats, device discovery, vulnerability scanning, logs, threat detection, alerts, risk scoring, local AI explanations, reports, audit, and notification data.

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : has
    ORGANIZATION ||--o{ AGENT : owns
    ORGANIZATION ||--o{ DEVICE : owns
    ORGANIZATION ||--o{ SCAN : owns
    ORGANIZATION ||--o{ LOG : owns
    ORGANIZATION ||--o{ ALERT : owns
    ORGANIZATION ||--o{ THREAT_INDICATOR : owns
    ORGANIZATION ||--o{ REPORT : owns
    ORGANIZATION ||--o{ AI_CONVERSATION : owns
    ORGANIZATION ||--o{ NOTIFICATION : owns
    ORGANIZATION ||--o{ AUDIT_LOG : owns
    ORGANIZATION ||--o{ SYSTEM_SETTING : owns

    ROLE ||--o{ USER : assigns
    ROLE ||--o{ ROLE_PERMISSION : grants
    PERMISSION ||--o{ ROLE_PERMISSION : maps

    AGENT ||--o{ AGENT_CREDENTIAL : has
    AGENT ||--o{ AGENT_HEARTBEAT : emits
    AGENT ||--o{ SCAN : runs
    AGENT ||--o{ LOG : emits
    AGENT ||--o{ ALERT : emits
    AGENT ||--o{ DEVICE : discovered_by

    DEVICE ||--o{ DEVICE_INTERFACE : has
    DEVICE ||--o{ SCAN_RESULT : yields
    DEVICE ||--o{ VULNERABILITY : found_on
    DEVICE ||--o{ LOG : source
    DEVICE ||--o{ ALERT : affects
    DEVICE ||--o{ RISK_SCORE : applies_to

    SCAN ||--o{ SCAN_RESULT : contains
    SCAN ||--o{ REPORT : summarizes

    SCAN_RESULT ||--o{ VULNERABILITY : produces
    CVE ||--o{ VULNERABILITY : references

    ALERT ||--o{ ALERT_EVENT : changes
    ALERT ||--o{ NOTIFICATION : triggers
    ALERT ||--o{ RISK_SCORE : scores

    USER ||--o{ REPORT : creates
    USER ||--o{ AUDIT_LOG : acts_on
    USER ||--o{ AI_CONVERSATION : starts
    USER ||--o{ NOTIFICATION : receives

    AI_CONVERSATION ||--o{ AI_MESSAGE : contains
```

## Notes

- Organizations are explicit even for a single-organization MVP so future multi-organization isolation is not retrofitted later.
- Agent credentials are stored in a separate table from user accounts. This matches the Agent security model from the SRS and architecture docs.
- Risk scoring is intentionally represented as both a final score and a score-factor payload instead of a black-box integer only.
- AI conversations and messages are provider-agnostic; they do not assume a specific external LLM or cloud AI service.
