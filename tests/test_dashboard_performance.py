"""
Tests for Consolidated Dashboard Endpoint and Performance Optimization.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.agent import Agent
from app.models.device import Device
from app.models.organization import Organization, Role
from app.models.scan import Scan, Vulnerability
from app.models.user import User
from app.core.security import create_access_token, hash_password
from app.core.seed import CANONICAL_ROLES

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_dashboard_test_data(create_tables, db_session):
    org1 = Organization(name="DashOrg1", slug=f"dash-org-1-{uuid.uuid4().hex[:6]}")
    org2 = Organization(name="DashOrg2", slug=f"dash-org-2-{uuid.uuid4().hex[:6]}")
    db_session.add_all([org1, org2])
    db_session.flush()

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

    admin1 = User(
        organization_id=org1.id,
        role_id=roles["Administrator"].id,
        email=f"admin_dash_{uuid.uuid4().hex[:6]}@example.com",
        username="admin_dash",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    viewer1 = User(
        organization_id=org1.id,
        role_id=roles["Viewer"].id,
        email=f"viewer_dash_{uuid.uuid4().hex[:6]}@example.com",
        username="viewer_dash",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    admin2 = User(
        organization_id=org2.id,
        role_id=roles["Administrator"].id,
        email=f"admin2_dash_{uuid.uuid4().hex[:6]}@example.com",
        username="admin2_dash",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    db_session.add_all([admin1, viewer1, admin2])
    db_session.flush()

    # Seed Agent for Org1
    a1 = Agent(
        organization_id=org1.id,
        name="Org1 Agent",
        hostname="org1-host",
        status="ONLINE",
        is_active=True,
    )
    # Seed Device for Org1
    d1 = Device(
        organization_id=org1.id,
        ip_address="10.0.0.1",
        hostname="org1-dev",
        status="online",
    )
    # Seed Device for Org2
    d2 = Device(
        organization_id=org2.id,
        ip_address="192.168.1.99",
        hostname="org2-dev",
        status="online",
    )
    db_session.add_all([a1, d1, d2])
    db_session.commit()

    token_admin1 = create_access_token(str(admin1.id), "Administrator", str(org1.id))
    token_viewer1 = create_access_token(str(viewer1.id), "Viewer", str(org1.id))
    token_admin2 = create_access_token(str(admin2.id), "Administrator", str(org2.id))

    return {
        "org1": org1,
        "org2": org2,
        "token_admin1": token_admin1,
        "token_viewer1": token_viewer1,
        "token_admin2": token_admin2,
    }


def test_dashboard_unauthenticated_returns_401():
    resp = client.get("/api/v1/dashboard/")
    assert resp.status_code == 401


def test_dashboard_returns_consolidated_data(setup_dashboard_test_data):
    token = setup_dashboard_test_data["token_admin1"]
    resp = client.get("/api/v1/dashboard/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert "summary" in data
    assert "agents" in data
    assert "devices" in data
    assert "vulnerabilities" in data
    assert "scans" in data
    assert "recent_logs" in data

    assert data["summary"]["agents_online"] >= 1
    assert data["summary"]["devices_online"] >= 1
    assert any(d["ip_address"] == "10.0.0.1" for d in data["devices"])


def test_dashboard_accessible_by_viewer(setup_dashboard_test_data):
    token = setup_dashboard_test_data["token_viewer1"]
    resp = client.get("/api/v1/dashboard/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data


def test_dashboard_enforces_org_isolation(setup_dashboard_test_data):
    token = setup_dashboard_test_data["token_admin2"]
    resp = client.get("/api/v1/dashboard/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()

    # Org2 should only see Org2 devices
    assert any(d["ip_address"] == "192.168.1.99" for d in data["devices"])
    assert not any(d["ip_address"] == "10.0.0.1" for d in data["devices"])
