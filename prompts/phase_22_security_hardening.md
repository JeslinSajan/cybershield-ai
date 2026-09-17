# Phase 22 — Security Hardening

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 22: Security Hardening

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

Review the system as a security product and fix the most important 
security issues. This phase is about correctness, not perfection.

=======================================================================
CHECKLIST — DO ALL OF THESE
=======================================================================

1. INPUT VALIDATION
   - Every POST/PATCH endpoint must validate and reject unexpected 
     fields (use Pydantic models — already in place, just verify).
   - IP addresses in log/device endpoints must be validated as valid 
     IP format.
   - Text fields must have max length limits set in Pydantic schemas.

2. RATE LIMITING
   - Add rate limiting to POST /auth/login only.
   - Use slowapi (pip install slowapi): 10 requests per minute per IP.
   - Return 429 Too Many Requests if exceeded.
   - Add slowapi to requirements.txt.

3. SECURE HEADERS
   - Add these response headers to all API responses via FastAPI 
     middleware:
       X-Content-Type-Options: nosniff
       X-Frame-Options: DENY
       Referrer-Policy: strict-origin-when-cross-origin

4. CORS
   - Review CORS settings. Ensure CORS_ORIGINS in production is 
     set to only the Vercel frontend URL, not "*".
   - Confirm this is already set correctly in app/main.py.

5. ORGANIZATION ISOLATION
   - Audit every list endpoint (GET /devices/, GET /alerts/, etc.)
   - Confirm EVERY query filters by organization_id from 
     the logged-in user's token.
   - If any query is missing the org filter: add it.
   - This prevents one user seeing another organization's data.

6. ERROR MESSAGES
   - Confirm error responses never leak stack traces in production.
   - Set DEBUG=False in production .env.
   - The general exception handler in main.py should only return 
     "An unexpected error occurred" — never the raw exception message.

7. AUDIT LOG ENTRIES
   - Confirm these events are already writing to audit_logs table:
       User login / failed login
       Agent enrolled / revoked
       Scan started
       Alert status changed
       Report generated
   - If any are missing: add them.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Hit POST /auth/login 11 times rapidly — confirm 429 on the 11th.
2. Confirm API responses include X-Content-Type-Options header.
3. Create two organizations with users — confirm user A cannot see 
   user B's devices/alerts.
4. With DEBUG=False, trigger a 500 error — confirm no stack trace 
   in the response body.
5. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 22 — security hardening (rate limiting, headers, org isolation, audit)"
```
