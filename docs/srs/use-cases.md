# CyberShield AI - Use Cases

**Version:** 2.0  
**Date:** August 23, 2026  
**Phase:** 1 of 27 - Project Requirements & SRS

---

## Table of Contents

1. [Authentication Use Cases](#1-authentication-use-cases)
2. [User Management Use Cases](#2-user-management-use-cases)
3. [Agent Management Use Cases](#3-agent-management-use-cases)
4. [Device Discovery Use Cases](#4-device-discovery-use-cases)
5. [Vulnerability Scanning Use Cases](#5-vulnerability-scanning-use-cases)
6. [Threat Detection Use Cases](#6-threat-detection-use-cases)
7. [Alert Management Use Cases](#7-alert-management-use-cases)
8. [Reporting Use Cases](#8-reporting-use-cases)
9. [Dashboard Use Cases](#9-dashboard-use-cases)

---

## 1. Authentication Use Cases

### UC-AUTH-01: User Login

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User has a valid account in the system
- User account is not locked
- System is accessible and operational

**Main Flow**:
1. User navigates to the login page
2. User enters username and password
3. User clicks "Login" button
4. System validates username and password
5. System generates JWT session token
6. System redirects user to dashboard
7. Session token is stored in browser localStorage

**Alternative Flows**:
- **Invalid Credentials**: System displays error message "Invalid username or password"
- **Account Locked**: System displays error message "Account locked. Please try again in 30 minutes or contact administrator"
- **System Unavailable**: System displays error message "System temporarily unavailable"

**Postconditions**:
- User is authenticated and has active session
- User can access authorized features based on role
- Session expires after 24 hours of inactivity

---

### UC-AUTH-02: User Logout

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in with active session

**Main Flow**:
1. User clicks "Logout" button
2. System invalidates JWT session token
3. System clears session data from browser
4. System redirects user to login page

**Postconditions**:
- User session is terminated
- User must authenticate again to access system

---

### UC-AUTH-03: Password Change

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in with active session
- User knows current password

**Main Flow**:
1. User navigates to profile settings
2. User clicks "Change Password"
3. User enters current password
4. User enters new password
5. User confirms new password
6. System validates current password
7. System validates new password meets requirements
8. System updates password hash in database
9. System displays success message
10. System prompts user to log in again

**Alternative Flows**:
- **Invalid Current Password**: System displays error message "Current password is incorrect"
- **New Password Too Weak**: System displays error message "Password must be at least 12 characters with uppercase, lowercase, number, and special character"
- **Passwords Do Not Match**: System displays error message "New password and confirmation do not match"

**Postconditions**:
- User password is updated
- User must authenticate with new password

---

## 2. User Management Use Cases

### UC-USER-01: Create User

**Actor**: Administrator

**Preconditions**:
- Administrator is logged in
- Administrator has user management permissions

**Main Flow**:
1. Administrator navigates to user management page
2. Administrator clicks "Create User" button
3. Administrator enters username
4. Administrator enters email
5. Administrator enters initial password
6. Administrator selects role (Administrator, Security Analyst, Viewer)
7. Administrator clicks "Create"
8. System validates username is unique
9. System validates email is unique
10. System validates password meets requirements
11. System creates user account with password hash
12. System adds entry to audit log
13. System displays success message

**Alternative Flows**:
- **Username Exists**: System displays error message "Username already exists"
- **Email Exists**: System displays error message "Email already exists"
- **Password Too Weak**: System displays error message "Password does not meet requirements"

**Postconditions**:
- New user account exists in system
- User can log in with provided credentials
- Audit log records user creation

---

### UC-USER-02: Update User Role

**Actor**: Administrator

**Preconditions**:
- Administrator is logged in
- User to update exists in system
- Administrator is not the only Administrator (if removing Administrator role)

**Main Flow**:
1. Administrator navigates to user management$page
2. Administrator selects user from list
3. Administrator clicks "Edit"
4. Administrator changes role selection
5. Administrator clicks "Save"
6. System validates role change is permitted
7. System updates user role in database
8. System adds entry to audit log
9. System displays success message

**Alternative Flows**:
- **Last Administrator**: System displays error message "Cannot remove Administrator role from last administrator"
- **Self Role Change**: System displays error message "Cannot change your own role"

**Postconditions**:
- User role is updated
- User permissions change on next login
- Audit log records role change

---

### UC-USER-03: Delete User

**Actor**: Administrator

**Preconditions**:
- Administrator is logged in
- User to delete exists in system
- User is not the only Administrator

**Main Flow**:
1. Administrator navigates to user management page
2. Administrator selects user from list
3. Administrator clicks "Delete"
4. System displays confirmation dialog
5. Administrator confirms deletion
6. System deletes user account from database
7. System invalidates all active sessions for user
8. System adds entry to audit log
9. System displays success message

**Alternative Flows**:
- **Last Administrator**: System displays error message "Cannot delete last administrator"
- **User Deletion Cancelled**: System returns to user list without changes

**Postconditions**:
- User account is removed from system
- User cannot log in
- Audit log records user deletion

---

## 3. Agent Management Use Cases

### UC-AGENT-01: Register Agent

**Actor**: System (automated), Administrator (manual configuration)

**Preconditions**:
- Backend system is running
- Agent software is installed on target machine
- Network connectivity exists between agent and backend

**Main Flow**:
1. Agent generates unique agent ID
2. Agent sends registration request to backend API
3. Backend validates authentication token
4. Backend stores agent information (ID, hostname, IP, OS version)
5. Backend returns registration confirmation
6. Agent begins sending heartbeat messages
7. Backend updates agent status to "online"

**Alternative Flows**:
- **Invalid Token**: Backend returns 401 Unauthorized, agent retries with valid token
- **Duplicate Agent ID**: Backend returns error, agent generates new ID and retries

**Postconditions**:
- Agent is registered in system
- Agent appears in agent list
- Agent status is tracked

---

### UC-AGENT-02: View Agent Status

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in
- User has agent viewing permissions
- Agent is registered in system

**Main Flow**:
1. User navigates to agent management page
2. System displays list of registered agents
3. User clicks on specific agent
4. System displays agent details (hostname, IP, OS, status, last seen)
5. System displays agent heartbeat history

**Postconditions**:
- User can view agent status and details
- User can identify offline agents

---

### UC-AGENT-03: Deregister Agent

**Actor**: Administrator

**Preconditions**:
- Administrator is logged in
- Agent to deregister exists in system

**Main Flow**:
1. Administrator navigates to agent management page
2. Administrator selects agent from list
3. Administrator clicks "Deregister"
4. System displays confirmation dialog
5. Administrator confirms deregistration
6. System removes agent from database
7. System stops processing data from agent
8. System adds entry to audit log
9. System displays success message

**Postconditions**:
- Agent is removed from system
- Agent data is no longer accepted
- Audit log records agent deregistration

---

## 4. Device Discovery Use Cases

### UC-DEV-01: Trigger Network Scan

**Actor**: Administrator, Security Analyst

**Preconditions**:
- User is logged in
- User has scan triggering permissions
- At least one agent is online

**Main Flow**:
1. User navigates to device discovery page
2. User clicks "Scan Network" button
3. User selects target agent or "All Agents"
4. User selects scan type (quick, full)
5. User clicks "Start Scan"
6. System sends scan command to selected agent(s)
7. Agent performs network scan (ICMP ping, port scan)
8. Agent sends discovered devices to backend
9. Backend stores device information in database
10. Backend updates device inventory
11. System displays scan progress
12. System displays scan results when complete

**Alternative Flows**:
- **No Online Agents**: System displays error message "No agents available for scanning"
- **Scan Timeout**: System displays error message "Scan timed out, please try again"

**Postconditions**:
- Discovered devices are added to inventory
- Device information is stored in database
- Scan results are available for viewing

---

### UC-DEV-02: View Device Inventory

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in
- User has device viewing permissions
- Devices have been discovered

**Main Flow**:
1. User navigates to device discovery page
2. System displays list of discovered devices
3. User can filter devices by type, status, or IP range
4. User clicks on specific device
5. System displays device details (IP, MAC, hostname, open ports, services, OS)

**Postconditions**:
- User can view device inventory
- User can access detailed device information

---

### UC-DEV-03: Configure Scheduled Scans

**Actor**: Administrator

**Preconditions**:
- Administrator is logged in
- Administrator has configuration permissions

**Main Flow**:
1. Administrator navigates to device discovery settings
2. Administrator clicks "Configure Scheduled Scans"
3. Administrator selects scan interval (hourly, daily, weekly)
4. Administrator selects target agent(s)
5. Administrator selects scan type
6. Administrator clicks "Save"
7. System stores scheduled scan configuration
8. System adds entry to audit log
9. System displays success message

**Postconditions**:
- Scheduled scans are configured
- System automatically triggers scans at configured intervals
- Audit log records configuration change

---

## 5. Vulnerability Scanning Use Cases

### UC-VULN-01: Trigger Vulnerability Scan

**Actor**: Administrator, Security Analyst

**Preconditions**:
- User is logged in
- User has scan triggering permissions
- CVE database is available
- At least one agent is online

**Main Flow**:
1. User navigates to vulnerability scanning page
2. User clicks "Scan Vulnerabilities" button
3. User selects target device(s) or "All Devices"
4. User clicks "Start Scan"
5. System sends scan command to agent
6. Agent collects software version information from target device
7. Agent sends software data to backend
8. Backend compares software versions against CVE database
9. Backend identifies matching vulnerabilities
10. Backend calculates severity based on CVSS scores
11. Backend stores vulnerability results in database
12. System displays scan progress
13. System displays vulnerability results when complete

**Alternative Flows**:
- **CVE Database Outdated**: System prompts user to update CVE database first
- **Device Unreachable**: System marks device as unreachable and continues with other devices

**Postconditions**:
- Vulnerability scan results are stored
- Vulnerabilities are categorized by severity
- Results are available for viewing and reporting

---

### UC-VULN-02: View Vulnerability Details

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in
- User has vulnerability viewing permissions
- Vulnerabilities have been detected

**Main Flow**:
1. User navigates to vulnerability scanning page
2. System displays list of detected vulnerabilities
3. User filters vulnerabilities by severity, device, or CVE ID
4. User clicks on specific vulnerability
5. System displays vulnerability details (CVE ID, description, CVSS score, affected software, remediation steps)

**Postconditions**:
- User can view vulnerability details
- User can access remediation recommendations

---

### UC-VULN-03: Update CVE Database

**Actor**: Administrator

**Preconditions**:
- Administrator is logged in
- Internet connectivity is available

**Main Flow**:
1. Administrator navigates to vulnerability scanning settings
2. Administrator clicks "Update CVE Database"
3. System connects to NVD (National Vulnerability Database)
4. System downloads latest CVE data
5. System processes and stores CVE data in local database
6. System displays update progress
7. System displays success message with number of CVEs updated

**Alternative Flows**:
- **No Internet Connection**: System displays error message "Internet connection required for CVE database update"
- **NVD Unavailable**: System displays error message "NVD service unavailable, please try again later"

**Postconditions**:
- Local CVE database is updated
- Vulnerability scans use latest CVE data
- Audit log records database update

---

## 6. Threat Detection Use Cases

### UC-THREAT-01: Investigate Alert

**Actor**: Administrator, Security Analyst

**Preconditions**:
- User is logged in
- User has alert viewing permissions
- Alert has been generated

**Main Flow**:
1. User navigates to alerts page
2. System displays list of alerts
3. User filters alerts by severity, status, or time range
4. User clicks on specific alert
5. System displays alert details (threat type, severity, evidence, affected assets, timestamp)
6. User clicks "View AI Explanation"
7. System displays rule-based explanation of threat
8. User clicks "Acknowledge" to mark alert as reviewed
9. User optionally assigns alert to themselves or another user
10. User updates alert status (investigating, resolved, false positive)
11. System adds entry to audit log

**Postconditions**:
- Alert status is updated
- Alert assignment is recorded
- Audit log records investigation actions

---

### UC-THREAT-02: Create Detection Rule

**Actor**: Administrator, Security Analyst

**Preconditions**:
- User is logged in
- User has rule creation permissions

**Main Flow**:
1. User navigates to threat detection settings
2. User clicks "Create Detection Rule"
3. User enters rule name
4. User selects rule type (signature, anomaly, correlation)
5. User defines rule conditions (log pattern, network traffic pattern, threshold)
6. User assigns severity level
7. User optionally assigns recommended actions
8. User clicks "Save"
9. System validates rule syntax
10. System stores rule in database
11. System activates rule for threat detection
12. System adds entry to audit log
13. System displays success message

**Alternative Flows**:
- **Invalid Syntax**: System displays error message "Invalid rule syntax, please correct"
- **Rule Name Exists**: System displays error message "Rule name already exists"

**Postconditions**:
- Detection rule is active
- System uses rule for threat detection
- Audit log records rule creation

---

### UC-THREAT-03: View Threat Correlation

**Actor**: Administrator, Security Analyst

**Preconditions**:
- User is logged in
- User has threat viewing permissions
- Multiple related threats have been detected

**Main Flow**:
1. User navigates to threat detection page
2. User clicks "View Correlated Threats"
3. System analyzes threat patterns and relationships
4. System displays threat clusters or attack chains
5. User clicks on specific threat cluster
6. System displays timeline of related events
7. System displays affected assets across cluster
8. System displays common attack patterns

**Postconditions**:
- User can identify attack campaigns
- User can understand threat relationships
- User can prioritize response based on cluster severity

---

## 7. Alert Management Use Cases

### UC-ALERT-01: Configure Alert Rules

**Actor**: Administrator

**Preconditions**:
- Administrator is logged in
- Administrator has configuration permissions

**Main Flow**:
1. Administrator navigates to alert settings
2. Administrator clicks "Configure Alert Rules"
3. Administrator selects alert trigger condition (risk threshold, threat severity, system event)
4. Administrator sets threshold values
5. Administrator selects notification channels (in-app, email)
6. Administrator selects recipients for email alerts
7. Administrator clicks "Save"
8. System stores alert rule configuration
9. System adds entry to audit log
10. System displays success message

**Postconditions**:
- Alert rules are configured
- System generates alerts based on rules
- Audit log records configuration change

---

### UC-ALERT-02: Acknowledge Alert

**Actor**: Administrator, Security Analyst

**Preconditions**:
- User is logged in
- Alert exists and is not already acknowledged

**Main Flow**:
1. User navigates to alerts page
2. User clicks on specific alert
3. User clicks "Acknowledge" button
4. System updates alert status to acknowledged
5. System records user who acknowledged and timestamp
6. System adds entry to audit log
7. System displays success message

**Postconditions**:
- Alert is marked as acknowledged
- Alert no longer appears in "new" alerts filter
- Audit log records acknowledgment

---

### UC-ALERT-03: Resolve Alert

**Actor**: Administrator, Security Analyst

**Preconditions**:
- User is logged in
- Alert exists and is acknowledged

**Main Flow**:
1. User navigates to alerts page
2. User clicks on specific alert
3. User enters resolution notes
4. User clicks "Resolve" button
5. System updates alert status to resolved
6. System stores resolution notes
7. System records user who resolved and timestamp
8. System adds entry to audit log
9. System displays success message

**Postconditions**:
- Alert is marked as resolved
- Resolution is documented
- Audit log records resolution

---

## 8. Reporting Use Cases

### UC-REP-01: Generate Security Report

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in
- User has report generation permissions
- Data exists for selected time range

**Main Flow**:
1. User navigates to reports page
2. User clicks "Generate Report"
3. User selects report template (vulnerability summary, threat summary, risk assessment, compliance)
4. User selects time range (last 24 hours, last 7 days, last 30 days, custom)
5. User optionally selects specific devices or agents
6. User clicks "Generate"
7. System collects data from database
8. System formats data according to template
9. System generates report
10. System displays report preview
11. User selects export format (PDF, CSV, JSON)
12. User clicks "Download"
13. System generates downloadable file
14. System stores report in database with metadata

**Alternative Flows**:
- **No Data Available**: System displays message "No data available for selected time range"
- **Generation Timeout**: System displays error message "Report generation timed out, please try again with smaller time range"

**Postconditions**:
- Report is generated and stored
- Report is available for download
- Report metadata is recorded in database

---

### UC-REP-02: Configure Scheduled Reports

**Actor**: Administrator

**Preconditions**:
- Administrator is logged in
- Administrator has configuration permissions

**Main Flow**:
1. Administrator navigates to reports settings
2. Administrator clicks "Configure Scheduled Reports"
3. Administrator clicks "Create Schedule"
4. Administrator selects report template
5. Administrator selects schedule interval (daily, weekly, monthly)
6. Administrator selects time of day
7. Administrator selects recipients
8. Administrator clicks "Save"
9. System stores scheduled report configuration
10. System adds entry to audit log
11. System displays success message

**Postconditions**:
- Scheduled report is configured
- System automatically generates reports at scheduled times
- Recipients receive reports via configured notification channels
- Audit log records configuration change

---

### UC-REP-03: Create Custom Report Template

**Actor**: Administrator, Security Analyst

**Preconditions**:
- User is logged in
- User has template creation permissions

**Main Flow**:
1. User navigates to reports page
2. User clicks "Create Custom Template"
3. User enters template name
4. User selects data sources (vulnerabilities, threats, logs, risk scores)
5. User configures filters for each data source
6. User selects visualizations (charts, tables, graphs)
7. User arranges layout of report sections
8. User clicks "Save Template"
9. System stores custom template
10. Template appears in template selection list
11. System adds entry to audit log
12. System displays success message

**Postconditions**:
- Custom template is saved
- Template can be used for report generation
- Audit log records template creation

---

## 9. Dashboard Use Cases

### UC-DASH-01: View Overview Dashboard

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in
- System is operational

**Main Flow**:
1. User navigates to dashboard
2. System displays overview dashboard with widgets:
   - Overall risk score with trend
   - Active threats count by severity
   - Open vulnerabilities count by severity
   - Agent status (online/offline)
   - Recent alerts feed
   - Network traffic chart
   - Device inventory summary
3. System updates widgets in real-time via WebSocket
4. User can click on any widget to view detailed data

**Postconditions**:
- User has comprehensive view of security posture
- User can identify areas requiring attention

---

### UC-DASH-02: Customize Dashboard

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in

**Main Flow**:
1. User navigates to dashboard
2. User clicks "Customize Dashboard"
3. System displays available widgets
4. User selects which widgets to display
5. User arranges widgets by drag-and-drop
6. User clicks "Save"
7. System stores dashboard configuration for user
8. System displays customized dashboard

**Postconditions**:
- Dashboard displays user's selected widgets
- Dashboard layout is saved for future sessions

---

### UC-DASH-03: View Real-Time Updates

**Actor**: Administrator, Security Analyst, Viewer

**Preconditions**:
- User is logged in
- User is on dashboard page

**Main Flow**:
1. User navigates to dashboard
2. System establishes WebSocket connection
3. System pushes real-time updates:
   - New alerts appear in alert feed
   - Risk score updates when vulnerabilities change
   - Agent status updates when heartbeat received
   - Network traffic chart updates continuously
4. User sees changes without page refresh

**Alternative Flows**:
- **WebSocket Disconnected**: System displays "Connection lost, reconnecting..." and attempts to reconnect
- **Reconnection Failed**: System displays "Real-time updates unavailable, refresh page to retry"

**Postconditions**:
- User sees live updates without manual refresh
- Dashboard reflects current system state

---

## Appendix A: Use Case Prioritization

The following use cases are prioritized for Phase 1 MVP implementation:

**High Priority (Must Have)**:
- UC-AUTH-01: User Login
- UC-AUTH-02: User Logout
- UC-AGENT-01: Register Agent
- UC-AGENT-02: View Agent Status
- UC-DEV-01: Trigger Network Scan
- UC-DEV-02: View Device Inventory
- UC-VULN-01: Trigger Vulnerability Scan
- UC-VULN-02: View Vulnerability Details
- UC-THREAT-01: Investigate Alert
- UC-ALERT-02: Acknowledge Alert
- UC-REP-01: Generate Security Report
- UC-DASH-01: View Overview Dashboard

**Medium Priority (Should Have)**:
- UC-AUTH-03: Password Change
- UC-USER-01: Create User
- UC-USER-02: Update User Role
- UC-AGENT-03: Deregister Agent
- UC-DEV-03: Configure Scheduled Scans
- UC-VULN-03: Update CVE Database
- UC-THREAT-02: Create Detection Rule
- UC-ALERT-01: Configure Alert Rules
- UC-ALERT-03: Resolve Alert
- UC-REP-02: Configure Scheduled Reports
- UC-DASH-02: Customize Dashboard
- UC-DASH-03: View Real-Time Updates

**Low Priority (Nice to Have)**:
- UC-USER-03: Delete User
- UC-THREAT-03: View Threat Correlation
- UC-REP-03: Create Custom Report Template

---

## Appendix B: Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | August 23, 2026 | Development Team | Initial use cases document for Phase 1 MVP |

---

## Appendix C: Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Manager | | | |
| Lead Developer | | | |
| Security Architect | | | |
| QA Lead | | | |
