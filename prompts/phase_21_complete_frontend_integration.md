# Phase 21 — Complete Frontend Integration

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 21: Complete Frontend Integration

Repo: https://github.com/JeslinSajan/cybershield-ai

=======================================================================
WHAT TO BUILD
=======================================================================

Build the complete React frontend (TypeScript + Vite + Tailwind CSS) 
and connect every page to the real backend API.
This is the visible part of your project — make it look good for demo.

=======================================================================
PAGES TO BUILD
=======================================================================

1. LOGIN PAGE
   - Email + password form.
   - POST /api/v1/auth/login.
   - Store JWT in localStorage.
   - Redirect to Dashboard on success.

2. DASHBOARD
   - Summary cards (from GET /alerts/summary + GET /agents/):
       "Online Agents", "Discovered Devices", "Open Alerts", 
       "Critical Vulnerabilities", "Avg Risk Score"
   - Recent alerts table (last 5 from GET /alerts/).
   - Agent status list (GET /agents/).

3. AGENTS PAGE
   - List all agents with status badge (ONLINE = green, 
     OFFLINE = red, PENDING = yellow).
   - Click an agent → see details + last heartbeat + health stats.
   - "Generate Enrollment Token" button (Admin only).
   - "Revoke Agent" button (Admin only).

4. DEVICES PAGE
   - List all discovered devices.
   - Show: IP, hostname, MAC, status, last seen.
   - Click a device → see details + vulnerabilities + risk score.
   - "Run Discovery Scan" button (Admin/Analyst — shows auth notice 
     before starting: "Only scan networks you are authorized to test").

5. VULNERABILITIES PAGE
   - List all vulnerabilities grouped by severity.
   - Filter by: severity, device, CVE ID.
   - Click a vulnerability → full detail + AI explanation button.

6. ALERTS PAGE
   - List all alerts with status filter tabs: All / Open / 
     Acknowledged / Investigating / Resolved.
   - Click an alert → detail view with:
       - Alert info (type, severity, source IP, description)
       - Status change buttons (Acknowledge / Investigate / Resolve)
       - Alert history timeline
       - "Explain with AI" button

7. LOGS PAGE
   - Table of recent security logs.
   - Filter by: event_type, source, date range.

8. THREAT INTELLIGENCE PAGE
   - List of known bad indicators.
   - Add new indicator form (Admin/Analyst).
   - Delete indicator (Admin only).

9. REPORTS PAGE
   - List of generated reports.
   - "Generate Report" button with type selector.
   - Download PDF / CSV buttons.

10. AI ASSISTANT PAGE (Admin/Analyst only — Viewer sees 403)
    - Simple chat-style interface.
    - User types a question or selects a context item.
    - Shows AI explanation from POST /ai/chat.
    - Clearly labeled: "Local Security Explanation Engine"
    - Do NOT show this page/menu to Viewers.

11. SETTINGS PAGE (Admin only)
    - User management: list users, create user, change role, 
      deactivate user.
    - System settings: GET/PUT /api/v1/settings/ 
      (build these backend endpoints in this phase if not yet done)
      Keys to expose in UI: heartbeat_interval, scan_timeout,
      agent_offline_timeout_seconds.

12. AUDIT LOGS PAGE (Admin only)
    - GET /api/v1/audit-logs/ (Administrator only — Viewer/Analyst get 403)
    - Shows: action, actor, target, timestamp
    - Filter by: action type, date range
    - Implement this backend endpoint now if not yet done.

13. NOTIFICATIONS (all roles)
    - A bell icon in the top navigation bar.
    - GET /api/v1/notifications/ — returns unread notifications 
      for the logged-in user from the notifications table (schema table 23).
    - Mark as read: PATCH /api/v1/notifications/{id}/read
    - When a High or Critical alert is created (Phase 15), create a 
      notification row for each user in the organization:
        notification_type = "alert", channel = "dashboard",
        title = "New <severity> Alert: <alert_type>",
        body = <alert description>, is_read = False
    - Show unread count as a badge on the bell icon.
    - Implement both the backend endpoints and the frontend component.

=======================================================================
TECH REQUIREMENTS
=======================================================================

- React + TypeScript + Vite + Tailwind CSS
- Use axios or fetch for API calls.
- Store JWT in localStorage, send as: Authorization: Bearer <token>
- Role-based UI: hide buttons/pages based on user role from /auth/me.
- Show loading states and error messages on all API calls.
- Responsive design — must work on laptop screen (1280px+).

Make the UI look professional. Use a dark or dark/light theme.
Use Tailwind components consistently. This is what your examiner sees.

=======================================================================
API BASE URL
=======================================================================

Read from: VITE_API_BASE_URL in frontend/.env
Default for local dev: http://localhost:8000
Production: https://cybershield-ai-xnn7.onrender.com

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Login works end-to-end (real JWT, not mock).
2. Dashboard shows real data from the backend.
3. Run a scan from the UI — confirm it dispatches to the agent.
4. Change an alert status from the UI — confirm it updates.
5. Download a PDF report from the UI.
6. AI Explain button returns a real explanation.
7. Viewer role cannot see Admin buttons.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat(frontend): Phase 21 — complete frontend with all pages connected to real API"
```
