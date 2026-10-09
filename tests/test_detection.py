"""
Test suite for Phase 15 — Threat Detection.
Tests Brute Force, Port Scan, Suspicious Login rules, alert deduplication,
system audit logs, notifications, and multi-tenant isolation.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.core.seed import CANONICAL_ROLES
from app.main import app
from app.models.agent import Agent, AgentCredential
from app.models.alert import Alert
from app.models.device import Device
from app.models.log import Log
from app.models.organization import Organization, Role
from app.models.scan import Scan, ScanResult
from app.models.system import AuditLog, Notification
from app.models.user import User
from app.services.detection_service import (
    check_brute_force,
    check_port_scan,
    check_suspicious_login,
    create_alert,
    process_log_detections,
    process_scan_detections,
)

client = TestClient(app)


@pytest.fixture
def setup_detection_env(db_session):
    uid = uuid.uuid4().hex[:8]
    org1 = Organization(name=f"DetOrg1-{uid}", slug=f"det-org-1-{uid}")
    org2 = Organization(name=f"DetOrg2-{uid}", slug=f"det-org-2-{uid}")
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

    # Users in Org1
    admin1 = User(
        organization_id=org1.id,
        role_id=roles["Administrator"].id,
        email=f"admin1-{uid}@test.com",
        username=f"admin1-{uid}",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    analyst1 = User(
        organization_id=org1.id,
        role_id=roles["Security Analyst"].id,
        email=f"analyst1-{uid}@test.com",
        username=f"analyst1-{uid}",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    viewer1 = User(
        organization_id=org1.id,
        role_id=roles["Viewer"].id,
        email=f"viewer1-{uid}@test.com",
        username=f"viewer1-{uid}",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )

    # User in Org2
    admin2 = User(
        organization_id=org2.id,
        role_id=roles["Administrator"].id,
        email=f"admin2-{uid}@test.com",
        username=f"admin2-{uid}",
        password_hash=hash_password("Pass123!"),
        is_active=True,
    )
    db_session.add_all([admin1, analyst1, viewer1, admin2])
    db_session.flush()

    # Agent 1
    agent1 = Agent(
        organization_id=org1.id,
        name=f"agent1-{uid}",
        hostname="host-1",
        status="ONLINE",
        is_active=True,
    )
    db_session.add(agent1)
    db_session.flush()

    raw_cred1 = secrets.token_urlsafe(48)
    cred_hash1 = hashlib.sha256(raw_cred1.encode()).hexdigest()
    cred1 = AgentCredential(
        agent_id=agent1.id,
        credential_hash=cred_hash1,
        type="token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_active=True,
    )
    db_session.add(cred1)

    # Agent 2
    agent2 = Agent(
        organization_id=org2.id,
        name=f"agent2-{uid}",
        hostname="host-2",
        status="ONLINE",
        is_active=True,
    )
    db_session.add(agent2)
    db_session.flush()

    raw_cred2 = secrets.token_urlsafe(48)
    cred_hash2 = hashlib.sha256(raw_cred2.encode()).hexdigest()
    cred2 = AgentCredential(
        agent_id=agent2.id,
        credential_hash=cred_hash2,
        type="token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_active=True,
    )
    db_session.add(cred2)

    # Devices
    dev1 = Device(
        organization_id=org1.id,
        agent_id=agent1.id,
        ip_address="192.168.1.10",
        hostname="host-1",
        status="online",
    )
    dev2 = Device(
        organization_id=org2.id,
        agent_id=agent2.id,
        ip_address="10.0.0.10",
        hostname="host-2",
        status="online",
    )
    db_session.add_all([dev1, dev2])

    # Scan in Org1
    scan1 = Scan(
        organization_id=org1.id,
        agent_id=agent1.id,
        created_by_user_id=admin1.id,
        scan_type="vulnerability",
        status="RUNNING",
        target_scope="192.168.1.10",
    )
    db_session.add(scan1)
    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "users_org1": [admin1, analyst1, viewer1],
        "users_org2": [admin2],
        "agent1": agent1,
        "agent2": agent2,
        "raw_cred1": raw_cred1,
        "raw_cred2": raw_cred2,
        "dev1": dev1,
        "dev2": dev2,
        "scan1": scan1,
    }


class TestRule1BruteForce:
    def test_less_than_five_failures_does_not_trigger_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        org_id = env["org1"].id
        agent_id = env["agent1"].id
        source_ip = "198.51.100.11"
        now = datetime.now(timezone.utc)

        # Insert 4 login_failure logs
        for i in range(4):
            log = Log(
                organization_id=org_id,
                agent_id=agent_id,
                source="auth.log",
                event_type="login_failure",
                severity="medium",
                message=f"Failed attempt {i+1}",
                source_ip=source_ip,
                username="root",
                timestamp=now - timedelta(minutes=i),
            )
            db_session.add(log)
        db_session.commit()

        alert = check_brute_force(db_session, org_id, agent_id, source_ip)
        assert alert is None

    def test_five_failures_within_ten_minutes_triggers_brute_force_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        org_id = env["org1"].id
        agent_id = env["agent1"].id
        source_ip = "198.51.100.22"
        now = datetime.now(timezone.utc)

        # Insert 5 login_failure logs
        for i in range(5):
            log = Log(
                organization_id=org_id,
                agent_id=agent_id,
                source="auth.log",
                event_type="login_failure",
                severity="medium",
                message=f"Failed attempt {i+1}",
                source_ip=source_ip,
                username="admin",
                timestamp=now - timedelta(minutes=i),
            )
            db_session.add(log)
        db_session.commit()

        alert = check_brute_force(db_session, org_id, agent_id, source_ip, device_id=env["dev1"].id)
        assert alert is not None
        assert alert.alert_type == "brute_force"
        assert alert.severity == "High"
        assert float(alert.risk_score) == 40.0
        assert alert.status == "Open"
        assert source_ip in alert.description
        assert alert.organization_id == org_id
        assert alert.agent_id == agent_id
        assert alert.device_id == env["dev1"].id

        # Verify AuditLog created
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.target_id == alert.id, AuditLog.action == "alert_created")
            .first()
        )
        assert audit is not None
        assert audit.actor_type == "system"
        assert audit.organization_id == org_id

        # Verify Notifications created for all 3 users in Org1
        notifications = (
            db_session.query(Notification)
            .filter(Notification.alert_id == alert.id)
            .all()
        )
        assert len(notifications) == 3
        for n in notifications:
            assert n.notification_type == "alert"
            assert n.channel == "dashboard"
            assert n.is_read is False

    def test_failures_older_than_ten_minutes_ignored(self, setup_detection_env, db_session):
        env = setup_detection_env
        org_id = env["org1"].id
        agent_id = env["agent1"].id
        source_ip = "198.51.100.33"
        now = datetime.now(timezone.utc)

        # 5 failures, but 2 are 15 minutes ago
        timestamps = [
            now - timedelta(minutes=1),
            now - timedelta(minutes=2),
            now - timedelta(minutes=3),
            now - timedelta(minutes=15),
            now - timedelta(minutes=16),
        ]
        for ts in timestamps:
            log = Log(
                organization_id=org_id,
                agent_id=agent_id,
                source="auth.log",
                event_type="login_failure",
                severity="medium",
                message="Old attempt",
                source_ip=source_ip,
                username="admin",
                timestamp=ts,
            )
            db_session.add(log)
        db_session.commit()

        alert = check_brute_force(db_session, org_id, agent_id, source_ip)
        assert alert is None


class TestRule2PortScan:
    def test_less_than_ten_open_ports_does_not_trigger_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        scan = env["scan1"]
        org_id = env["org1"].id
        agent_id = env["agent1"].id

        services = [{"port": 80 + i, "service": "http", "state": "open"} for i in range(9)]
        scan_result = ScanResult(
            organization_id=org_id,
            scan_id=scan.id,
            device_id=env["dev1"].id,
            result_type="services",
            upload_id=str(uuid.uuid4()),
            raw_payload={"target_ip": "192.168.1.10", "services": services},
        )
        db_session.add(scan_result)
        db_session.commit()

        alert = check_port_scan(db_session, org_id, agent_id, scan_result)
        assert alert is None

    def test_ten_or_more_open_ports_triggers_port_scan_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        scan = env["scan1"]
        org_id = env["org1"].id
        agent_id = env["agent1"].id

        services = [{"port": 80 + i, "service": "http", "state": "open"} for i in range(12)]
        scan_result = ScanResult(
            organization_id=org_id,
            scan_id=scan.id,
            device_id=env["dev1"].id,
            result_type="services",
            upload_id=str(uuid.uuid4()),
            raw_payload={"target_ip": "192.168.1.10", "services": services},
        )
        db_session.add(scan_result)
        db_session.commit()

        alert = check_port_scan(db_session, org_id, agent_id, scan_result)
        assert alert is not None
        assert alert.alert_type == "port_scan"
        assert alert.severity == "Medium"
        assert float(alert.risk_score) == 20.0
        assert "12 open ports" in alert.description
        assert alert.device_id == env["dev1"].id

        # Verify AuditLog created
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.target_id == alert.id, AuditLog.action == "alert_created")
            .first()
        )
        assert audit is not None


class TestRule3SuspiciousLogin:
    def test_login_success_without_prior_failures_no_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        org_id = env["org1"].id
        agent_id = env["agent1"].id
        source_ip = "198.51.100.44"

        alert = check_suspicious_login(db_session, org_id, agent_id, source_ip, username="ubuntu")
        assert alert is None

    def test_login_success_with_two_prior_failures_no_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        org_id = env["org1"].id
        agent_id = env["agent1"].id
        source_ip = "198.51.100.55"
        now = datetime.now(timezone.utc)

        for i in range(2):
            log = Log(
                organization_id=org_id,
                agent_id=agent_id,
                source="auth.log",
                event_type="login_failure",
                severity="medium",
                message="fail",
                source_ip=source_ip,
                username="ubuntu",
                timestamp=now - timedelta(minutes=10 * (i + 1)),
            )
            db_session.add(log)
        db_session.commit()

        alert = check_suspicious_login(db_session, org_id, agent_id, source_ip, username="ubuntu")
        assert alert is None

    def test_login_success_after_three_failures_in_last_hour_triggers_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        org_id = env["org1"].id
        agent_id = env["agent1"].id
        source_ip = "198.51.100.66"
        now = datetime.now(timezone.utc)

        # 3 failures in past 30 minutes
        for i in range(3):
            log = Log(
                organization_id=org_id,
                agent_id=agent_id,
                source="auth.log",
                event_type="login_failure",
                severity="medium",
                message=f"fail {i}",
                source_ip=source_ip,
                username="ubuntu",
                timestamp=now - timedelta(minutes=5 * (i + 1)),
            )
            db_session.add(log)
        db_session.commit()

        alert = check_suspicious_login(
            db_session, org_id, agent_id, source_ip, username="ubuntu", device_id=env["dev1"].id
        )
        assert alert is not None
        assert alert.alert_type == "suspicious_login"
        assert alert.severity == "High"
        assert float(alert.risk_score) == 40.0
        assert "ubuntu" in alert.description
        assert source_ip in alert.description

        # High severity -> check notification
        notifs = db_session.query(Notification).filter(Notification.alert_id == alert.id).all()
        assert len(notifs) == 3


class TestAlertDeduplication:
    def test_deduplication_suppresses_duplicate_open_alerts(self, setup_detection_env, db_session):
        env = setup_detection_env
        org_id = env["org1"].id
        agent_id = env["agent1"].id
        source_ip = "198.51.100.77"

        # Create first alert
        alert1 = create_alert(
            db=db_session,
            organization_id=org_id,
            alert_type="brute_force",
            severity="High",
            description=f"Brute force from {source_ip}",
            risk_score=40.0,
            agent_id=agent_id,
            source_ip=source_ip,
        )
        db_session.commit()
        assert alert1 is not None

        # Attempt to create duplicate alert within 1 hour
        alert2 = create_alert(
            db=db_session,
            organization_id=org_id,
            alert_type="brute_force",
            severity="High",
            description=f"Brute force from {source_ip}",
            risk_score=40.0,
            agent_id=agent_id,
            source_ip=source_ip,
        )
        assert alert2 is None

        # Verify only 1 alert in DB
        total_alerts = (
            db_session.query(Alert)
            .filter(Alert.organization_id == org_id, Alert.alert_type == "brute_force")
            .count()
        )
        assert total_alerts == 1

    def test_resolved_alert_allows_new_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        org_id = env["org1"].id
        agent_id = env["agent1"].id
        source_ip = "198.51.100.88"

        # First alert marked Resolved
        alert1 = create_alert(
            db=db_session,
            organization_id=org_id,
            alert_type="brute_force",
            severity="High",
            description=f"Brute force from {source_ip}",
            risk_score=40.0,
            agent_id=agent_id,
            source_ip=source_ip,
        )
        alert1.status = "Resolved"
        db_session.commit()

        # New alert should now be permitted
        alert2 = create_alert(
            db=db_session,
            organization_id=org_id,
            alert_type="brute_force",
            severity="High",
            description=f"Brute force from {source_ip}",
            risk_score=40.0,
            agent_id=agent_id,
            source_ip=source_ip,
        )
        db_session.commit()
        assert alert2 is not None
        assert alert2.id != alert1.id


class TestMultiTenantIsolation:
    def test_org2_failures_do_not_trigger_org1_alerts(self, setup_detection_env, db_session):
        env = setup_detection_env
        org2_id = env["org2"].id
        org1_id = env["org1"].id
        agent2_id = env["agent2"].id
        source_ip = "198.51.100.99"
        now = datetime.now(timezone.utc)

        # 5 failures in Org 2
        for i in range(5):
            log = Log(
                organization_id=org2_id,
                agent_id=agent2_id,
                source="auth.log",
                event_type="login_failure",
                severity="medium",
                message="fail",
                source_ip=source_ip,
                username="root",
                timestamp=now - timedelta(minutes=i),
            )
            db_session.add(log)
        db_session.commit()

        # Check Org 1 -> no alert
        alert_org1 = check_brute_force(db_session, org1_id, None, source_ip)
        assert alert_org1 is None

        # Check Org 2 -> alert created
        alert_org2 = check_brute_force(db_session, org2_id, agent2_id, source_ip)
        assert alert_org2 is not None
        assert alert_org2.organization_id == org2_id

        # Verify notifications only created for Org 2 admin
        notifs_org1 = (
            db_session.query(Notification)
            .filter(Notification.organization_id == org1_id)
            .count()
        )
        assert notifs_org1 == 0


class TestIngestionEndpointsTriggerDetection:
    def test_log_ingestion_endpoint_triggers_brute_force_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        raw_cred = env["raw_cred1"]
        org_id = env["org1"].id
        source_ip = "192.168.100.5"

        payload = {
            "logs": [
                {
                    "source": "auth.log",
                    "event_type": "login_failure",
                    "message": f"Failed login #{i}",
                    "source_ip": source_ip,
                    "username": "root",
                }
                for i in range(5)
            ]
        }

        resp = client.post(
            "/api/v1/agents/logs",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json=payload,
        )
        assert resp.status_code == 201

        # Check that Alert was created synchronously
        alert = (
            db_session.query(Alert)
            .filter(Alert.organization_id == org_id, Alert.alert_type == "brute_force")
            .first()
        )
        assert alert is not None
        assert alert.severity == "High"
        assert source_ip in alert.description

    def test_scan_result_endpoint_triggers_port_scan_alert(self, setup_detection_env, db_session):
        env = setup_detection_env
        raw_cred = env["raw_cred1"]
        scan = env["scan1"]
        org_id = env["org1"].id

        services = [{"port": 1000 + i, "service": f"svc-{i}", "state": "open"} for i in range(11)]
        payload = {
            "scan_id": str(scan.id),
            "result_type": "services",
            "raw_payload": {
                "target_ip": "192.168.1.10",
                "services": services,
            },
        }

        resp = client.post(
            "/api/v1/agents/results",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json=payload,
        )
        assert resp.status_code == 201

        # Check that Alert was created synchronously
        alert = (
            db_session.query(Alert)
            .filter(Alert.organization_id == org_id, Alert.alert_type == "port_scan")
            .first()
        )
        assert alert is not None
        assert alert.severity == "Medium"
        assert "11 open ports" in alert.description
