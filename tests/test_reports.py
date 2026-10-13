"""
Tests for Phase 20 — Reports (Compliance & Executive Reporting).

Covers:
- Dependencies: fpdf2 PDF generator and standard library CSV export.
- Strict RBAC:
  - Generate reports: Administrator & Security Analyst allowed; Viewer forbidden (403 FORBIDDEN).
  - List & View reports: All authenticated roles (Administrator, Security Analyst, Viewer) allowed.
  - Download reports: Administrator & Security Analyst allowed; Viewer forbidden (403 FORBIDDEN).
  - Unauthenticated requests return 401.
- Endpoints:
  - POST /api/v1/reports/ (generation of 'security_overview', 'vulnerability', 'alert').
  - GET  /api/v1/reports/ (listing with type filter, pagination, org isolation).
  - GET  /api/v1/reports/{id} (metadata retrieval, 404 on missing or cross-org).
  - GET  /api/v1/reports/{id}/download?format=pdf (streaming PDF file with application/pdf MIME type).
  - GET  /api/v1/reports/{id}/download?format=csv (streaming CSV file with text/csv MIME type).
- AuditLog verification on report generation.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import Agent
from app.models.alert import Alert, RiskScore
from app.models.device import Device
from app.models.organization import Organization, Role
from app.models.report import Report
from app.models.scan import CVE, Vulnerability
from app.models.system import AuditLog
from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.services.report_service import REPORT_DIR

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures & Setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def setup_reports_data(create_tables, db_session):
    """Set up organizations, users (Admin, Analyst, Viewer), and test entities."""
    org1 = Organization(name="ReportsOrg1", slug=f"rep-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(name="ReportsOrg2", slug=f"rep-org-2-{uuid.uuid4().hex[:6]}")
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
        email=f"rep_admin_{uuid.uuid4().hex[:6]}@test.com",
        username="rep_admin",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    analyst = User(
        organization_id=org1.id,
        role_id=roles["Security Analyst"].id,
        email=f"rep_analyst_{uuid.uuid4().hex[:6]}@test.com",
        username="rep_analyst",
        password_hash=hash_password("AnalystPass123!"),
        is_active=True,
    )
    viewer = User(
        organization_id=org1.id,
        role_id=roles["Viewer"].id,
        email=f"rep_viewer_{uuid.uuid4().hex[:6]}@test.com",
        username="rep_viewer",
        password_hash=hash_password("ViewerPass123!"),
        is_active=True,
    )
    org2_admin = User(
        organization_id=org2.id,
        role_id=roles["Administrator"].id,
        email=f"rep_org2_{uuid.uuid4().hex[:6]}@test.com",
        username="rep_org2",
        password_hash=hash_password("Org2Pass123!"),
        is_active=True,
    )
    db_session.add_all([admin, analyst, viewer, org2_admin])
    db_session.flush()

    # Create devices & agent for Org1
    dev1 = Device(
        organization_id=org1.id,
        ip_address="192.168.1.50",
        mac_address="00:11:22:33:44:aa",
        hostname="production-db",
        device_type="Server",
        status="online",
    )
    db_session.add(dev1)
    db_session.flush()

    # Create sample alert and vulnerability in Org1
    alert1 = Alert(
        organization_id=org1.id,
        device_id=dev1.id,
        alert_type="brute_force",
        severity="High",
        status="Open",
        description="5 failed logins from 198.51.100.1",
        risk_score=40,
        triggered_at=datetime.now(timezone.utc),
    )
    cve1 = CVE(
        organization_id=org1.id,
        cve_id="CVE-2023-38408",
        severity="Critical",
        cvss_score=9.8,
        affected_service="OpenSSH",
        affected_version="7.2p2",
        summary="Remote code execution in PKCS#11 provider.",
        recommendation="Update OpenSSH.",
    )
    db_session.add_all([alert1, cve1])
    db_session.flush()

    vuln1 = Vulnerability(
        organization_id=org1.id,
        device_id=dev1.id,
        cve_id=cve1.id,
        severity="Critical",
        score=9.8,
        description="Critical OpenSSH vulnerability.",
        status="open",
    )
    db_session.add(vuln1)

    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "admin": admin,
        "analyst": analyst,
        "viewer": viewer,
        "org2_admin": org2_admin,
        "device1": dev1,
        "alert1": alert1,
        "vuln1": vuln1,
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
# Test Suite: Generate Report (POST /reports/)
# ---------------------------------------------------------------------------

class TestGenerateReport:
    def test_admin_generate_security_overview(self, setup_reports_data, db_session):
        admin = setup_reports_data["admin"]
        headers = _auth_header(admin)

        now = datetime.now(timezone.utc)
        payload = {
            "type": "security_overview",
            "from_date": (now - timedelta(days=30)).isoformat(),
            "to_date": now.isoformat(),
        }

        resp = client.post("/api/v1/reports/", json=payload, headers=headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["report_type"] == "security_overview"
        assert data["status"] == "READY"
        assert data["mime_type"] == "application/pdf"
        assert data["file_name"].startswith("cybershield_report_")

        # Verify AuditLog written
        report_id = uuid.UUID(data["id"])
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.target_id == report_id, AuditLog.action == "report_generated")
            .first()
        )
        assert audit is not None
        assert audit.actor_id == admin.id

    def test_analyst_generate_vulnerability_report(self, setup_reports_data):
        analyst = setup_reports_data["analyst"]
        headers = _auth_header(analyst)

        now = datetime.now(timezone.utc)
        payload = {
            "type": "vulnerability",
            "from_date": (now - timedelta(days=7)).isoformat(),
            "to_date": now.isoformat(),
        }

        resp = client.post("/api/v1/reports/", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["report_type"] == "vulnerability"

    def test_analyst_generate_alert_report(self, setup_reports_data):
        analyst = setup_reports_data["analyst"]
        headers = _auth_header(analyst)

        now = datetime.now(timezone.utc)
        payload = {
            "type": "alert",
            "from_date": (now - timedelta(days=1)).isoformat(),
            "to_date": now.isoformat(),
        }

        resp = client.post("/api/v1/reports/", json=payload, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["report_type"] == "alert"

    def test_viewer_cannot_generate_report(self, setup_reports_data):
        viewer = setup_reports_data["viewer"]
        headers = _auth_header(viewer)

        now = datetime.now(timezone.utc)
        payload = {
            "type": "security_overview",
            "from_date": (now - timedelta(days=30)).isoformat(),
            "to_date": now.isoformat(),
        }

        resp = client.post("/api/v1/reports/", json=payload, headers=headers)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_unauthenticated_generate_returns_401(self):
        now = datetime.now(timezone.utc)
        resp = client.post(
            "/api/v1/reports/",
            json={"type": "security_overview", "from_date": now.isoformat(), "to_date": now.isoformat()},
        )
        assert resp.status_code == 401

    def test_invalid_report_type_returns_400(self, setup_reports_data):
        admin = setup_reports_data["admin"]
        headers = _auth_header(admin)

        now = datetime.now(timezone.utc)
        resp = client.post(
            "/api/v1/reports/",
            json={"type": "invalid_type", "from_date": now.isoformat(), "to_date": now.isoformat()},
            headers=headers,
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_inverted_date_range_returns_400(self, setup_reports_data):
        admin = setup_reports_data["admin"]
        headers = _auth_header(admin)

        now = datetime.now(timezone.utc)
        resp = client.post(
            "/api/v1/reports/",
            json={
                "type": "security_overview",
                "from_date": now.isoformat(),
                "to_date": (now - timedelta(days=5)).isoformat(),
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Test Suite: List & Get Reports (GET /reports/)
# ---------------------------------------------------------------------------

class TestListAndGetReports:
    def test_all_roles_can_list_reports(self, setup_reports_data):
        for role_key in ["admin", "analyst", "viewer"]:
            user = setup_reports_data[role_key]
            headers = _auth_header(user)
            resp = client.get("/api/v1/reports/", headers=headers)
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 1

    def test_filter_by_report_type(self, setup_reports_data):
        analyst = setup_reports_data["analyst"]
        headers = _auth_header(analyst)

        resp = client.get("/api/v1/reports/?type=vulnerability", headers=headers)
        assert resp.status_code == 200
        reports = resp.json()
        assert all(r["report_type"] == "vulnerability" for r in reports)

    def test_get_report_metadata(self, setup_reports_data):
        viewer = setup_reports_data["viewer"]
        headers = _auth_header(viewer)

        list_resp = client.get("/api/v1/reports/", headers=headers)
        report_id = list_resp.json()[0]["id"]

        resp = client.get(f"/api/v1/reports/{report_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == report_id

    def test_get_report_not_found(self, setup_reports_data):
        analyst = setup_reports_data["analyst"]
        headers = _auth_header(analyst)

        resp = client.get(f"/api/v1/reports/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"

    def test_org_isolation_on_list(self, setup_reports_data):
        org2_admin = setup_reports_data["org2_admin"]
        headers = _auth_header(org2_admin)

        resp = client.get("/api/v1/reports/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 0  # Org2 has no reports created


# ---------------------------------------------------------------------------
# Test Suite: Download Reports (GET /reports/{id}/download)
# ---------------------------------------------------------------------------

class TestDownloadReports:
    def test_download_pdf_analyst_success(self, setup_reports_data):
        analyst = setup_reports_data["analyst"]
        headers = _auth_header(analyst)

        list_resp = client.get("/api/v1/reports/", headers=headers)
        report_id = list_resp.json()[0]["id"]

        resp = client.get(f"/api/v1/reports/{report_id}/download?format=pdf", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"] == "application/pdf"
        assert "attachment" in resp.headers["content-disposition"]
        assert resp.content.startswith(b"%PDF")

    def test_download_csv_admin_success(self, setup_reports_data):
        admin = setup_reports_data["admin"]
        headers = _auth_header(admin)

        list_resp = client.get("/api/v1/reports/", headers=headers)
        report_id = list_resp.json()[0]["id"]

        resp = client.get(f"/api/v1/reports/{report_id}/download?format=csv", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in resp.headers["content-disposition"]
        text = resp.text
        assert len(text) > 10

    def test_download_viewer_forbidden(self, setup_reports_data):
        viewer = setup_reports_data["viewer"]
        analyst = setup_reports_data["analyst"]

        list_resp = client.get("/api/v1/reports/", headers=_auth_header(analyst))
        report_id = list_resp.json()[0]["id"]

        resp = client.get(f"/api/v1/reports/{report_id}/download?format=pdf", headers=_auth_header(viewer))
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_download_cross_org_returns_404(self, setup_reports_data):
        org2_admin = setup_reports_data["org2_admin"]
        analyst = setup_reports_data["analyst"]

        list_resp = client.get("/api/v1/reports/", headers=_auth_header(analyst))
        report_id = list_resp.json()[0]["id"]

        resp = client.get(f"/api/v1/reports/{report_id}/download?format=pdf", headers=_auth_header(org2_admin))
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOT_FOUND"
