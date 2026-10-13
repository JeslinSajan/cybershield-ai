import json as _json_module
import uuid as _uuid_module
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import INET as PGINET, JSONB as PGJSONB, UUID as PGUUID
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQLite compatibility patching for PostgreSQL types (UUID, JSONB, INET)
# ---------------------------------------------------------------------------
def _visit_JSONB(self, type_, **kw):
    return "TEXT"

def _visit_UUID(self, type_, **kw):
    return "CHAR(36)"

def _visit_INET(self, type_, **kw):
    return "VARCHAR(45)"

SQLiteTypeCompiler.visit_JSONB = _visit_JSONB
SQLiteTypeCompiler.visit_UUID = _visit_UUID
SQLiteTypeCompiler.visit_INET = _visit_INET

if not getattr(PGUUID, "_sqlite_patched", False):
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
                return _json_module.dumps(value)
            return process
        return _orig_jsonb_bind_processor(self, dialect)

    def _jsonb_result_processor(self, dialect, coltype):
        if dialect.name == "sqlite":
            def process(value):
                if value is None:
                    return None
                try:
                    return _json_module.loads(value)
                except Exception:
                    return value
            return process
        return _orig_jsonb_result_processor(self, dialect, coltype)

    PGUUID.bind_processor = _uuid_bind_processor
    PGUUID.result_processor = _uuid_result_processor
    PGJSONB.bind_processor = _jsonb_bind_processor
    PGJSONB.result_processor = _jsonb_result_processor
    PGUUID._sqlite_patched = True

Base = declarative_base()

# Singleton engine and session factory
_engine = None
_SessionLocal = None


def _normalize_db_url(url: str) -> str:
    """
    Normalize the database URL to use the psycopg (v3) driver explicitly.

    SQLAlchemy defaults to psycopg2 when it sees "postgresql://".
    This project installs psycopg (v3) via psycopg[binary], not psycopg2.
    Neon and most PostgreSQL providers give connection strings with the
    plain "postgresql://" scheme, so we rewrite it here in code rather
    than requiring every environment (.env, Render dashboard, CI) to
    remember to use the correct dialect prefix.
    """
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Also handle "postgres://" (short alias sometimes used by Heroku/Neon)
    if url.startswith("postgres://") and not url.startswith("postgres+"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def get_engine():
    """Get or create database engine from settings."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = _normalize_db_url(settings.DATABASE_URL)
        if db_url.startswith("sqlite"):
            _engine = create_engine(db_url, connect_args={"check_same_thread": False}, echo=settings.DEBUG, future=True)
        else:
            _engine = create_engine(
                db_url, 
                pool_pre_ping=True, 
                pool_recycle=300, 
                pool_size=2, 
                max_overflow=3,
                connect_args={
                    "connect_timeout": 10, 
                    "keepalives": 1, 
                    "keepalives_idle": 30,
                    "keepalives_interval": 10, 
                    "keepalives_count": 5, 
                    "prepare_threshold": None
                },
                echo=settings.DEBUG, 
                future=True
            )
        logger.info("Database engine created successfully")
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=Session
        )
    return _SessionLocal


def SessionLocal():
    """Convenience function for background tasks that need a DB session."""
    return get_session_factory()()


def init_db():
    """Initialize database engine and session factory.
    If using SQLite (local dev), automatically ensure all tables are created.
    """
    engine = get_engine()
    _ = get_session_factory()
    settings = get_settings()
    db_url = _normalize_db_url(settings.DATABASE_URL)
    if db_url.startswith("sqlite"):
        import app.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite database tables verified/created")
    logger.info("Database initialization complete")


async def close_db():
    """Close database connections."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("Database connections closed")


def get_db():
    """Dependency for getting database sessions."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy.exc import OperationalError
import time
MAX_DB_RETRIES = 3

async def test_db_connection():
    """Test database connectivity."""
    for attempt in range(1, MAX_DB_RETRIES + 1):
        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except OperationalError as e:
            if attempt < MAX_DB_RETRIES:
                wait = attempt * 2
                logger.warning(f"DB connection attempt {attempt} failed, retrying in {wait}s")
                time.sleep(wait)
            else:
                logger.error(f"Database connection failed after {MAX_DB_RETRIES} attempts")
                return False
        except Exception as e:
            logger.error(f"Database connection test failed: {type(e).__name__}")
            return False
