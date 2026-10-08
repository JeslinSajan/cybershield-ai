"""
Test suite for Phase 13 — Vulnerability Scanning.
Covers CVE seed data, vulnerability processing, and endpoints.
"""

import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.seed import seed_cves
from app.models.agent import Agent, AgentCredential
from app.models.device import Device
from app.models.organization import Organization, Role
from app.models.scan import CVE, Scan, ScanResult, Vulnerability
from app.models.system import AuditLog
from app.models.user import User
from app.services.vulnerability_service import process_vulnerability_result

client = TestClient(app)


class TestCVESeedData:
    def test_seed_cves_populates_database(self, db_session):
        """seed_cves inserts demo CVE records into database for the specified organization."""
        db_session.query(CVE).delete()
        db_session.commit()

        uid = uuid.uuid4().hex[:8]
        org = Organization(name=f"CVETestOrg-{uid}", slug=f"cve-test-org-{uid}")
        db_session.add(org)
        db_session.commit()

        count = seed_cves(db=db_session, organization_id=org.id)
        assert count >= 10

        cves = db_session.query(CVE).filter(CVE.organization_id == org.id).all()
        assert len(cves) == count

        # Verify critical CVEs are present
        cve_ids = {c.cve_id for c in cves}
        assert "CVE-2021-44228" in cve_ids  # Log4Shell
        assert "CVE-2021-41773" in cve_ids  # Apache Path Traversal
        assert "CVE-2018-15473" in cve_ids  # OpenSSH User Enum

    def test_seed_cves_is_idempotent(self, db_session):
        """Calling seed_cves repeatedly does not duplicate rows."""
        existing_count = db_session.query(CVE).count()
        if existing_count == 0:
            uid = uuid.uuid4().hex[:8]
            org = Organization(name=f"CVEIdempOrg-{uid}", slug=f"cve-idemp-org-{uid}")
            db_session.add(org)
            db_session.commit()
            seed_cves(db=db_session, organization_id=org.id)
            existing_count = db_session.query(CVE).count()

        # Calling again must insert 0 records
        second_count = seed_cves(db=db_session)
        assert second_count == 0

        total = db_session.query(CVE).count()
        assert total == existing_count

    def test_seeded_cve_fields_integrity(self, db_session):
        """Verify field values of seeded CVEs."""
        log4j = db_session.query(CVE).filter(
            CVE.cve_id == "CVE-2021-44228",
        ).first()

        assert log4j is not None
        assert log4j.severity == "Critical"
        assert float(log4j.cvss_score) == 10.0
        assert log4j.affected_service == "log4j"
        assert log4j.is_demo_data is True
        assert "JNDI" in log4j.summary


class TestVulnerabilityProcessingService:
    @pytest.fixture
    def setup_vulnerability_env(self, db_session):
        """Set up test org, agent, scan, and ensure seed CVEs exist."""
        uid = uuid.uuid4().hex[:8]
        org = Organization(name=f"VulnProcOrg-{uid}", slug=f"vuln-proc-org-{uid}")
        db_session.add(org)
        db_session.flush()

        # Ensure demo CVEs exist
        if db_session.query(CVE).count() < 10:
            seed_cves(db=db_session, organization_id=org.id)

        role = db_session.query(Role).first()
        if not role:
            role = Role(name="Administrator", description="Admin role")
            db_session.add(role)
            db_session.flush()

        user = User(
            organization_id=org.id,
            role_id=role.id,
            email=f"vulnuser-{uid}@test.com",
            username=f"vulnuser-{uid}",
            password_hash="testhash",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        agent = Agent(
            organization_id=org.id,
            name=f"vuln-agent-{uid}",
            hostname="vuln-host",
            status="ONLINE",
            is_active=True,
        )
        db_session.add(agent)
        db_session.flush()

        raw_cred = secrets.token_urlsafe(48)
        cred_hash = hashlib.sha256(raw_cred.encode()).hexdigest()
        cred = AgentCredential(
            agent_id=agent.id,
            credential_hash=cred_hash,
            type="token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True,
        )
        db_session.add(cred)
        db_session.flush()

        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=user.id,
            scan_type="vulnerability",
            status="RUNNING",
            target_scope="192.168.1.100",
        )
        db_session.add(scan)
        db_session.commit()

        return {
            "org": org,
            "user": user,
            "agent": agent,
            "raw_cred": raw_cred,
            "scan": scan,
        }

    def test_matching_services_creates_vulnerabilities(self, db_session, setup_vulnerability_env):
        env = setup_vulnerability_env
        agent = env["agent"]
        scan = env["scan"]

        scan_result = ScanResult(
            organization_id=agent.organization_id,
            scan_id=scan.id,
            result_type="services",
            upload_id=str(uuid.uuid4()),
            raw_payload={
                "target_ip": "192.168.1.100",
                "services": [
                    {
                        "port": 80,
                        "protocol": "tcp",
                        "service": "http",
                        "version": "Apache 2.4.49",
                        "state": "open",
                    },
                    {
                        "port": 22,
                        "protocol": "tcp",
                        "service": "ssh",
                        "version": "OpenSSH 7.4",
                        "state": "open",
                    },
                ],
            },
        )
        db_session.add(scan_result)
        db_session.flush()

        vulns = process_vulnerability_result(db_session, scan_result, agent)
        db_session.commit()

        # Should match Apache 2.4.49 (CVE-2021-41773) and OpenSSH 7.4 (CVE-2018-15473)
        assert len(vulns) >= 2
        for v in vulns:
            assert v.status == "open"
            assert isinstance(v.cve_id, uuid.UUID)  # FK to cves.id, not string
            assert v.device_id == scan_result.device_id
            assert v.organization_id == agent.organization_id
            assert v.scan_id == scan.id
            assert v.severity in ("Critical", "High", "Medium", "Low")
            assert v.score is not None

        # Verify device was created and linked
        device = db_session.query(Device).filter(Device.id == scan_result.device_id).first()
        assert device is not None
        assert device.ip_address == "192.168.1.100"

        # Verify AuditLog written
        audit = db_session.query(AuditLog).filter(
            AuditLog.organization_id == agent.organization_id,
            AuditLog.action == "vulnerabilities_detected",
        ).first()
        assert audit is not None
        assert audit.target_id == device.id

    def test_deduplication_skips_existing_open_vulnerabilities(self, db_session, setup_vulnerability_env):
        env = setup_vulnerability_env
        agent = env["agent"]
        scan = env["scan"]

        scan_result = ScanResult(
            organization_id=agent.organization_id,
            scan_id=scan.id,
            result_type="services",
            upload_id=str(uuid.uuid4()),
            raw_payload={
                "target_ip": "192.168.1.100",
                "services": [
                    {
                        "port": 80,
                        "protocol": "tcp",
                        "service": "http",
                        "version": "Apache 2.4.49",
                        "state": "open",
                    },
                ],
            },
        )
        db_session.add(scan_result)
        db_session.flush()

        # First run creates vulnerability
        vulns_first = process_vulnerability_result(db_session, scan_result, agent)
        db_session.commit()
        assert len(vulns_first) >= 1

        # Second run with same device and services must skip duplicate
        scan_result_2 = ScanResult(
            organization_id=agent.organization_id,
            scan_id=scan.id,
            device_id=scan_result.device_id,
            result_type="services",
            upload_id=str(uuid.uuid4()),
            raw_payload=scan_result.raw_payload,
        )
        db_session.add(scan_result_2)
        db_session.flush()

        vulns_second = process_vulnerability_result(db_session, scan_result_2, agent)
        db_session.commit()
        assert len(vulns_second) == 0

    def test_non_matching_services_creates_zero_vulnerabilities(self, db_session, setup_vulnerability_env):
        env = setup_vulnerability_env
        agent = env["agent"]
        scan = env["scan"]

        scan_result = ScanResult(
            organization_id=agent.organization_id,
            scan_id=scan.id,
            result_type="services",
            upload_id=str(uuid.uuid4()),
            raw_payload={
                "target_ip": "192.168.1.222",
                "services": [
                    {
                        "port": 9999,
                        "protocol": "tcp",
                        "service": "safe-custom-app",
                        "version": "99.9.9",
                        "state": "open",
                    },
                ],
            },
        )
        db_session.add(scan_result)
        db_session.flush()

        vulns = process_vulnerability_result(db_session, scan_result, agent)
        db_session.commit()

        assert len(vulns) == 0
        # Device is created, but no vulnerabilities
        device = db_session.query(Device).filter(Device.ip_address == "192.168.1.222").first()
        assert device is not None


