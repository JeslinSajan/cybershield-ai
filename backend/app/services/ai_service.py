"""
Local Rule AI Security Explanation Engine — Phase 19.

This service is a deterministic, rule-based security explanation engine.
It uses NO external AI APIs, NO LLMs, and runs 100% locally and offline.
Label in UI: 'Local Security Explanation Engine'.

Provides:
- explain_alert: Explanations and triage playbooks for security alerts.
- explain_vulnerability: CVE technical breakdown and remediation advice.
- explain_risk_score: Quantified breakdown of risk scoring factors.
- chat: Contextual conversational interface with persistent AIConversation history.
"""

from abc import ABC, abstractmethod
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.ai import AIConversation, AIMessage
from app.models.alert import Alert, RiskScore
from app.models.device import Device
from app.models.scan import CVE, Vulnerability

logger = logging.getLogger("app.services.ai")


class AIService(ABC):
    """Abstract base class for AI security explanation engines."""

    @abstractmethod
    def explain_alert(self, db: Session, alert_id: uuid.UUID, org_id: uuid.UUID) -> str:
        """Generate human-readable explanation and triage recommendations for an alert."""
        pass

    @abstractmethod
    def explain_vulnerability(self, db: Session, vuln_id: uuid.UUID, org_id: uuid.UUID) -> str:
        """Generate technical CVE explanation and mitigation steps for a vulnerability."""
        pass

    @abstractmethod
    def explain_risk_score(self, db: Session, device_id: uuid.UUID, org_id: uuid.UUID) -> str:
        """Generate breakdown and score reduction guidance for a device risk score."""
        pass


