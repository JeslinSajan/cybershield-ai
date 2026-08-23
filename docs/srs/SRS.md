# CyberShield AI — Software Requirements Specification (SRS)

**Version:** 2.0 (correction of v1.0 — see Appendix A)
**Date:** August 2026
**Project:** Final-Year B.E. Computer Science Engineering Project
**Institution:** PPG Institute of Technology, Coimbatore

---

## Table of Contents

1. Introduction
2. Overall Description
3. Specific Requirements (summary — full detail in companion documents)
4. External Interface Requirements
5. Constraints and Assumptions
6. Future Enhancements (explicitly out of MVP scope)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for **CyberShield AI**, an
agent-based unified cybersecurity monitoring and threat management
platform, developed as a final-year engineering capstone project. It
defines what the system must do, for whom, and under what constraints,
to guide implementation, testing, and evaluation from August 2026 to
February 2027.

### 1.2 Scope

CyberShield AI centralizes security visibility for small, authorized
environments (college labs, schools, startups, home labs) through a
lightweight local Agent that reports system, network, and log data to
a central Backend, which performs rule-based threat detection, risk
scoring, alerting, and reporting, surfaced through a web dashboard.

The system is **local-first**: the complete MVP pipeline runs entirely
on a single laptop during development, with no dependency on a paid
cloud AI API or a cloud VM. It is architected so it can later be
containerized and deployed to a cloud VM without redesign.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Meaning |
|---|---|
| Agent | Local Python application collecting security data from an authorized host |
| RBAC | Role-Based Access Control |
| CVE | Common Vulnerabilities and Exposures |
| MVP | Minimum Viable Product |
| LocalRuleAI | Deterministic, rule-based explanation engine (no external LLM) |
| SOC | Security Operations Center (style of UI, not a claim of enterprise SOC capability) |

### 1.4 References

- Original project specification document (CyberShield AI — Agent-Based
  Unified Cybersecurity Monitoring and Threat Management Platform)
- OWASP Top 10 Security Risks
- IEEE Std 830-1998 (SRS structure reference only — not followed rigidly,
  given project scale)

### 1.5 Overview

Section 2 describes the system's context and users. Section 3
summarizes requirement categories (full numbered requirements are in
`functional-requirements.md` and `non-functional-requirements.md`).
Section 4 covers interfaces. Section 5 states constraints and
assumptions explicitly, including what this project deliberately does
**not** attempt. Section 6 lists future enhancements that are
out of scope for the graded MVP.

---

## 2. Overall Description

### 2.1 Product Perspective

CyberShield AI is a **standalone, self-contained local application**
for its MVP phase — not a hosted multi-tenant SaaS product. It
consists of four components running on one laptop during development:

- **Frontend** — React + TypeScript SOC-style dashboard
- **Backend** — FastAPI REST API with PostgreSQL persistence
- **CyberShield Agent** — Python agent on the authorized host(s)
- **Local Security Explanation Engine** — deterministic rule-based
  module behind an `AIService` abstraction, replacing any need for an
  external AI API during development

There is no reverse proxy, load balancer, or orchestration layer in
the MVP. Docker Compose packages the four components for reproducible
local runs and, later, single-VM cloud deployment.

### 2.2 Product Functions

The MVP shall provide:

1. Authentication and RBAC (Administrator, Security Analyst, Viewer)
2. Agent registration, authentication, and heartbeat monitoring
3. Authorized local-network device discovery (via Nmap)
4. Vulnerability scanning with local/cached CVE data
5. Log collection and normalization (SSH/auth logs, syslog)
6. Deterministic threat detection (brute force, port scan, suspicious
   login, indicator match)
7. Transparent, documented rule-based risk scoring (0–100)
8. Alert lifecycle management (Open → Acknowledged → Investigating →
   Resolved / False Positive)
9. A dashboard summarizing agents, devices, vulnerabilities, alerts,
   and risk
10. A Local Security Explanation Engine that explains alerts,
    vulnerabilities, and risk scores in plain language, clearly
    labeled as a local rule-based engine (not an external LLM)
11. PDF/CSV report generation

### 2.3 User Characteristics

Three user roles interact with the system directly (see
`user-roles.md` for the full permission matrix):

- **Administrator** — manages users, roles, agents, and system settings
- **Security Analyst** — operates the platform day-to-day: runs scans,
  investigates alerts, uses the AI assistant, generates reports
- **Viewer** — read-only access for oversight

A non-human actor, the **CyberShield Agent**, also interacts with the
system via a restricted API — it is not a user and has no dashboard
access.

There is no "Executive" role and no assumption of thousands of users;
this is a single-organization tool for a handful of accounts during
the academic demonstration.

### 2.4 Constraints

- **No external AI API** (OpenAI, Gemini, Qwen, or any paid service)
  is available during development. All AI-labeled functionality must
  work through `LocalRuleAI` with zero external calls.
- **No cloud VM** is available during development. Every MVP workflow
  must run and be demonstrable entirely on a single laptop.
- Development team size is small (final-year student project); the
  system must remain buildable and maintainable at that scale — not
  designed for enterprise concurrency or high-availability guarantees.