class TestUploadResultVulnerabilityIntegration:
    def test_agent_upload_result_processes_vulnerabilities(self, db_session):
        """End-to-end integration: POST /agents/results with result_type='services' creates vulnerabilities."""
        uid = uuid.uuid4().hex[:8]
        org = Organization(name=f"UploadVulnOrg-{uid}", slug=f"upload-vuln-org-{uid}")
        db_session.add(org)
        db_session.flush()

        if db_session.query(CVE).count() < 10:
            seed_cves(db=db_session, organization_id=org.id)

        role = db_session.query(Role).first()
        if not role:
            role = Role(name="Administrator", description="Admin role")
            db_session.add(role)
            db_session.flush()

        user = User(
            organization_id=org.id,
            role_id=role.id,
            email=f"uploaduser-{uid}@test.com",
            username=f"uploaduser-{uid}",
            password_hash="testhash",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        agent = Agent(
            organization_id=org.id,
            name=f"upload-agent-{uid}",
            hostname="upload-host",
            status="ONLINE",
            is_active=True,
        )
        db_session.add(agent)
        db_session.flush()

        raw_cred = secrets.token_urlsafe(48)
        cred_hash = hashlib.sha256(raw_cred.encode()).hexdigest()
        cred = AgentCredential(
            agent_id=agent.id,
            credential_hash=cred_hash,
            type="token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True,
        )
        db_session.add(cred)
        db_session.flush()

        scan = Scan(
            organization_id=org.id,
            agent_id=agent.id,
            created_by_user_id=user.id,
            scan_type="vulnerability",
            status="RUNNING",
            target_scope="192.168.1.105",
        )
        db_session.add(scan)
        db_session.commit()

        # POST /agents/results
        resp = client.post(
            "/api/v1/agents/results",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json={
                "scan_id": str(scan.id),
                "result_type": "services",
                "upload_id": str(uuid.uuid4()),
                "raw_payload": {
                    "target_ip": "192.168.1.105",
                    "services": [
                        {
                            "port": 21,
                            "protocol": "tcp",
                            "service": "vsftpd",
                            "version": "2.3.4",
                            "state": "open",
                        }
                    ],
                },
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["result_type"] == "services"
        assert data["device_id"] is not None

        # Check vulnerability created for vsftpd 2.3.4 (CVE-2011-2523)
        device_id = uuid.UUID(data["device_id"])
        vulns = db_session.query(Vulnerability).filter(
            Vulnerability.device_id == device_id,
            Vulnerability.status == "open",
        ).all()
        assert len(vulns) >= 1
        vsftpd_vuln = vulns[0]
        assert vsftpd_vuln.severity == "Critical"
        assert "Backdoor" in vsftpd_vuln.description
