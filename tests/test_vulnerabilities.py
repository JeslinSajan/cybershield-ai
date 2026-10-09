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


class TestVulnerabilityEndpoints:
    @pytest.fixture
    def vuln_endpoint_setup(self, db_session):
        from app.core.security import create_access_token, hash_password
        from app.core.seed import CANONICAL_ROLES

        uid = uuid.uuid4().hex[:8]
        org1 = Organization(name=f"VulnEpOrg1-{uid}", slug=f"vuln-ep-org-1-{uid}")
        org2 = Organization(name=f"VulnEpOrg2-{uid}", slug=f"vuln-ep-org-2-{uid}")
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

        # Users for Org1: Admin, Analyst, Viewer
        admin_org1 = User(
            organization_id=org1.id,
            role_id=roles["Administrator"].id,
            email=f"admin1-{uid}@test.com",
            username=f"admin1-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        analyst_org1 = User(
            organization_id=org1.id,
            role_id=roles["Security Analyst"].id,
            email=f"analyst1-{uid}@test.com",
            username=f"analyst1-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        viewer_org1 = User(
            organization_id=org1.id,
            role_id=roles["Viewer"].id,
            email=f"viewer1-{uid}@test.com",
            username=f"viewer1-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        # User for Org2: Viewer
        viewer_org2 = User(
            organization_id=org2.id,
            role_id=roles["Viewer"].id,
            email=f"viewer2-{uid}@test.com",
            username=f"viewer2-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        db_session.add_all([admin_org1, analyst_org1, viewer_org1, viewer_org2])
        db_session.flush()

        # Seed CVEs
        if db_session.query(CVE).count() < 10:
            seed_cves(db=db_session, organization_id=org1.id)

        cve1 = db_session.query(CVE).filter(CVE.cve_id == "CVE-2021-41773").first()
        cve2 = db_session.query(CVE).filter(CVE.cve_id == "CVE-2018-15473").first()

        # Create device in Org1
        dev1 = Device(
            organization_id=org1.id,
            ip_address="192.168.1.55",
            hostname="server-55",
            status="online",
        )
        db_session.add(dev1)
        db_session.flush()

        # Create 2 vulnerabilities in Org1
        vuln1 = Vulnerability(
            organization_id=org1.id,
            device_id=dev1.id,
            cve_id=cve1.id if cve1 else None,
            severity="Critical",
            score=9.8,
            description="Apache Path Traversal",
            recommendation="Update Apache",
            status="open",
        )
        vuln2 = Vulnerability(
            organization_id=org1.id,
            device_id=dev1.id,
            cve_id=cve2.id if cve2 else None,
            severity="Medium",
            score=5.3,
            description="OpenSSH User Enum",
            recommendation="Upgrade OpenSSH",
            status="resolved",
        )
        db_session.add_all([vuln1, vuln2])
        db_session.commit()

        # Tokens
        token_admin = create_access_token(str(admin_org1.id), "Administrator", str(org1.id))
        token_analyst = create_access_token(str(analyst_org1.id), "Security Analyst", str(org1.id))
        token_viewer = create_access_token(str(viewer_org1.id), "Viewer", str(org1.id))
        token_org2 = create_access_token(str(viewer_org2.id), "Viewer", str(org2.id))

        return {
            "org1": org1,
            "org2": org2,
            "dev1": dev1,
            "vuln1": vuln1,
            "vuln2": vuln2,
            "tokens": {
                "admin": token_admin,
                "analyst": token_analyst,
                "viewer": token_viewer,
                "org2": token_org2,
            },
        }

    def test_all_three_roles_can_list_vulnerabilities(self, vuln_endpoint_setup):
        tokens = vuln_endpoint_setup["tokens"]
        for role_name in ("admin", "analyst", "viewer"):
            resp = client.get(
                "/api/v1/vulnerabilities/",
                headers={"Authorization": f"Bearer {tokens[role_name]}"},
            )
            assert resp.status_code == 200, f"Role {role_name} failed: {resp.text}"
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 2

    def test_unauthenticated_request_returns_401(self):
        resp = client.get("/api/v1/vulnerabilities/")
        assert resp.status_code == 401

    def test_list_vulnerabilities_filters(self, vuln_endpoint_setup):
        token = vuln_endpoint_setup["tokens"]["viewer"]
        dev_id = vuln_endpoint_setup["dev1"].id

        # Filter by severity
        resp_crit = client.get(
            "/api/v1/vulnerabilities/?severity=Critical",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_crit.status_code == 200
        for item in resp_crit.json():
            assert item["severity"] == "Critical"

        # Filter by status
        resp_open = client.get(
            "/api/v1/vulnerabilities/?status=open",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_open.status_code == 200
        for item in resp_open.json():
            assert item["status"] == "open"

        # Filter by device_id
        resp_dev = client.get(
            f"/api/v1/vulnerabilities/?device_id={dev_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_dev.status_code == 200
        assert len(resp_dev.json()) >= 2
        for item in resp_dev.json():
            assert item["device_id"] == str(dev_id)

        # Pagination: limit=1
        resp_page = client.get(
            "/api/v1/vulnerabilities/?limit=1&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_page.status_code == 200
        assert len(resp_page.json()) == 1

    def test_get_vulnerability_by_id(self, vuln_endpoint_setup):
        token = vuln_endpoint_setup["tokens"]["analyst"]
        vuln1 = vuln_endpoint_setup["vuln1"]

        # 200 Success
        resp = client.get(
            f"/api/v1/vulnerabilities/{vuln1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(vuln1.id)
        assert data["severity"] == "Critical"
        assert data["score"] == 9.8
        assert data["cve_code"] == "CVE-2021-41773"
        assert data["cve_details"] is not None
        assert data["cve_details"]["cve_id"] == "CVE-2021-41773"

        # 404 Nonexistent
        non_id = uuid.uuid4()
        resp_404 = client.get(
            f"/api/v1/vulnerabilities/{non_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_404.status_code == 404
        assert resp_404.json()["error"]["code"] == "NOT_FOUND"

    def test_get_device_vulnerabilities_endpoint(self, vuln_endpoint_setup):
        token = vuln_endpoint_setup["tokens"]["viewer"]
        dev_id = vuln_endpoint_setup["dev1"].id

        resp = client.get(
            f"/api/v1/devices/{dev_id}/vulnerabilities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        for item in data:
            assert item["device_id"] == str(dev_id)
            assert "severity" in item
            assert "description" in item

        # 404 for nonexistent device
        resp_404 = client.get(
            f"/api/v1/devices/{uuid.uuid4()}/vulnerabilities",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_404.status_code == 404
        assert resp_404.json()["error"]["code"] == "NOT_FOUND"

    def test_cross_organization_vulnerability_isolation(self, vuln_endpoint_setup):
        token_org2 = vuln_endpoint_setup["tokens"]["org2"]
        vuln1 = vuln_endpoint_setup["vuln1"]
        dev1 = vuln_endpoint_setup["dev1"]

        # Org2 listing vulnerabilities should be empty
        resp_list = client.get(
            "/api/v1/vulnerabilities/",
            headers={"Authorization": f"Bearer {token_org2}"},
        )
        assert resp_list.status_code == 200
        assert len(resp_list.json()) == 0

        # Org2 getting Org1's vulnerability ID returns 404
        resp_get = client.get(
            f"/api/v1/vulnerabilities/{vuln1.id}",
            headers={"Authorization": f"Bearer {token_org2}"},
        )
        assert resp_get.status_code == 404
        assert resp_get.json()["error"]["code"] == "NOT_FOUND"

        # Org2 getting Org1's device vulnerabilities returns 404
        resp_dev = client.get(
            f"/api/v1/devices/{dev1.id}/vulnerabilities",
            headers={"Authorization": f"Bearer {token_org2}"},
        )
        assert resp_dev.status_code == 404
        assert resp_dev.json()["error"]["code"] == "NOT_FOUND"


class TestVulnerabilityScanningIntegration:
    def test_full_vulnerability_scanning_lifecycle(self, db_session):
        """End-to-end integration test covering scan trigger, task polling, agent upload, matching, and retrieval."""
        from app.core.security import create_access_token, hash_password
        from app.core.seed import CANONICAL_ROLES

        uid = uuid.uuid4().hex[:8]
        org = Organization(name=f"IntegVulnOrg-{uid}", slug=f"integ-vuln-org-{uid}")
        db_session.add(org)
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

        analyst = User(
            organization_id=org.id,
            role_id=roles["Security Analyst"].id,
            email=f"integ-analyst-{uid}@test.com",
            username=f"integ-analyst-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        viewer = User(
            organization_id=org.id,
            role_id=roles["Viewer"].id,
            email=f"integ-viewer-{uid}@test.com",
            username=f"integ-viewer-{uid}",
            password_hash=hash_password("Pass123!"),
            is_active=True,
        )
        agent = Agent(
            organization_id=org.id,
            name=f"integ-agent-{uid}",
            hostname="integ-host",
            status="ONLINE",
            is_active=True,
        )
        db_session.add_all([analyst, viewer, agent])
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

        # Step 1: Ensure CVEs are seeded
        seed_count = db_session.query(CVE).count()
        if seed_count < 10:
            seed_cves(db=db_session, organization_id=org.id)
            seed_count = db_session.query(CVE).count()
        assert seed_count >= 10
        db_session.commit()

        token_analyst = create_access_token(str(analyst.id), "Security Analyst", str(org.id))
        token_viewer = create_access_token(str(viewer.id), "Viewer", str(org.id))

        # Step 2: Analyst creates vulnerability scan via POST /api/v1/scans/
        create_scan_resp = client.post(
            "/api/v1/scans/",
            headers={"Authorization": f"Bearer {token_analyst}"},
            json={
                "agent_id": str(agent.id),
                "scan_type": "vulnerability",
                "target_scope": "192.168.1.150",
            },
        )
        assert create_scan_resp.status_code == 201, create_scan_resp.text
        scan_id = create_scan_resp.json()["id"]

        # Step 3: Agent polls task via GET /api/v1/agents/tasks
        poll_resp = client.get(
            "/api/v1/agents/tasks",
            headers={"Authorization": f"Bearer {raw_cred}"},
        )
        assert poll_resp.status_code == 200
        tasks = poll_resp.json()
        assert any(t["id"] == scan_id for t in tasks)

        # Mark task RUNNING
        client.post(
            f"/api/v1/agents/tasks/{scan_id}/status",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json={"status": "RUNNING"},
        )

        # Step 4: Agent uploads result via POST /api/v1/agents/results with result_type="services"
        upload_resp = client.post(
            "/api/v1/agents/results",
            headers={"Authorization": f"Bearer {raw_cred}"},
            json={
                "scan_id": scan_id,
                "upload_id": str(uuid.uuid4()),
                "result_type": "services",
                "raw_payload": {
                    "target_ip": "192.168.1.150",
                    "services": [
                        {
                            "port": 80,
                            "protocol": "tcp",
                            "service": "http",
                            "version": "Apache httpd 2.4.49",
                            "state": "open",
                        },
                        {
                            "port": 21,
                            "protocol": "tcp",
                            "service": "vsftpd",
                            "version": "2.3.4",
                            "state": "open",
                        },
                    ],
                },
            },
        )
        assert upload_resp.status_code == 201, upload_resp.text
        upload_data = upload_resp.json()
        assert upload_data["result_type"] == "services"
        assert upload_data["device_id"] is not None
        device_id = upload_data["device_id"]

        # Step 5: Verify scan status is COMPLETED
        scan_check = client.get(
            f"/api/v1/scans/{scan_id}",
            headers={"Authorization": f"Bearer {token_analyst}"},
        )
        assert scan_check.status_code == 200
        assert scan_check.json()["status"] == "COMPLETED"

        # Step 6: Viewer queries GET /api/v1/vulnerabilities/
        list_vulns_resp = client.get(
            "/api/v1/vulnerabilities/",
            headers={"Authorization": f"Bearer {token_viewer}"},
        )
        assert list_vulns_resp.status_code == 200
        vulns_list = list_vulns_resp.json()
        assert len(vulns_list) >= 2
        detected_cves = {v["cve_code"] for v in vulns_list}
        assert "CVE-2021-41773" in detected_cves
        assert "CVE-2011-2523" in detected_cves

        # Step 7: Viewer queries GET /api/v1/devices/{device_id}/vulnerabilities
        device_vulns_resp = client.get(
            f"/api/v1/devices/{device_id}/vulnerabilities",
            headers={"Authorization": f"Bearer {token_viewer}"},
        )
        assert device_vulns_resp.status_code == 200
        device_vulns = device_vulns_resp.json()
        assert len(device_vulns) >= 2
        for v in device_vulns:
            assert v["device_id"] == str(device_id)
            assert v["status"] == "open"


