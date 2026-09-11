"""
conftest.py — Shared test fixtures for Phase 8 tests.

SQLITE STRATEGY:
We patch the SQLiteTypeCompiler to handle PostgreSQL-specific types (JSONB, UUID)
by adding visit_JSONB and visit_UUID methods that map them to TEXT and CHAR(36).

For DML, we patch bind_processor and result_processor on the type instances
so UUID values are stored as strings and retrieved as uuid.UUID objects.

This approach patches at the compiler (DDL) and processor (DML) levels,
which is more reliable than patching class attributes that may not exist.
"""

import os
import uuid as _uuid_module
import json
import pytest
from sqlalchemy import create_engine, event, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB as PGJSONB, INET as PGINET


# ---------------------------------------------------------------------------
# 1. Patch SQLite compiler for DDL (CREATE TABLE)
# ---------------------------------------------------------------------------

def _visit_JSONB(self, type_, **kw):
    return "TEXT"

def _visit_UUID(self, type_, **kw):
    return "CHAR(36)"

def _visit_INET(self, type_, **kw):
    return "VARCHAR(45)"  # big enough for IPv6 addresses

SQLiteTypeCompiler.visit_JSONB = _visit_JSONB
SQLiteTypeCompiler.visit_UUID = _visit_UUID
SQLiteTypeCompiler.visit_INET = _visit_INET


# ---------------------------------------------------------------------------
# 2. Patch bind/result processors via SQLAlchemy events on connection
#    Using TypeDecorator approach: monkeypatch bind_processor/result_processor
# ---------------------------------------------------------------------------

_orig_uuid_bind_processor = PGUUID.bind_processor
_orig_uuid_result_processor = PGUUID.result_processor
_orig_jsonb_bind_processor = PGJSONB.bind_processor
_orig_jsonb_result_processor = PGJSONB.result_processor


def _uuid_bind_processor(self, dialect):
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            return str(value)
        return process
    return _orig_uuid_bind_processor(self, dialect)


def _uuid_result_processor(self, dialect, coltype):
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            try:
                return _uuid_module.UUID(str(value))
            except (ValueError, AttributeError):
                return value
        return process
    return _orig_uuid_result_processor(self, dialect, coltype)


def _jsonb_bind_processor(self, dialect):
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            return json.dumps(value)
        return process
    return _orig_jsonb_bind_processor(self, dialect)


def _jsonb_result_processor(self, dialect, coltype):
    if dialect.name == "sqlite":
        def process(value):
            if value is None:
                return None
            try:
                return json.loads(value)
            except Exception:
                return value
        return process
    return _orig_jsonb_result_processor(self, dialect, coltype)


PGUUID.bind_processor = _uuid_bind_processor
PGUUID.result_processor = _uuid_result_processor
PGJSONB.bind_processor = _jsonb_bind_processor
PGJSONB.result_processor = _jsonb_result_processor


# ---------------------------------------------------------------------------
# 3. Import app (models auto-register with Base.metadata)
# ---------------------------------------------------------------------------

from app.core.database import Base, get_db
from app.main import app as fastapi_app  # triggers all model imports


TEST_DB_URL = "sqlite:///./test_phase8.db"
_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = _override_get_db


# ---------------------------------------------------------------------------
# 4. Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables with SQLite-compatible type mappings."""
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)
    if os.path.exists("test_phase8.db"):
        try:
            os.remove("test_phase8.db")
        except PermissionError:
            pass  # Windows may keep the file open; it will be cleaned up on next run


@pytest.fixture(scope="session")
def db_session(create_tables):
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
