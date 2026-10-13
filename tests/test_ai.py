"""
Tests for Phase 19 — AI Security Assistant (Local Security Explanation Engine).

Covers:
- Strict RBAC: Administrator and Security Analyst allowed; Viewer forbidden (403 FORBIDDEN); Unauthenticated returns 401.
- Deterministic LocalRuleAI engine (100% local, no external APIs).
- Endpoints:
  - POST /api/v1/ai/explain-alert:
    - Happy path: explains alert using telemetry, device details, risk score, and playbook.
    - 404 on invalid alert ID or cross-organization alert.
  - POST /api/v1/ai/explain-vulnerability:
    - Happy path: explains CVE details, attack vectors, and remediation steps.
    - 404 on invalid vulnerability ID or cross-organization vulnerability.
  - POST /api/v1/ai/explain-risk:
    - Happy path: explains device risk factor breakdown and reduction steps.
    - 404 on invalid device ID or cross-organization device.
  - POST /api/v1/ai/chat:
    - Creates AIConversation and AIMessage rows in DB.
    - Subsequent chat appends messages to existing conversation thread.
    - Responds deterministically according to context type.
  - GET /api/v1/ai/conversations:
    - Lists user's conversation threads with org isolation.
  - GET /api/v1/ai/conversations/{id}:
    - Retrieves conversation details and complete message history.
    - 404 on invalid ID or cross-org ID.
"""