class LocalRuleAI(AIService):
    """
    Deterministic rule-based explanation engine.
    Uses strictly local database telemetry to construct structured SOC intelligence summaries.
    """

    PROVIDER_NAME = "local_rule_ai"

    def explain_alert(self, db: Session, alert_id: uuid.UUID, org_id: uuid.UUID) -> str:
        alert = (
            db.query(Alert)
            .filter(Alert.id == alert_id, Alert.organization_id == org_id)
            .first()
        )
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "message": f"Alert '{alert_id}' was not found.", "details": []}},
            )

        device = None
        if alert.device_id:
            device = db.query(Device).filter(Device.id == alert.device_id).first()

        device_str = (
            f"Device {device.ip_address} ({device.hostname or 'unknown hostname'})"
            if device
            else "Target host / endpoint"
        )
        atype = alert.alert_type.lower()
        score = float(alert.risk_score) if alert.risk_score is not None else 0.0

        sections = [
            f"### [CyberShield AI Alert Analysis — {alert.alert_type.upper().replace('_', ' ')}]",
            f"**Severity:** {alert.severity} | **Risk Weight:** {score} pts | **Status:** {alert.status}",
            f"**Affected Asset:** {device_str}",
            f"**Alert Description:** {alert.description}",
            "",
            "#### 1. Threat Description & Mechanism",
        ]

        if atype == "brute_force":
            sections.extend([
                "A brute-force attack was detected. Multiple authentication failures were recorded from an identical source "
                "within a tight time threshold (typically 5+ failed attempts in under 10 minutes). "
                "This indicates an adversary or automated bot script attempting dictionary or credential-stuffing attacks "
                "against local services."
            ])
        elif atype == "port_scan":
            sections.extend([
                "A port scanning reconnaissance pattern was detected. An external or internal scanner interrogated 10 or more "
                "open network ports on the asset. Adversaries use port sweeps to profile running operating systems and "
                "service versions before launching targeted exploits."
            ])
        elif atype == "suspicious_login":
            sections.extend([
                "A suspicious authentication anomaly was detected. A successful authentication occurred from an IP address "
                "that previously recorded multiple failed login attempts within the preceding hour. This is a high-confidence "
                "indicator of credential compromise, brute-force success, or unauthorized session acquisition."
            ])
        elif atype == "malware_indicator":
            sections.extend([
                "A confirmed threat intelligence match was triggered. Ingested network or authentication telemetry matches "
                "a known malicious indicator of compromise (IOC) recorded in the CyberShield Threat Intelligence database. "
                "This suggests active communication with adversary command-and-control (C2) or botnet infrastructure."
            ])
        else:
            sections.extend([
                f"Security event triggered rule '{alert.alert_type}'. The system flagged anomalous activity matching "
                f"configured SOC detection thresholds."
            ])

        sections.extend([
            "",
            "#### 2. Potential Impact",
            f"- **Confidentiality / Integrity:** Potential unauthorized access to asset `{device_str}`.",
            f"- **Lateral Movement Risk:** Asset risk score increased by +{score} points.",
            "",
            "#### 3. Recommended Incident Response Playbook",
            "1. **Isolate or Block:** Temporarily restrict or firewall the source IP address identified in the telemetry.",
            "2. **Credential Auditing:** Invalidate active sessions and force a credential reset for any targeted accounts.",
            "3. **Log Examination:** Inspect surrounding authentication and connection logs for preceding activity.",
            f"4. **Status Triage:** Update alert status in CyberShield AI to `Acknowledged` or `Investigating` to track review.",
        ])

        return "\n".join(sections)

    def explain_vulnerability(self, db: Session, vuln_id: uuid.UUID, org_id: uuid.UUID) -> str:
        vuln = (
            db.query(Vulnerability)
            .filter(Vulnerability.id == vuln_id, Vulnerability.organization_id == org_id)
            .first()
        )
        if not vuln:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "message": f"Vulnerability '{vuln_id}' was not found.", "details": []}},
            )

        cve = db.query(CVE).filter(CVE.id == vuln.cve_id).first()
        device = db.query(Device).filter(Device.id == vuln.device_id).first()

        device_name = f"{device.ip_address} ({device.hostname or 'unnamed'})" if device else "Unspecified Device"
        cve_id = cve.cve_id if cve else "Unknown CVE"
        cvss = cve.cvss_score if cve and cve.cvss_score is not None else "N/A"
        service = cve.affected_service if cve and cve.affected_service else "system service"
        version = cve.affected_version if cve and cve.affected_version else "detected version"
        summary = cve.summary if cve and cve.summary else vuln.description
        rec = cve.recommendation if cve and cve.recommendation else vuln.recommendation

        sections = [
            f"### [CyberShield AI Vulnerability Brief — {cve_id}]",
            f"**Severity:** {vuln.severity} | **CVSS Base Score:** {cvss} | **Status:** {vuln.status}",
            f"**Vulnerable Host:** {device_name}",
            f"**Software Component:** `{service}` (version `{version}`)",
            "",
            "#### 1. Technical Vulnerability Summary",
            summary or "No CVE technical summary available in local database seed.",
            "",
            "#### 2. Risk Exposure & Attack Vector",
            f"- Asset `{device_name}` is actively exposing `{service}` vulnerable to `{cve_id}`.",
            f"- If unpatched, remote attackers can exploit known weaknesses to execute arbitrary commands, "
            f"bypass authorization, or induce service failure.",
            "",
            "#### 3. Recommended Remediation Strategy",
            rec or f"Upgrade `{service}` to the latest stable release or apply the vendor security advisory patch.",
            "- **Workaround:** If immediate patching is not possible, restrict ingress access to the service port using network access control lists (ACLs) or local firewall rules.",
            "- **Verification:** Re-run an agent vulnerability scan against the target device after patching to confirm resolution.",
        ]

        return "\n".join(sections)

    def explain_risk_score(self, db: Session, device_id: uuid.UUID, org_id: uuid.UUID) -> str:
        device = (
            db.query(Device)
            .filter(Device.id == device_id, Device.organization_id == org_id)
            .first()
        )
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "message": f"Device '{device_id}' was not found.", "details": []}},
            )

        # Retrieve risk score record or calculate on the fly
        risk = (
            db.query(RiskScore)
            .filter(
                RiskScore.organization_id == org_id,
                RiskScore.entity_type == "device",
                RiskScore.entity_id == device_id,
            )
            .order_by(RiskScore.created_at.desc())
            .first()
        )

        breakdown = {}
        score = 0.0
        band = "Low"

        if risk and risk.factor_breakdown:
            try:
                breakdown = json.loads(risk.factor_breakdown) if isinstance(risk.factor_breakdown, str) else risk.factor_breakdown
                score = float(risk.score)
                band = risk.risk_band
            except Exception:
                pass

        if not risk or not breakdown:
            from app.services.risk_service import calculate_device_risk
            risk_obj = calculate_device_risk(db, device_id=device_id, org_id=org_id)
            score = float(risk_obj.score)
            band = risk_obj.risk_band
            try:
                breakdown = json.loads(risk_obj.factor_breakdown) if isinstance(risk_obj.factor_breakdown, str) else risk_obj.factor_breakdown
            except Exception:
                breakdown = {}

        vuln_pts = breakdown.get("vulnerabilities", {}).get("total_points", 0)
        alert_pts = breakdown.get("alerts", {}).get("total_points", 0)
        exposure_pts = breakdown.get("exposure", {}).get("total_points", 0)
        open_ports_count = breakdown.get("exposure", {}).get("open_ports_count", 0)
        open_alerts_count = breakdown.get("alerts", {}).get("open_alerts_count", 0)
        vuln_counts = breakdown.get("vulnerabilities", {}).get("counts", {})

        sections = [
            f"### [CyberShield AI Device Risk Assessment — {device.ip_address}]",
            f"**Hostname:** {device.hostname or 'N/A'} | **Overall Score:** {score}/100 | **Risk Band:** {band}",
            "",
            "#### 1. Quantified Factor Breakdown",
            f"- **Vulnerabilities Contribution:** **{vuln_pts} pts** (Max cap: 80)",
            f"  - Critical: {vuln_counts.get('critical', 0)} (+30 pts ea, max 30)",
            f"  - High: {vuln_counts.get('high', 0)} (+15 pts ea, max 30)",
            f"  - Medium: {vuln_counts.get('medium', 0)} (+5 pts ea, max 15)",
            f"  - Low: {vuln_counts.get('low', 0)} (+2 pts ea, max 5)",
            f"- **Active Alerts Contribution:** **{alert_pts} pts** (Max cap: 45)",
            f"  - {open_alerts_count} active Open/Acknowledged threat alerts on device.",
            f"- **Network Exposure Contribution:** **{exposure_pts} pts** (Max cap: 10)",
            f"  - {open_ports_count} open listening ports discovered by network scanning.",
            "",
            "#### 2. Risk Evaluation & Analysis",
        ]

        if band == "Critical":
            sections.append(
                "This device is in the **CRITICAL** risk band (score >= 75). Immediate incident response action is required. "
                "The host exhibits high-severity vulnerabilities and/or unresolved active threat alerts that expose the organization "
                "to probable exploitation."
            )
        elif band == "High":
            sections.append(
                "This device is in the **HIGH** risk band (score 50–74). Remediate top vulnerabilities and investigate active alerts "
                "to prevent compromise."
            )
        elif band == "Medium":
            sections.append(
                "This device is in the **MEDIUM** risk band (score 25–49). Moderate risk profile driven by medium-severity findings "
                "or open ports. Schedule routine patching."
            )
        else:
            sections.append(
                "This device is in the **LOW** risk band (score 0–24). The device maintains an acceptable security posture with no "
                "critical unpatched vulnerabilities or active threat alerts."
            )

        sections.extend([
            "",
            "#### 3. How to Reduce This Device's Risk Score",
            "1. **Remediate Critical & High Vulnerabilities:** Patching the top vulnerabilities directly eliminates up to 60 risk points.",
            "2. **Triage & Resolve Active Alerts:** Investigating and resolving open brute force or IOC alerts deducts active alert penalties.",
            "3. **Close Unnecessary Services:** Disabling unused listening services to bring open ports under 10 eliminates the 10-point exposure penalty.",
        ])

        return "\n".join(sections)

    def chat(
        self,
        db: Session,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
        context_type: str,
        context_id: uuid.UUID,
    ) -> Tuple[AIConversation, str]:
        """
        Handle a conversational query, mapping to local rules and saving conversation history.
        """
        clean_context_type = context_type.lower().strip()

        # Find or create conversation for this context
        conversation = (
            db.query(AIConversation)
            .filter(
                AIConversation.organization_id == org_id,
                AIConversation.user_id == user_id,
                AIConversation.subject_type == clean_context_type,
                AIConversation.subject_id == context_id,
            )
            .order_by(AIConversation.created_at.desc())
            .first()
        )

        if not conversation:
            conversation = AIConversation(
                organization_id=org_id,
                user_id=user_id,
                subject_type=clean_context_type,
                subject_id=context_id,
                provider_type=self.PROVIDER_NAME,
            )
            db.add(conversation)
            db.flush()

        # Save user message
        user_msg = AIMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        db.add(user_msg)

        # Generate rule-based response
        response_text = ""
        try:
            if clean_context_type == "alert":
                base_explanation = self.explain_alert(db, alert_id=context_id, org_id=org_id)
                response_text = f"{base_explanation}\n\n*Response to inquiry: '{message}':* Follow the triage playbook above to secure the asset."
            elif clean_context_type == "vulnerability":
                base_explanation = self.explain_vulnerability(db, vuln_id=context_id, org_id=org_id)
                response_text = f"{base_explanation}\n\n*Response to inquiry: '{message}':* Prioritize vendor updates for the affected component."
            elif clean_context_type in ("risk", "device"):
                base_explanation = self.explain_risk_score(db, device_id=context_id, org_id=org_id)
                response_text = f"{base_explanation}\n\n*Response to inquiry: '{message}':* Implement the reduction recommendations to decrease risk score."
            else:
                response_text = (
                    f"CyberShield AI Local Explanation Engine received inquiry for context '{clean_context_type}' ({context_id}): "
                    f"'{message}'. All system security rules are evaluated locally based on database findings."
                )
        except HTTPException as e:
            response_text = f"Context lookup note: {e.detail.get('error', {}).get('message', str(e.detail)) if isinstance(e.detail, dict) else str(e.detail)}"

        # Save assistant message
        assistant_msg = AIMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
        )
        db.add(assistant_msg)

        db.commit()
        db.refresh(conversation)

        return conversation, response_text


# Global engine singleton
ai_engine = LocalRuleAI()
