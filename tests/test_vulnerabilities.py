"""
Test suite for Phase 13 — Vulnerability Scanning.
Covers CVE seed data, vulnerability processing, and endpoints.
"""

import uuid
import pytest
from app.core.seed import seed_cves
from app.models.organization import Organization
from app.models.scan import CVE


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
