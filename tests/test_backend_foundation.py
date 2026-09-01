"""
Foundation tests for CyberShield AI Phase 7

Tests for:
- Configuration loading
- Database layer
- Model imports
- API structure
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.config import get_settings


# Test database URL (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


class TestConfiguration:
    """Test configuration loading."""
    
    def test_settings_loaded(self):
        """Test that settings are loaded."""
        settings = get_settings()
        assert settings is not None
    
    def test_required_settings(self):
        """Test that required settings are present."""
        settings = get_settings()
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'APP_VERSION')
    
    def test_app_name(self):
        """Test app name setting."""
        settings = get_settings()
        assert settings.APP_NAME == "CyberShield AI"
    
    def test_app_version(self):
        """Test app version setting."""
        settings = get_settings()
        assert settings.APP_VERSION == "0.1.0"


class TestDatabaseLayer:
    """Test database layer functionality."""
    
    def test_database_connection(self):
        """Test that database connection works."""
        db = TestingSessionLocal()
        try:
            result = db.execute(text("SELECT 1"))
            assert result is not None
        finally:
            db.close()
    
    def test_models_imported(self):
        """Test that all models are imported."""
        # Import all models to verify no import errors
        from app.models import (
            Organization, Role, Permission, RolePermission,
            User, Agent, AgentCredential, AgentHeartbeat,
            Device, DeviceInterface, Scan, ScanResult, CVE, Vulnerability,
            Log, ThreatIndicator, Alert, AlertEvent, RiskScore,
            Report, AIConversation, AIMessage,
            Notification, AuditLog, SystemSetting
        )
        assert Organization is not None
        assert User is not None
        assert Agent is not None
    
    def test_metadata_tables_count(self):
        """Test that metadata contains expected number of tables."""
        # Should have 25 tables defined
        table_count = len(Base.metadata.tables)
        assert table_count == 25, f"Expected 25 tables, got {table_count}"
    
    def test_expected_tables_exist(self):
        """Test that all expected tables are defined."""
        expected_tables = [
            'organizations', 'roles', 'permissions', 'role_permissions',
            'users', 'agents', 'agent_credentials', 'agent_heartbeats',
            'devices', 'device_interfaces',
            'scans', 'scan_results', 'cves', 'vulnerabilities',
            'logs', 'threat_indicators',
            'alerts', 'alert_events', 'risk_scores',
            'reports', 'ai_conversations', 'ai_messages',
            'notifications', 'audit_logs', 'system_settings'
        ]
        metadata_tables = set(Base.metadata.tables.keys())
        for table in expected_tables:
            assert table in metadata_tables, f"Missing table: {table}"


class TestApplicationImports:
    """Test FastAPI application imports."""
    
    def test_app_imports(self):
        """Test that FastAPI app can be imported."""
        from app.main import app
        assert app is not None
    
    def test_app_title(self):
        """Test that app has correct title."""
        from app.main import app
        assert app.title == "CyberShield AI"
    
    def test_app_version(self):
        """Test that app has version."""
        from app.main import app
        assert app.version == "0.1.0"
    
    def test_app_routes_exist(self):
        """Test that expected routes are registered."""
        from app.main import app
        routes = [route.path for route in app.routes]
        
        # Check for key routes
        assert "/" in routes
        assert any("/health" in route for route in routes), "Health endpoint not found"


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_health_response_schema(self):
        """Test HealthResponse schema."""
        from app.schemas import HealthResponse
        resp = HealthResponse(status="healthy")
        assert resp.status == "healthy"
    
    def test_health_db_response_schema(self):
        """Test HealthDatabaseResponse schema."""
        from app.schemas import HealthDatabaseResponse
        resp = HealthDatabaseResponse(
            status="healthy",
            database="connected",
            message="Test"
        )
        assert resp.status == "healthy"
        assert resp.database == "connected"
    
    def test_root_response_schema(self):
        """Test RootResponse schema."""
        from app.schemas import RootResponse
        resp = RootResponse(
            name="Test",
            version="1.0",
            status="running"
        )
        assert resp.name == "Test"
        assert resp.version == "1.0"


class TestErrorHandling:
    """Test error handling components."""
    
    def test_exceptions_import(self):
        """Test that exception classes can be imported."""
        from app.core.exceptions import (
            CyberShieldException,
            ValidationException,
            NotFoundException,
            ErrorResponse
        )
        assert CyberShieldException is not None
        assert ErrorResponse is not None
    
    def test_validation_exception(self):
        """Test ValidationException."""
        from app.core.exceptions import ValidationException
        exc = ValidationException("Test validation error")
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == 400


class TestLogging:
    """Test logging configuration."""
    
    def test_logging_import(self):
        """Test that logging can be imported."""
        from app.core.logging import configure_logging, get_logger
        assert configure_logging is not None
        assert get_logger is not None
    
    def test_get_logger(self):
        """Test get_logger function."""
        from app.core.logging import get_logger
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "app.test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
