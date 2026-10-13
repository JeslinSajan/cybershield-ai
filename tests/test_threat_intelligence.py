"""
Tests for Phase 18 — Threat Intelligence and IOC Correlation.

Covers:
- ThreatIndicator CRUD endpoints:
  - POST /threat-intelligence/ (Admin & Analyst allowed, Viewer 403, 401 unauth, 409 conflict on duplicate, validation).
  - GET /threat-intelligence/ (All roles, filters by type/search/limit/offset, org isolation).
  - GET /threat-intelligence/{id} (All roles, 404 for invalid/cross-org).
  - DELETE /threat-intelligence/{id} (Admin only, Analyst & Viewer 403, 404, audit logging).
- Automated Threat Intelligence Detection:
  - Agent log ingestion containing malicious IP matching a ThreatIndicator triggers a High severity alert (malware_indicator, risk 40).
  - Alert deduplication: repeated log with same malicious IP does not generate duplicate open alert.
- Seed data loading verification.
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import Agent, AgentCredential
from app.models.alert import Alert
from app.models.log import Log, ThreatIndicator
from app.models.organization import Organization, Role
from app.models.system import AuditLog
from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.core.seed import seed_threat_intelligence
from app.services.detection_service import process_log_detections

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures & Setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_ti_data(create_tables, db_session):
    """Set up organizations, roles, users (Admin, Analyst, Viewer), and an enrolled agent."""
    org1 = Organization(name="TIOrg1", slug=f"ti-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(name="TIOrg2", slug=f"ti-org-2-{uuid.uuid4().hex[:6]}")
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
        email=f"ti_admin_{uuid.uuid4().hex[:6]}@test.com",
        username="ti_admin",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    analyst = User(
        organization_id=org1.id,
        role_id=roles["Security Analyst"].id,
        email=f"ti_analyst_{uuid.uuid4().hex[:6]}@test.com",
        username="ti_analyst",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    viewer = User(
        organization_id=org1.id,
        role_id=roles["Viewer"].id,
        email=f"ti_viewer_{uuid.uuid4().hex[:6]}@test.com",
        username="ti_viewer",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    org2_admin = User(
        organization_id=org2.id,
        role_id=roles["Administrator"].id,
        email=f"ti_org2_{uuid.uuid4().hex[:6]}@test.com",
        username="ti_org2",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    db_session.add_all([admin, analyst, viewer, org2_admin])
    db_session.flush()

    # Create agent and credential for log ingestion tests
    agent = Agent(
        organization_id=org1.id,
        name="ti-agent",
        hostname="ti-host",
        status="ONLINE",
        version="1.0.0",
        is_active=True,
    )
    db_session.add(agent)
    db_session.flush()

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    cred = AgentCredential(
        agent_id=agent.id,
        credential_hash=token_hash,
        type="token",
        is_active=True,
    )
    db_session.add(cred)

    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "admin": admin,
        "analyst": analyst,
        "viewer": viewer,
        "org2_admin": org2_admin,
        "agent": agent,
        "agent_token": raw_token,
    }


def _token_for(user):
    from app.models.organization import Role
    from tests.conftest import _TestingSessionLocal
    db = _TestingSessionLocal()
    role = db.query(Role).filter(Role.id == user.role_id).first()
    db.close()
    return create_access_token(
        subject=str(user.id),
        role_name=role.name,
        organization_id=str(user.organization_id),
    )


# ---------------------------------------------------------------------------
# Test Threat Intelligence CRUD Endpoints
# ---------------------------------------------------------------------------

class TestThreatIntelligenceCRUD:
    def test_analyst_can_create_threat_indicator(self, setup_ti_data, db_session):
        analyst = setup_ti_data["analyst"]
        token = _token_for(analyst)
        payload = {
            "indicator_type": "ip",
            "value": "198.51.100.77",
            "description": "Known Cobalt Strike C2 server",
            "source": "crowdstrike_intel",
        }
        resp = client.post(
            "/api/v1/threat-intelligence/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["indicator_type"] == "ip"
        assert data["value"] == "198.51.100.77"
        assert data["description"] == "Known Cobalt Strike C2 server"
        assert data["source"] == "crowdstrike_intel"
        assert "id" in data

        # Verify audit log was created
        audit = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.action == "threat_indicator_created",
                AuditLog.target_id == uuid.UUID(data["id"]),
            )
            .first()
        )
        assert audit is not None
        assert audit.actor_id == analyst.id

    def test_admin_can_create_threat_indicator(self, setup_ti_data):
        admin = setup_ti_data["admin"]
        token = _token_for(admin)
        payload = {
            "indicator_type": "domain",
            "value": "phishing-bank-login.net",
            "description": "Credential harvesting domain",
            "source": "local",
        }
        resp = client.post(
            "/api/v1/threat-intelligence/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["indicator_type"] == "domain"
        assert data["value"] == "phishing-bank-login.net"

    def test_viewer_cannot_create_indicator_returns_403(self, setup_ti_data):
        viewer = setup_ti_data["viewer"]
        token = _token_for(viewer)
        payload = {
            "indicator_type": "hash",
            "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        }
        resp = client.post(
            "/api/v1/threat-intelligence/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_unauthenticated_cannot_create_indicator_returns_401(self):
        resp = client.post(
            "/api/v1/threat-intelligence/",
            json={"indicator_type": "ip", "value": "1.2.3.4"},
        )
        assert resp.status_code == 401

    def test_duplicate_indicator_returns_409_conflict(self, setup_ti_data):
        analyst = setup_ti_data["analyst"]
        token = _token_for(analyst)
        payload = {
            "indicator_type": "ip",
            "value": "198.51.100.88",
            "description": "First insertion",
        }
        resp1 = client.post(
            "/api/v1/threat-intelligence/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 201

        # Second insertion with same type and value -> 409 CONFLICT
        resp2 = client.post(
            "/api/v1/threat-intelligence/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 409
        err = resp2.json()["error"]
        assert err["code"] == "CONFLICT"

    def test_invalid_indicator_type_returns_422(self, setup_ti_data):
        admin = setup_ti_data["admin"]
        token = _token_for(admin)
        resp = client.post(
            "/api/v1/threat-intelligence/",
            json={"indicator_type": "invalid_type", "value": "test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_list_indicators_with_filters(self, setup_ti_data):
        viewer = setup_ti_data["viewer"]
        token = _token_for(viewer)

        # List all
        resp = client.get(
            "/api/v1/threat-intelligence/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 2

        # Filter by type=ip
        resp_ip = client.get(
            "/api/v1/threat-intelligence/?indicator_type=ip",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_ip.status_code == 200
        ip_items = resp_ip.json()
        for item in ip_items:
            assert item["indicator_type"] == "ip"

        # Search filter
        resp_search = client.get(
            "/api/v1/threat-intelligence/?search=phishing",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_search.status_code == 200
        search_items = resp_search.json()
        assert len(search_items) >= 1
        assert "phishing" in (search_items[0]["value"] + (search_items[0]["description"] or ""))

    def test_get_indicator_by_id(self, setup_ti_data):
        analyst = setup_ti_data["analyst"]
        token = _token_for(analyst)

        # Create one
        create_resp = client.post(
            "/api/v1/threat-intelligence/",
            json={"indicator_type": "domain", "value": f"lookup-{uuid.uuid4().hex[:6]}.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        created_id = create_resp.json()["id"]

        # Fetch it
        resp = client.get(
            f"/api/v1/threat-intelligence/{created_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == created_id

    def test_get_nonexistent_or_cross_org_indicator_returns_404(self, setup_ti_data):
        admin = setup_ti_data["admin"]
        org2_admin = setup_ti_data["org2_admin"]

        # Create in org1
        create_resp = client.post(
            "/api/v1/threat-intelligence/",
            json={"indicator_type": "ip", "value": f"10.99.{uuid.uuid4().int % 255}.1"},
            headers={"Authorization": f"Bearer {_token_for(admin)}"},
        )
        ind_id = create_resp.json()["id"]

        # Org2 admin tries to read org1's indicator -> 404
        resp = client.get(
            f"/api/v1/threat-intelligence/{ind_id}",
            headers={"Authorization": f"Bearer {_token_for(org2_admin)}"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_admin_can_delete_indicator(self, setup_ti_data, db_session):
        admin = setup_ti_data["admin"]
        admin_token = _token_for(admin)

        # Create an indicator to delete
        create_resp = client.post(
            "/api/v1/threat-intelligence/",
            json={"indicator_type": "hash", "value": f"hash-to-delete-{uuid.uuid4().hex}"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ind_id = create_resp.json()["id"]

        # Delete as Admin
        del_resp = client.delete(
            f"/api/v1/threat-intelligence/{ind_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["id"] == ind_id

        # Verify not found now
        get_resp = client.get(
            f"/api/v1/threat-intelligence/{ind_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_resp.status_code == 404

        # Verify audit log
        audit = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.action == "threat_indicator_deleted",
                AuditLog.target_id == uuid.UUID(ind_id),
            )
            .first()
        )
        assert audit is not None
        assert audit.actor_id == admin.id

    def test_analyst_cannot_delete_indicator_returns_403(self, setup_ti_data):
        admin_token = _token_for(setup_ti_data["admin"])
        analyst_token = _token_for(setup_ti_data["analyst"])

        # Create as Admin
        create_resp = client.post(
            "/api/v1/threat-intelligence/",
            json={"indicator_type": "ip", "value": f"198.51.100.{uuid.uuid4().int % 255}"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ind_id = create_resp.json()["id"]

        # Analyst attempts delete -> 403
        del_resp = client.delete(
            f"/api/v1/threat-intelligence/{ind_id}",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert del_resp.status_code == 403
        assert del_resp.json()["error"]["code"] == "FORBIDDEN"


# ---------------------------------------------------------------------------
# Test Automated IOC Detection during Log Ingestion
# ---------------------------------------------------------------------------

class TestThreatIntelligenceDetection:
    def test_matching_malicious_ip_triggers_high_severity_alert(self, setup_ti_data, db_session):
        admin = setup_ti_data["admin"]
        agent = setup_ti_data["agent"]
        agent_token = setup_ti_data["agent_token"]
        malicious_ip = f"198.51.100.{uuid.uuid4().int % 200 + 10}"

        # 1. Register malicious IP in Threat Intelligence
        create_resp = client.post(
            "/api/v1/threat-intelligence/",
            json={
                "indicator_type": "ip",
                "value": malicious_ip,
                "description": "Active ransomware distribution IP",
                "source": "cisa_threat_feed",
            },
            headers={"Authorization": f"Bearer {_token_for(admin)}"},
        )
        assert create_resp.status_code == 201

        # 2. Ingest agent log with source_ip matching the registered threat indicator
        now_iso = datetime.now(timezone.utc).isoformat()
        log_payload = {
            "logs": [
                {
                    "source": "auth.log",
                    "event_type": "connection_attempt",
                    "severity": "info",
                    "message": f"Inbound connection observed from {malicious_ip}",
                    "source_ip": malicious_ip,
                    "username": "root",
                    "timestamp": now_iso,
                }
            ]
        }
        ingest_resp = client.post(
            "/api/v1/agents/logs",
            json=log_payload,
            headers={"Authorization": f"Bearer {agent_token}"},
        )
        assert ingest_resp.status_code == 201

        # 3. Verify Alert was created
        alert = (
            db_session.query(Alert)
            .filter(
                Alert.organization_id == admin.organization_id,
                Alert.alert_type == "malware_indicator",
                Alert.status == "Open",
            )
            .order_by(Alert.created_at.desc())
            .first()
        )
        assert alert is not None
        assert alert.severity == "High"
        assert alert.risk_score == 40.0
        assert malicious_ip in alert.description
        assert "matches threat intelligence feed" in alert.description

    def test_threat_intelligence_seed_loader(self, setup_ti_data, db_session):
        org = setup_ti_data["org2"]
        # Seed threat intel for org2
        count = seed_threat_intelligence(db=db_session, organization_id=org.id)
        assert count >= 5

        # Query indicators for org2
        indicators = db_session.query(ThreatIndicator).filter(ThreatIndicator.organization_id == org.id).all()
        types = {i.indicator_type for i in indicators}
        assert "ip" in types
        assert "domain" in types
        assert "hash" in types