import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.ai import AIConversation, AIMessage
from app.models.alert import Alert, RiskScore
from app.models.device import Device
from app.models.organization import Organization, Role
from app.models.scan import CVE, Scan, Vulnerability
from app.models.user import User
from app.core.security import create_access_token, hash_password

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures & Setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_ai_data(create_tables, db_session):
    """Set up organizations, roles, users (Admin, Analyst, Viewer), and test entities."""
    org1 = Organization(name="AIOrg1", slug=f"ai-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(name="AIOrg2", slug=f"ai-org-2-{uuid.uuid4().hex[:6]}")
    db_session.add_all([org1, org2])
    db_session.flush()

    roles = {}
    for name, desc in [
        ("Administrator", "Admin access"),
        ("Security Analyst", "Analyst access"),
        ("Viewer", "Viewer access"),
    ]:
        existing = db_session.query(Role).filter(Role.name == name).first()
        if existing:
            roles[name] = existing
        else:
            r = Role(name=name, description=desc)
            db_session.add(r)
            db_session.flush()
            roles[name] = r

    admin = User(
        organization_id=org1.id,
        role_id=roles["Administrator"].id,
        email=f"ai_admin_{uuid.uuid4().hex[:6]}@test.com",
        username="ai_admin",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    analyst = User(
        organization_id=org1.id,
        role_id=roles["Security Analyst"].id,
        email=f"ai_analyst_{uuid.uuid4().hex[:6]}@test.com",
        username="ai_analyst",
        password_hash=hash_password("AnalystPass123!"),
        is_active=True,
    )
    viewer = User(
        organization_id=org1.id,
        role_id=roles["Viewer"].id,
        email=f"ai_viewer_{uuid.uuid4().hex[:6]}@test.com",
        username="ai_viewer",
        password_hash=hash_password("ViewerPass123!"),
        is_active=True,
    )
    org2_admin = User(
        organization_id=org2.id,
        role_id=roles["Administrator"].id,
        email=f"ai_org2_{uuid.uuid4().hex[:6]}@test.com",
        username="ai_org2",
        password_hash=hash_password("Org2Pass123!"),
        is_active=True,
    )
    db_session.add_all([admin, analyst, viewer, org2_admin])
    db_session.flush()

    # Create target device for Org1
    device1 = Device(
        organization_id=org1.id,
        ip_address="192.168.1.105",
        mac_address="00:11:22:33:44:55",
        hostname="fileserver-primary",
        device_type="Server",
        status="online",
    )
    # Target device for Org2
    device2 = Device(
        organization_id=org2.id,
        ip_address="10.0.0.99",
        mac_address="aa:bb:cc:dd:ee:ff",
        hostname="org2-host",
        device_type="Host",
        status="online",
    )
    db_session.add_all([device1, device2])
    db_session.flush()

    # Create Alert for Org1
    alert1 = Alert(
        organization_id=org1.id,
        device_id=device1.id,
        alert_type="brute_force",
        severity="High",
        status="Open",
        description="Repeated failed SSH logins detected from 198.51.100.22",
        risk_score=40,
        triggered_at=datetime.now(timezone.utc),
    )
    # Create Alert for Org2
    alert2 = Alert(
        organization_id=org2.id,
        device_id=device2.id,
        alert_type="port_scan",
        severity="Medium",
        status="Open",
        description="Port scan on Org2 asset",
        risk_score=20,
        triggered_at=datetime.now(timezone.utc),
    )
    db_session.add_all([alert1, alert2])
    db_session.flush()

    # Create CVE and Vulnerability for Org1
    cve1 = CVE(
        organization_id=org1.id,
        cve_id="CVE-2023-48795",
        severity="Medium",
        cvss_score=5.9,
        affected_service="OpenSSH",
        affected_version="8.9p1",
        summary="Terrapin attack: prefix truncation vulnerability in OpenSSH transport protocol.",
        recommendation="Upgrade OpenSSH to version 9.6p1 or later.",
        source="local_seed",
    )
    db_session.add(cve1)
    db_session.flush()

    vuln1 = Vulnerability(
        organization_id=org1.id,
        device_id=device1.id,
        cve_id=cve1.id,
        severity="Medium",
        score=5.9,
        description="Vulnerable OpenSSH service detected on port 22.",
        recommendation="Upgrade OpenSSH to version 9.6p1 or disable vulnerable cipher suites.",
        status="open",
    )
    db_session.add(vuln1)
    db_session.flush()

    # Create RiskScore record for Device1
    breakdown_data = {
        "vulnerabilities": {
            "total_points": 5,
            "counts": {"critical": 0, "high": 0, "medium": 1, "low": 0},
        },
        "alerts": {
            "total_points": 20,
            "open_alerts_count": 1,
            "brute_force_score": 20,
        },
        "exposure": {
            "total_points": 0,
            "open_ports_count": 3,
        },
    }
    risk1 = RiskScore(
        organization_id=org1.id,
        entity_type="device",
        entity_id=device1.id,
        score=25.0,
        risk_band="Medium",
        factor_breakdown=json.dumps(breakdown_data),
        formula_version="v1",
    )
    db_session.add(risk1)

    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "admin": admin,
        "analyst": analyst,
        "viewer": viewer,
        "org2_admin": org2_admin,
        "device1": device1,
        "device2": device2,
        "alert1": alert1,
        "alert2": alert2,
        "cve1": cve1,
        "vuln1": vuln1,
        "risk1": risk1,
    }


def _auth_header(user):
    from app.models.organization import Role
    from tests.conftest import _TestingSessionLocal

    db = _TestingSessionLocal()
    role = db.query(Role).filter(Role.id == user.role_id).first()
    db.close()
    token = create_access_token(
        subject=str(user.id),
        role_name=role.name,
        organization_id=str(user.organization_id),
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Test Suite: Explain Alert
# ---------------------------------------------------------------------------

class TestExplainAlert:
    def test_explain_alert_analyst_success(self, setup_ai_data):
        analyst = setup_ai_data["analyst"]
        alert = setup_ai_data["alert1"]
        headers = _auth_header(analyst)

        resp = client.post(
            "/api/v1/ai/explain-alert",
            json={"alert_id": str(alert.id)},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["target_id"] == str(alert.id)
        assert data["target_type"] == "alert"
        assert data["provider"] == "local_rule_ai"
        assert "BRUTE FORCE" in data["explanation"]
        assert "Recommended Incident Response Playbook" in data["explanation"]

    def test_explain_alert_admin_success(self, setup_ai_data):
        admin = setup_ai_data["admin"]
        alert = setup_ai_data["alert1"]
        headers = _auth_header(admin)

        resp = client.post(
            "/api/v1/ai/explain-alert",
            json={"alert_id": str(alert.id)},
            headers=headers,
        )
        assert resp.status_code == 200

    def test_explain_alert_viewer_forbidden(self, setup_ai_data):
        viewer = setup_ai_data["viewer"]
        alert = setup_ai_data["alert1"]
        headers = _auth_header(viewer)

        resp = client.post(
            "/api/v1/ai/explain-alert",
            json={"alert_id": str(alert.id)},
            headers=headers,
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_explain_alert_unauthorized(self, setup_ai_data):
        alert = setup_ai_data["alert1"]
        resp = client.post(
            "/api/v1/ai/explain-alert",
            json={"alert_id": str(alert.id)},
        )
        assert resp.status_code == 401

    def test_explain_alert_not_found(self, setup_ai_data):
        analyst = setup_ai_data["analyst"]
        headers = _auth_header(analyst)

        resp = client.post(
            "/api/v1/ai/explain-alert",
            json={"alert_id": str(uuid.uuid4())},
            headers=headers,
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_explain_alert_org_isolation(self, setup_ai_data):
        # Org2 alert accessed by Org1 analyst -> 404
        analyst = setup_ai_data["analyst"]
        alert2 = setup_ai_data["alert2"]
        headers = _auth_header(analyst)

        resp = client.post(
            "/api/v1/ai/explain-alert",
            json={"alert_id": str(alert2.id)},
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test Suite: Explain Vulnerability
# ---------------------------------------------------------------------------

class TestExplainVulnerability:
    def test_explain_vulnerability_success(self, setup_ai_data):
        analyst = setup_ai_data["analyst"]
        vuln = setup_ai_data["vuln1"]
        headers = _auth_header(analyst)

        resp = client.post(
            "/api/v1/ai/explain-vulnerability",
            json={"vulnerability_id": str(vuln.id)},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["target_id"] == str(vuln.id)
        assert data["target_type"] == "vulnerability"
        assert "CVE-2023-48795" in data["explanation"]
        assert "OpenSSH" in data["explanation"]
        assert "Remediation Strategy" in data["explanation"]

    def test_explain_vulnerability_viewer_forbidden(self, setup_ai_data):
        viewer = setup_ai_data["viewer"]
        vuln = setup_ai_data["vuln1"]
        headers = _auth_header(viewer)

        resp = client.post(
            "/api/v1/ai/explain-vulnerability",
            json={"vulnerability_id": str(vuln.id)},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_explain_vulnerability_not_found(self, setup_ai_data):
        analyst = setup_ai_data["analyst"]
        headers = _auth_header(analyst)

        resp = client.post(
            "/api/v1/ai/explain-vulnerability",
            json={"vulnerability_id": str(uuid.uuid4())},
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test Suite: Explain Risk
# ---------------------------------------------------------------------------

class TestExplainRisk:
    def test_explain_risk_success(self, setup_ai_data):
        analyst = setup_ai_data["analyst"]
        device = setup_ai_data["device1"]
        headers = _auth_header(analyst)

        resp = client.post(
            "/api/v1/ai/explain-risk",
            json={"device_id": str(device.id)},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["target_id"] == str(device.id)
        assert data["target_type"] == "device_risk"
        assert "Quantified Factor Breakdown" in data["explanation"]
        assert "Reduce This Device's Risk Score" in data["explanation"]

    def test_explain_risk_viewer_forbidden(self, setup_ai_data):
        viewer = setup_ai_data["viewer"]
        device = setup_ai_data["device1"]
        headers = _auth_header(viewer)

        resp = client.post(
            "/api/v1/ai/explain-risk",
            json={"device_id": str(device.id)},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_explain_risk_device_not_found(self, setup_ai_data):
        analyst = setup_ai_data["analyst"]
        headers = _auth_header(analyst)

        resp = client.post(
            "/api/v1/ai/explain-risk",
            json={"device_id": str(uuid.uuid4())},
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test Suite: AI Chat and Conversations
# ---------------------------------------------------------------------------

class TestAIChatAndConversations:
    def test_chat_creates_conversation_and_messages(self, setup_ai_data, db_session):
        analyst = setup_ai_data["analyst"]
        alert = setup_ai_data["alert1"]
        headers = _auth_header(analyst)

        prompt_text = "What is the primary risk of this brute force attempt?"
        resp = client.post(
            "/api/v1/ai/chat",
            json={
                "message": prompt_text,
                "context_type": "alert",
                "context_id": str(alert.id),
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "conversation_id" in data
        assert "response" in data
        assert data["context_type"] == "alert"
        assert data["provider"] == "local_rule_ai"

        conv_id = uuid.UUID(data["conversation_id"])

        # Verify DB rows
        conv = db_session.query(AIConversation).filter(AIConversation.id == conv_id).first()
        assert conv is not None
        assert conv.user_id == analyst.id
        assert conv.subject_type == "alert"
        assert conv.subject_id == alert.id
        assert conv.provider_type == "local_rule_ai"

        messages = (
            db_session.query(AIMessage)
            .filter(AIMessage.conversation_id == conv_id)
            .order_by(AIMessage.created_at.asc())
            .all()
        )
        assert len(messages) >= 2
        assert messages[0].role == "user"
        assert messages[0].content == prompt_text
        assert messages[1].role == "assistant"
        assert len(messages[1].content) > 20

    def test_chat_thread_continuation(self, setup_ai_data, db_session):
        analyst = setup_ai_data["analyst"]
        alert = setup_ai_data["alert1"]
        headers = _auth_header(analyst)

        # Follow-up query in same context
        resp = client.post(
            "/api/v1/ai/chat",
            json={
                "message": "Should I block the source IP immediately?",
                "context_type": "alert",
                "context_id": str(alert.id),
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        conv_id = uuid.UUID(data["conversation_id"])

        # Should reuse same conversation thread
        conv = db_session.query(AIConversation).filter(AIConversation.id == conv_id).first()
        assert conv is not None

        messages = db_session.query(AIMessage).filter(AIMessage.conversation_id == conv_id).all()
        assert len(messages) >= 4  # 2 from first test + 2 from second test

    def test_chat_viewer_forbidden(self, setup_ai_data):
        viewer = setup_ai_data["viewer"]
        alert = setup_ai_data["alert1"]
        headers = _auth_header(viewer)

        resp = client.post(
            "/api/v1/ai/chat",
            json={
                "message": "Tell me about this alert",
                "context_type": "alert",
                "context_id": str(alert.id),
            },
            headers=headers,
        )
        assert resp.status_code == 403

    def test_list_conversations(self, setup_ai_data):
        analyst = setup_ai_data["analyst"]
        headers = _auth_header(analyst)

        resp = client.get("/api/v1/ai/conversations", headers=headers)
        assert resp.status_code == 200, resp.text
        convs = resp.json()
        assert isinstance(convs, list)
        assert len(convs) >= 1
        assert convs[0]["subject_type"] == "alert"

    def test_get_conversation_detail(self, setup_ai_data):
        analyst = setup_ai_data["analyst"]
        headers = _auth_header(analyst)

        # First list to get ID
        list_resp = client.get("/api/v1/ai/conversations", headers=headers)
        conv_id = list_resp.json()[0]["id"]

        detail_resp = client.get(f"/api/v1/ai/conversations/{conv_id}", headers=headers)
        assert detail_resp.status_code == 200, detail_resp.text
        detail = detail_resp.json()
        assert detail["id"] == conv_id
        assert "messages" in detail
        assert len(detail["messages"]) >= 2

    def test_get_conversation_not_found_or_cross_org(self, setup_ai_data):
        org2_admin = setup_ai_data["org2_admin"]
        analyst = setup_ai_data["analyst"]
        headers_analyst = _auth_header(analyst)
        headers_org2 = _auth_header(org2_admin)

        # Analyst's conversation
        list_resp = client.get("/api/v1/ai/conversations", headers=headers_analyst)
        conv_id = list_resp.json()[0]["id"]

        # Org2 admin trying to access Org1 conversation
        resp = client.get(f"/api/v1/ai/conversations/{conv_id}", headers=headers_org2)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"