- Only authorized systems and networks may be scanned or monitored;
  the UI must state this clearly wherever a scan or discovery action
  is initiated.
- Timeline: August 2026 – February 2027, developed incrementally by
  phase (see project roadmap), not in a single implementation pass.

### 2.5 Assumptions and Dependencies

- The developer/team has admin access to at least one authorized Linux
  host to run the Agent against during development.
- PostgreSQL, Python, and Node.js are installed locally.
- Nmap is available on the host running discovery/scans.
- CVE reference data will be seeded locally (static/sample dataset)
  when no external CVE feed is reachable, clearly labeled as
  development/demo data.
- A future phase may introduce a real cloud VM and/or a real AI API;
  the architecture must not require rework to adopt them (see
  `AIService` abstraction and Docker packaging).

---

## 3. Specific Requirements (Summary)

Full, numbered functional requirements are defined in
**`functional-requirements.md`**, organized by module: Authentication,
User Management, Agent Management, Device Discovery, Vulnerability
Scanning, Network Monitoring, Log Management, Threat Detection, Threat
Intelligence, Risk Scoring, Alerts, AI Assistant, Reports,
Notifications, Audit Logging, and Dashboard.

Full non-functional requirements (performance, security, reliability,
usability, maintainability, privacy — scoped realistically to a local
single-laptop deployment, not enterprise SLAs) are defined in
**`non-functional-requirements.md`**.

Role permissions are defined in **`user-roles.md`**.

Primary user workflows are defined in **`use-cases.md`**.

---

## 4. External Interface Requirements

### 4.1 User Interface

- Web-based dashboard (React SPA), served locally during development
  (e.g. `localhost:5173`), accessed via a modern desktop browser
  (Chrome/Firefox/Edge). Mobile/tablet responsiveness is a
  nice-to-have, not a Phase 1–13 requirement.
- Dark, professional SOC-style theme (see UI/UX wireframes phase).

### 4.2 Hardware Interfaces

- Runs on standard developer laptop hardware (no GPU, no specialized
  hardware required for LocalRuleAI, since it is rule-based, not a
  trained model requiring inference hardware).

### 4.3 Software Interfaces

- **Database:** PostgreSQL 14+ (local instance)
- **Backend framework:** FastAPI (Python), SQLAlchemy, Alembic
- **Frontend framework:** React + TypeScript + Vite
- **Agent runtime:** Python 3.x, using `psutil`, `httpx`, and Nmap
  (invoked as a subprocess or via a Python wrapper)
- **AI:** `AIService` abstraction; `LocalRuleAI` implementation only
  for the MVP; `OllamaAI`/`OpenAIProvider` are future, optional
  implementations of the same interface

### 4.4 Communication Interfaces

- Agent-to-Backend: HTTP/HTTPS REST over the local network
  (`http://localhost:8000` or LAN address during development)
- Frontend-to-Backend: HTTP/HTTPS REST, JSON payloads
- No mutual TLS, no WebSocket-at-scale, and no distributed message bus
  are required for the MVP — these belong in Section 6
  (Future Enhancements) if pursued at all.

---

## 5. Constraints and Assumptions (Explicit Non-Goals for MVP)

To keep the project realistic for one student/team and gradable within
this timeline, the following are **explicitly not MVP requirements**:

- No requirement to support 1,000+ concurrent users
- No requirement for horizontal scaling, load balancing, or database
  sharding
- No requirement for 99.9% uptime, automated failover, or disaster
  recovery targets
- No requirement for GDPR/ISO 27001 compliance processes (may be
  *referenced* conceptually in documentation, but not implemented as
  operational controls)
- No requirement for multi-factor authentication in the MVP (may be a
  future enhancement)
- No dependency on any external/paid AI service

---

## 6. Future Enhancements (Out of MVP Scope)

Recorded here so they are not silently designed-in nor silently lost:

- Multi-tenant / multi-organization SaaS deployment
- Kubernetes-based orchestration
- Real-time push notifications via Telegram/Discord/Slack
- Integration with a live external AI provider (Ollama, OpenAI, Qwen)
  behind the existing `AIService` abstraction
- Public threat-intelligence feed integration (beyond local indicator
  data)
- Windows Event Log collection (Linux log collection is the MVP target)
- Oracle Cloud deployment of the same Docker Compose stack

---

## Appendix A: Revision History

| Version | Date | Change |
|---|---|---|
| 1.0 | Aug 22, 2026 | Initial draft — generated from a generic enterprise cybersecurity SaaS template; incorrectly assumed Qwen AI integration, 1,000+ concurrent users, microservices/Kubernetes architecture, and mismatched user roles. Not aligned with actual project constraints. |
| 2.0 | Aug 2026 | Corrected: removed all external/cloud-AI dependency language, removed enterprise-scale claims, aligned user roles to Administrator/Security Analyst/Viewer, scoped all requirements to local-first single-laptop MVP, added explicit Future Enhancements section. |

## Appendix B: Approval

| Role | Name | Date |
|---|---|---|
| Student / Developer | Jeslin | |
| Project Guide | | |
