"""
Authentication security tests — Phase 8.

Uses conftest.py for SQLite-compatible DB setup (UUID/JSONB patched).
Tests run against the full ORM models via the overridden get_db dependency.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password, create_access_token, decode_access_token
from app.core.seed import CANONICAL_ROLES
from app.models.organization import Organization, Role
from app.models.user import User

# TestClient is created per test using the fixture
# conftest.py handles DB setup and get_db override


@pytest.fixture(scope="module")
def seeded_data(create_tables, db_session):
    """Seed org and 3 canonical roles once for the whole module."""
    db = db_session
    org = Organization(name="Auth Test Org", slug=f"auth-test-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()

    roles = {}
    for name, desc in CANONICAL_ROLES:
        existing = db.query(Role).filter(Role.name == name).first()
        if existing:
            roles[name] = existing
        else:
            r = Role(name=name, description=desc)
            db.add(r)
            db.flush()
            roles[name] = r

    db.commit()
    return {"org": org, "roles": roles}


def _make_user(db: Session, org_id, role: Role, email: str, password: str = "TestPass!123") -> User:
    u = User(
        organization_id=org_id,
        role_id=role.id,
        email=email,
        username=email.split("@")[0],
        password_hash=hash_password(password),
        is_active=True,
        failed_login_count=0,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def client():
    return TestClient(__import__("app.main", fromlist=["app"]).app)


@pytest.fixture()
def db(db_session):
    return db_session


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

class TestLogin:
    def test_correct_credentials_returns_200_and_jwt(self, client, db, seeded_data):
        role = seeded_data["roles"]["Security Analyst"]
        email = f"analyst_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)

        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass!123"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == email
        assert "password_hash" not in data["user"]

        payload = decode_access_token(data["token"])
        assert payload["sub"] == str(user.id)

    def test_wrong_password_returns_401(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"viewer_{uuid.uuid4().hex[:6]}@test.com"
        _make_user(db, seeded_data["org"].id, role, email)

        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword!"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_wrong_password_increments_failed_count(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"viewer_count_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)

        client.post("/api/v1/auth/login", json={"email": email, "password": "Wrong!"})
        db.refresh(user)
        assert user.failed_login_count == 1

        client.post("/api/v1/auth/login", json={"email": email, "password": "Wrong!"})
        db.refresh(user)
        assert user.failed_login_count == 2

    def test_nonexistent_email_returns_401(self, client):
        resp = client.post("/api/v1/auth/login",
                           json={"email": "doesnotexist@noreply.com", "password": "anything"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_successful_login_resets_failed_count(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"viewer_reset_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)

        user.failed_login_count = 3
        user.last_failed_at = datetime.now(timezone.utc)
        db.commit()

        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass!123"})
        assert resp.status_code == 200
        db.refresh(user)
        assert user.failed_login_count == 0
        assert user.last_failed_at is None

    def test_deactivated_account_returns_401(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"viewer_deact_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)
        user.is_active = False
        db.commit()

        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass!123"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "ACCOUNT_DEACTIVATED"


# ---------------------------------------------------------------------------
# Lockout tests
# ---------------------------------------------------------------------------

class TestLockout:
    def test_five_failures_locks_account(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"viewer_lock_{uuid.uuid4().hex[:6]}@test.com"
        _make_user(db, seeded_data["org"].id, role, email)

        for _ in range(5):
            client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass!"})

        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass!"})
        assert resp.status_code == 423
        assert resp.json()["error"]["code"] == "ACCOUNT_LOCKED"

    def test_correct_password_blocked_when_locked(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"viewer_lock2_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)
        user.failed_login_count = 5
        user.last_failed_at = datetime.now(timezone.utc)
        db.commit()

        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass!123"})
        assert resp.status_code == 423

    def test_lockout_expires_after_window(self, client, db, seeded_data):
        """FR-1.5 expiry: 5 failures 12 min ago → window expired → NOT 423.
        Wrong password after expiry → 401 + count resets to 1.
        Correct password after expiry → 200.
        """
        role = seeded_data["roles"]["Viewer"]
        email = f"viewer_expiry_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)
        user.failed_login_count = 5
        user.last_failed_at = datetime.now(timezone.utc) - timedelta(minutes=12)
        db.commit()

        # Wrong password — window expired, should NOT be 423
        resp = client.post("/api/v1/auth/login",
                           json={"email": email, "password": "WrongAfterExpiry!"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.json()}"
        db.refresh(user)
        assert user.failed_login_count == 1, "Count should reset to 1 on first failure of new window"

        # Correct password → 200
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass!123"})
        assert resp.status_code == 200
        db.refresh(user)
        assert user.failed_login_count == 0

    def test_lockout_window_boundary_still_locked(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"viewer_boundary_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)
        user.failed_login_count = 5
        user.last_failed_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass!123"})
        assert resp.status_code == 423


# ---------------------------------------------------------------------------
# /auth/me tests
# ---------------------------------------------------------------------------

class TestAuthMe:
    def _login(self, client, db, seeded_data, prefix: str) -> tuple:
        role = seeded_data["roles"]["Security Analyst"]
        email = f"{prefix}_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass!123"})
        return user, resp.json()["token"]

    def test_me_with_valid_token(self, client, db, seeded_data):
        user, token = self._login(client, db, seeded_data, "me_user")
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == user.email
        assert "password_hash" not in data

    def test_me_without_token_returns_401(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_malformed_token_returns_401(self, client):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not_a_real_token"})
        assert resp.status_code == 401

    def test_me_with_expired_token_returns_401(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"expired_{uuid.uuid4().hex[:6]}@test.com"
        user = _make_user(db, seeded_data["org"].id, role, email)

        expired_token = create_access_token(
            subject=str(user.id),
            role_name="Viewer",
            organization_id=str(user.organization_id),
            expires_delta=timedelta(hours=-1),
        )
        resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_with_valid_token_returns_204(self, client, db, seeded_data):
        role = seeded_data["roles"]["Viewer"]
        email = f"logout_{uuid.uuid4().hex[:6]}@test.com"
        _make_user(db, seeded_data["org"].id, role, email)
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass!123"})
        token = resp.json()["token"]

        resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    def test_logout_without_token_returns_401(self, client):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401
