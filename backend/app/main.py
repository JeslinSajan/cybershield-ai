"""
CyberShield AI Backend - FastAPI Application Foundation

Phase 7: Backend infrastructure and database foundation
- Configuration management
- Database connectivity
- API v1 router structure
- Health check endpoints
- Error handling
- Structured logging
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db, close_db, test_db_connection
from app.core.logging import configure_logging
from app.core.exceptions import CyberShieldException, ErrorResponse
from app.api.v1.router import router as api_v1_router
from app.schemas import RootResponse

# Configure logging early
logger = configure_logging()
logger.info("CyberShield AI Backend starting...")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    
    Startup:
    - Initialize database connection
    - Test database connectivity
    - Log startup information
    
    Shutdown:
    - Close database connections
    - Clean up resources
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize database
    init_db()
    logger.info("Database engine initialized")
    
    # Test database connection
    db_ok = await test_db_connection()
    if db_ok:
        logger.info("✓ Database connectivity verified")
    else:
        logger.warning("✗ Database connectivity check failed (will retry on first request)")
    
    logger.info(f"{settings.APP_NAME} startup complete")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")
    await close_db()
    logger.info("Database connections closed")
    logger.info(f"{settings.APP_NAME} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CyberShield AI - Unified Cybersecurity Monitoring and Threat Management Platform",
    lifespan=lifespan
)

# Configure CORS if origins are specified
if settings.CORS_ORIGINS:
    try:
        origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS.split(",") if settings.CORS_ALLOW_METHODS else ["*"],
            allow_headers=settings.CORS_ALLOW_HEADERS.split(",") if settings.CORS_ALLOW_HEADERS else ["*"],
        )
        logger.info(f"CORS configured for origins: {origins}")
    except Exception as e:
        logger.warning(f"Failed to configure CORS: {str(e)}")
else:
    # Default CORS for local development
    if settings.ENVIRONMENT == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS configured for development (all origins allowed)")


# Exception handlers
@app.exception_handler(CyberShieldException)
async def cybershield_exception_handler(request: Request, exc: CyberShieldException):
    """Handle CyberShield-specific exceptions."""
    logger.error(f"CyberShield exception: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.to_dict(exc.code, exc.message, exc.details)
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.to_dict(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
            []
        )
    )


# Root endpoint
@app.get(
    "/",
    response_model=RootResponse,
    summary="Root endpoint",
    description="Application information and status"
)
async def root() -> RootResponse:
    """
    Root endpoint providing basic application information.
    
    Returns:
        RootResponse: Application name, version, and status
    """
    return RootResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        status="running"
    )


# Include API v1 router
app.include_router(api_v1_router, prefix="/api/v1")

logger.info("FastAPI application configured successfully")
