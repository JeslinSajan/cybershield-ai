from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

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
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
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


def init_db():
    """Initialize database engine and session factory."""
    _ = get_engine()
    _ = get_session_factory()
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


async def test_db_connection():
    """Test database connectivity."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False
