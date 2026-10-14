"""
Generate the CyberShield AI Operational Workflow & Incident Runbook PDF.
Saves to docs/CyberShield_AI_Operational_Runbook.pdf.
"""
import os
from fpdf import FPDF

class CyberShieldPDF(FPDF):
    def header(self):
        # Header banner
        self.set_fill_color(15, 23, 42) # Slate-900
        self.rect(0, 0, 210, 24, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(12, 7)
        self.cell(0, 8, "CYBERSHIELD AI - OPERATIONAL WORKFLOW & INCIDENT RUNBOOK", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(6, 182, 212) # Cyan
        self.set_xy(12, 14)
        self.cell(0, 6, "Standard Operating Procedures (SOP) | Incident Response Matrix | Report Generation Guide", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}  |  CyberShield AI Platform v1.0.0  |  Confidential & Proprietary", align="C")

    def chapter_title(self, num, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(15, 23, 42)
        self.set_fill_color(226, 232, 240) # Slate-200
        self.cell(0, 8, f"  {num}. {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def section_heading(self, title):
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(2, 132, 199) # Blue-600
        self.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(51, 65, 85) # Slate-700
        self.multi_cell(0, 4.5, text)
        self.ln(2)

def generate_runbook():
    pdf = CyberShieldPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.alias_nb_pages()
    
    # ---------------- PAGE 1 ----------------
    pdf.add_page()
    pdf.set_margins(12, 15, 12)
    
    pdf.chapter_title(1, "System Overview & Daily Platform Operations")
    pdf.body_text(
        "CyberShield AI is an enterprise cybersecurity monitoring platform connecting central cloud orchestration "
        "(FastAPI on Render + Neon PostgreSQL) with on-premise monitoring agents. Daily operations require three active layers: "
        "the Backend API server, the Frontend single-page application, and at least one local Endpoint Monitoring Agent."
    )
    
    pdf.section_heading("Daily Startup & Operation Flow")
    
    # Startup steps table
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(30, 6, "Component", 1, 0, "C", True)
    pdf.cell(50, 6, "Execution Command", 1, 0, "C", True)
    pdf.cell(45, 6, "Default Port / URL", 1, 0, "C", True)
    pdf.cell(61, 6, "Expected Status Probe", 1, 1, "C", True)
    
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(30, 41, 59)
    rows = [
        ("1. Backend API", "uvicorn app.main:app --port 8000", "http://localhost:8000", "GET /health -> status: healthy"),
        ("2. Neon Database", "alembic upgrade head", "Neon Port 5432 (Pooler)", "GET /health/db -> connected"),
        ("3. Frontend UI", "npm run dev", "http://localhost:5173", "HTTP 200 Login Screen rendered"),
        ("4. Network Agent", "python main.py", "HTTPS to Backend /api/v1", "ONLINE badge in Agents table (30s)")
    ]
    for c, cmd, url, st in rows:
        pdf.cell(30, 5, c, 1, 0, "L")
        pdf.cell(50, 5, cmd, 1, 0, "L")
        pdf.cell(45, 5, url, 1, 0, "L")
        pdf.cell(61, 5, st, 1, 1, "L")
    pdf.ln(3)

    pdf.section_heading("User Roles & Operational Responsibilities")
    pdf.body_text(
        "* Administrator (admin@cybershield.ai): Full platform control. Issues agent enrollment tokens, manages users, "
        "edits system configuration settings, revokes compromised sensors, and reviews immutable compliance audit logs.\n"
        "* Security Analyst (analyst@cybershield.ai): Daily triage operator. Runs discovery scans, initiates vulnerability probes, "
        "acknowledges and resolves security alerts, chats with Local AI assistant, and generates executive reports.\n"
        "* Viewer (viewer@cybershield.ai): Read-only auditor. Views metrics, device lists, CVEs, and compliance summaries."
    )

    pdf.chapter_title(2, "Generating Compliance & Executive Reports")
    pdf.body_text(
        "CyberShield AI features an integrated PDF and CSV reporting pipeline built directly into the backend using fpdf2. "
        "Reports summarize real security telemetry, device inventories, vulnerability matrices, and incident response timelines."
    )

    pdf.section_heading("Step-by-Step: How to Generate a Report in the UI")
    pdf.body_text(
        "1. In the left navigation sidebar, click 'Reports' (Restricted to Administrator and Security Analyst roles).\n"
        "2. Click the '+ Generate Report' button in the upper-right corner.\n"
        "3. Select the desired Report Type from the options modal:\n"
        "   - Security Overview Report: Executive summary of overall organizational security posture, fleet asset counts, "
        "agent connectivity health, risk score distribution, and alert volume.\n"
        "   - Vulnerability Assessment Report: In-depth technical catalog of all identified CVEs, affected host IP addresses, "
        "listening software service banners, and severity CVSS scores.\n"
        "   - Incident & Alert Audit Report: Comprehensive chronological record of all triggered alarms, attacker source IPs, "
        "analyst status transitions, response timelines, and resolution notes.\n"
        "4. Choose the Reporting Period: Select Start Date and End Date (e.g., past 30 days or quarterly range).\n"
        "5. Click 'Generate Report'. The backend compiles the telemetry and marks the record as READY.\n"
        "6. In the Report Archive table, click 'PDF' to open/download a print-ready document or 'CSV' for SIEM data ingestion."
    )

    # ---------------- PAGE 2 ----------------
    pdf.add_page()
    pdf.chapter_title(3, "Incident Response Matrix: What to Do When What Happens")
    pdf.body_text(
        "This section serves as the definitive Standard Operating Procedure (SOP) and runbook for security operators. "
        "Follow these prescribed action trees when alarms trigger or abnormal events occur."
    )

    # Table of Scenarios
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(32, 6, "Trigger / Condition", 1, 0, "C", True)
    pdf.cell(48, 6, "Underlying Event Cause", 1, 0, "C", True)
    pdf.cell(52, 6, "Platform Automated Action", 1, 0, "C", True)
    pdf.cell(54, 6, "Required Operator Action", 1, 1, "C", True)

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(30, 41, 59)
    matrix = [
        ("Agent Status: OFFLINE", "Sensor missed 3 heartbeats (90s) due to network dropout or crash.", "Marks status OFFLINE in DB; stops assigning scan jobs to sensor.", "Verify sensor host power, inspect agent/.env BACKEND_URL, restart agent."),
        ("Alert: brute_force", "5+ failed logins from same source IP within a 10-minute window.", "Creates Alert, assigns Risk Score=40, sends in-app Notification.", "Acknowledge alert -> Check Log Management -> Block IP at firewall -> Resolve."),
        ("Alert: port_scan", "Host scan detected 10+ open ports on a single device.", "Creates Alert, assigns Risk Score=20, increases device risk factor.", "Verify if authorized vulnerability audit. If not, isolate host on VLAN."),
        ("Alert: suspicious_login", "Successful login from IP that had 3+ failures in previous hour.", "Creates Alert, assigns Risk Score=20, notifies admins.", "High risk credential stuffing! Force password reset; revoke active JWTs."),
        ("Alert: malware_indicator", "Network traffic source IP matches Threat Intelligence IOC list.", "Creates Alert, assigns Risk Score=40, records AuditLog.", "Immediately isolate endpoint; trace process initiating outbound connection."),
        ("CVE Finding: Critical", "Agent banner probe matched known RCE CVE (e.g., Log4Shell).", "Registers Vulnerability; adds +30 to device risk score.", "Click 'Explain with AI' -> Apply recommended vendor security patch."),
        ("Device Risk: Critical", "Combined high CVEs, active alerts, and port exposure score.", "Escalates device into Critical Risk Band on dashboard.", "Prioritize remediation of Critical CVEs and disable exposed ports.")
    ]
    for cond, cause, auto, oper in matrix:
        pdf.cell(32, 7, cond, 1, 0, "L")
        pdf.cell(48, 7, cause, 1, 0, "L")
        pdf.cell(52, 7, auto, 1, 0, "L")
        pdf.cell(54, 7, oper, 1, 1, "L")
    pdf.ln(4)

    pdf.chapter_title(4, "Detailed Playbooks: Step-by-Step Incident Workflows")
    
    pdf.section_heading("Playbook A: Brute Force Authentication Attack Response")
    pdf.body_text(
        "When an incident alert with alert_type='brute_force' appears in the top navigation bell:\n"
        "Step 1 - Triage & Acknowledge: Click the bell icon or navigate to 'Alerts'. Click the incident title to open details. "
        "Click the yellow 'Acknowledge' button. This stops alert duplication and notifies other team members you own the triage.\n"
        "Step 2 - AI Root Cause Assessment: Click the 'Explain with AI' button. The Local Security Explanation Engine "
        "will immediately parse the incident telemetry, identify the MITRE ATT&CK technique (T1110.001 - Password Guessing), "
        "and suggest immediate firewall isolation.\n"
        "Step 3 - Investigate Targeted Users: Go to 'Log Management' and filter by source IP matching the alert. "
        "Check which corporate usernames were targeted. Check if any 'login_success' event occurred after the failures.\n"
        "Step 4 - Mitigation: Add the attacker's IP to your perimeter firewall blocklist or VPN gateway null-route.\n"
        "Step 5 - Resolution: Return to the Alert page. Click the green 'Resolve' button and type your incident notes: "
        "'Attacker IP blocked at perimeter firewall. Target accounts verified uncompromised.' An immutable AlertEvent and AuditLog are saved."
    )

    pdf.section_heading("Playbook B: Critical Vulnerability Remediation Workflow")
    pdf.body_text(
        "When an automated scan discovers a critical vulnerability (e.g. CVE-2021-41773 Apache Path Traversal):\n"
        "Step 1 - Review Vulnerability Details: Go to 'Vulnerability Mgmt'. Filter by Severity: 'Critical'.\n"
        "Step 2 - Query AI Remediation: Click 'Explain with AI'. LocalRuleAI provides the specific minimum software version "
        "required to patch the flaw (e.g. upgrade Apache HTTP Server to 2.4.51 or higher) and transient configuration workarounds.\n"
        "Step 3 - Patch & Rescan: Deploy the security update to the host. In 'Devices', trigger 'Run Discovery Scan' to confirm "
        "the service version banner has updated and the vulnerability is closed."
    )

    # ---------------- PAGE 3 ----------------
    pdf.add_page()
    pdf.chapter_title(5, "Platform Resilience, Security Architecture & FAQ")
    
    pdf.section_heading("Security Architecture Safeguards")
    pdf.body_text(
        "1. Rate Limiting Protection: The POST /auth/login endpoint is shielded by SlowAPI at 10 requests/minute per IP. "
        "Rapid unauthorized attempts are rejected with HTTP 429 Too Many Requests.\n"
        "2. Strict Organization Boundaries: Every resource (device, alert, scan, setting) is scoped by organization_id. "
        "Users and agents cannot view or alter telemetry belonging to another tenant.\n"
        "3. LocalRuleAI Privacy: The AI assistant runs 100% on the backend server. Zero customer data, IP addresses, "
        "or vulnerability parameters are transmitted across external cloud AI APIs."
    )

    pdf.section_heading("Frequently Asked Operational Questions")
    
    faq_items = [
        ("Q: What happens if the backend server restarts while an agent is running?",
         "A: The agent contains an exponential backoff retry loop and an in-memory offline queue. It buffers heartbeats and retries connecting every 30 seconds for up to 10 attempts (5 minutes) before gracefully reporting status."),
        
        ("Q: Why does the device risk score change after resolving an alert?",
         "A: The CyberShield multi-factor risk engine recalculates device risk dynamically. Resolved alerts no longer contribute penalty points (+20 for brute force, +15 for suspicious login), immediately lowering the host's risk band."),
        
        ("Q: How can I export audit logs for external compliance reviews (SOC 2, ISO 27001)?",
         "A: Log in as Administrator. Navigate to 'Settings' -> 'Audit Logs' or 'Reports'. Generate an 'Incident & Alert Audit Report' and download the CSV format for direct import into SIEM or compliance spreadsheets.")
    ]
    
    for q, a in faq_items:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5, q, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(0, 4.5, a)
        pdf.ln(2)

    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "CyberShield_AI_Operational_Runbook.pdf")
    pdf.output(output_path)
    print(f"Runbook PDF generated successfully at: {output_path}")

if __name__ == "__main__":
    generate_runbook()
