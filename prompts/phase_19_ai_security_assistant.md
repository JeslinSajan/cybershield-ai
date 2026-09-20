# Phase 19 — AI Security Assistant

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

> **STANDING RULE — VERIFY BEFORE EXECUTING**  
> This prompt was written before execution. Before running it:
> (1) Run `alembic current` — confirm which migrations are applied.
> (2) Check `backend/app/api/v1/` — note which endpoints already exist.
> (3) Check `tests/` — note which test files already exist.
> (4) If reality differs from this prompt's assumptions, update this file first, then execute.
> Prompts are a living plan, not a frozen snapshot.

---

## Prompt

**Scope:**
1. **Local Rule AI Implementation (backend/app/services/ai_service.py)**:
   - Create class `LocalRuleAI` implementing an `AIService` abstraction. This is NOT an LLM, and uses NO external API. Label in UI: 'Local Security Explanation Engine'.
   - `explain_alert(db, alert_id, org_id) -> str`: Build explanations using actual alert data (`alert_type`, `severity`, `description`, `device`, `source_ip`).
   - `explain_vulnerability(db, vuln_id, org_id) -> str`: Build using `cve_id`, `severity`, `affected_service`, `affected_version`, `summary`, `recommendation`.
   - `explain_risk_score(db, device_id, org_id) -> str`: Read `RiskScore.factor_breakdown`, `json.loads` it (since it's `Text`), and generate a string explanation using the exact values.
2. **Endpoints (in backend/app/api/v1/ai.py)**:
   - Role: **`get_current_analyst_or_admin` ONLY** (Viewer cannot use AI).
   - `POST /ai/explain-alert` (body: `{alert_id: uuid}`)
   - `POST /ai/explain-vulnerability` (body: `{vulnerability_id: uuid}`)
   - `POST /ai/explain-risk` (body: `{device_id: uuid}`)
   - `POST /ai/chat` (body: `{message: str, context_type: str, context_id: uuid}`). Maps to `explain_*` based on `context_type`.
3. **Chat History**:
   - Check `models/ai.py` for actual columns.
   - `AIConversation`: `organization_id`, `user_id`, `subject_type`, `subject_id`, `provider_type`='local_rule_ai'.
   - `AIMessage`: `conversation_id`, `role` ('user'/'assistant'), `content`, `created_at`.
   - Save chat histories correctly upon `POST /ai/chat`.

**Rules & Constraints:**
- Do NOT use OpenAI/Gemini or external APIs.
- Adhere to the error envelope format.
- RBAC must be exactly `get_current_analyst_or_admin`.

**Verification Checklist:**
- [ ] `curl` output showing an explanation for a Risk Score.
- [ ] `curl` output showing an explanation for an Alert.
