"""
Tests for scan target validation and Nmap argument injection hardening.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.api.v1.scans import validate_target_scope
from app.models.agent import Agent
from app.core.security import create_access_token
from agent.collectors.vulnerability_scanner import (
    is_safe_target as vuln_is_safe_target,
    scan_vulnerabilities,
)
from agent.collectors.network_scanner import (
    is_safe_target as net_is_safe_target,
    discover_devices,
)

client = TestClient(app)


@pytest.fixture(scope="module")
def test_org_and_users(db_session):
    """Create org + admin + analyst + viewer for scan validation tests."""
    from app.models.organization import Organization, Role
    from app.models.user import User
    from app.core.security import hash_password

    org = Organization(name="ScanValOrg", slug="scan-val-org")
    db_session.add(org)
    db_session.flush()

    from app.core.seed import CANONICAL_ROLES
    roles = {}
    for name, desc in CANONICAL_ROLES:
        existing = db_session.query(Role).filter(Role.name == name).first()
        if existing:
            roles[name] = existing
        else:
            r = Role(name=name, description=desc)
            db_session.add(r)
            db_session.flush()
            roles[name] = r

    admin = User(
        organization_id=org.id,
        role_id=roles["Administrator"].id,
        email="scanvaladmin@test.com",
        password_hash=hash_password("AdminPass123!"),
        username="scanvaladmin",
        is_active=True,
    )
    analyst = User(
        organization_id=org.id,
        role_id=roles["Security Analyst"].id,
        email="scanvalanalyst@test.com",
        password_hash=hash_password("AnalystPass123!"),
        username="scanvalanalyst",
        is_active=True,
    )
    viewer = User(
        organization_id=org.id,
        role_id=roles["Viewer"].id,
        email="scanvalviewer@test.com",
        password_hash=hash_password("ViewerPass123!"),
        username="scanvalviewer",
        is_active=True,
    )
    db_session.add_all([admin, analyst, viewer])
    db_session.commit()
    return {"org": org, "admin": admin, "analyst": analyst, "viewer": viewer}


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


class TestTargetScopeValidationUnit:
    """Unit tests for validate_target_scope logic."""

    @pytest.mark.parametrize(
        "valid_target",
        [
            "local",
            "{}",
            "127.0.0.1",
            "192.168.1.100",
            "::1",
            "192.168.0.0/16",
            "192.168.1.0/24",
            "10.50.0.0/24",
            "2001:db8::/64",
            "localhost",
            "scanme.nmap.org",
            "secure-host.internal.local",
        ],
    )
    def test_valid_target_scopes(self, valid_target):
        result = validate_target_scope(valid_target)
        assert result == valid_target

    @pytest.mark.parametrize(
        "invalid_target",
        [
            "--script=vuln",
            "-sV",
            "-oN /tmp/hacked",
            "-T4",
            "192.168.1.1; cat /etc/passwd",
            "192.168.1.1|whoami",
            "192.168.1.1 && ping 1.1.1.1",
            "`id`",
            "$(whoami)",
            "192.168.1.1 > output.txt",
            "192.168.1.1 10.0.0.1",
            "0.0.0.0/0",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "2001:db8::/32",
            "999.999.999.999",
            "invalid hostname with spaces",
            "",
        ],
    )
    def test_invalid_target_scopes(self, invalid_target):
        with pytest.raises(HTTPException) as exc_info:
            validate_target_scope(invalid_target)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"]["code"] == "VALIDATION_ERROR"


class TestScanCreationAPIValidation:
    """API integration tests for scan endpoint target validation."""

    def test_api_rejects_option_injection(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        analyst = test_org_and_users["analyst"]
        token = _token_for(analyst)

        agent = Agent(
            organization_id=org.id,
            name="scan-val-agent",
            hostname="val-host",
            status="ONLINE",
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.post(
            "/api/v1/scans/",
            json={
                "agent_id": str(agent.id),
                "scan_type": "discovery",
                "target_scope": "--script=vuln -oN /tmp/test",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        err = resp.json()["error"]
        assert err["code"] == "VALIDATION_ERROR"
        assert "option injection" in err["message"] or "invalid" in err["message"].lower()

    def test_api_rejects_broad_cidr(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        analyst = test_org_and_users["analyst"]
        token = _token_for(analyst)

        agent = Agent(
            organization_id=org.id,
            name="scan-val-agent-2",
            hostname="val-host-2",
            status="ONLINE",
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.post(
            "/api/v1/scans/",
            json={
                "agent_id": str(agent.id),
                "scan_type": "discovery",
                "target_scope": "10.0.0.0/8",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_api_accepts_valid_scope(self, test_org_and_users, db_session):
        org = test_org_and_users["org"]
        analyst = test_org_and_users["analyst"]
        token = _token_for(analyst)

        agent = Agent(
            organization_id=org.id,
            name="scan-val-agent-3",
            hostname="val-host-3",
            status="ONLINE",
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.post(
            "/api/v1/scans/",
            json={
                "agent_id": str(agent.id),
                "scan_type": "vulnerability",
                "target_scope": "192.168.1.100",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["target_scope"] == "192.168.1.100"


class TestAgentCollectorHardening:
    """Agent-side collector validation tests."""

    def test_vuln_scanner_rejects_bad_targets(self):
        assert not vuln_is_safe_target("--script=smb-vuln*")
        assert not vuln_is_safe_target("-sV")
        assert not vuln_is_safe_target("127.0.0.1; whoami")
        assert not vuln_is_safe_target("")

        res = scan_vulnerabilities("--bad-flag")
        assert res["services"] == []

    def test_net_scanner_rejects_bad_targets(self):
        assert not net_is_safe_target("-sn")
        assert not net_is_safe_target("192.168.1.0/24 | ls")
        assert not net_is_safe_target("")

        res = discover_devices("--bad-flag")
        assert res["hosts"] == []
