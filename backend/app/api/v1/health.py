"""Health check endpoints for CyberShield AI."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.schemas import HealthResponse, HealthDatabaseResponse
from app.core.logging import get_logger

logger = get_logger("api.v1.health")

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application health check",
    description="Verify that the FastAPI application is running"
)
async def health() -> HealthResponse:
    """
    Basic health check - no database dependency.
    
    Returns:
        HealthResponse: Application status
    """
    logger.info("Health check requested")
    return HealthResponse(status="healthy")


@router.get(
    "/db",
    response_model=HealthDatabaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Database health check",
    description="Verify database connectivity and schema"
)
async def health_db(db: Session = Depends(get_db)) -> HealthDatabaseResponse:
    """
    Database health check - verifies connection and schema.
    
    Args:
        db: Database session (injected)
    
    Returns:
        HealthDatabaseResponse: Database status
        
    Raises:
        HTTPException: If database is unavailable
    """
    try:
        logger.info("Database health check requested")
        
        # Simple query to verify database connection
        result = db.execute(text("SELECT 1"))
        if result:
            logger.info("Database health check successful")
            return HealthDatabaseResponse(
                status="healthy",
                database="connected",
                message="Database connection successful"
            )
        else:
            logger.warning("Database health check returned no result")
            return HealthDatabaseResponse(
                status="degraded",
                database="connected",
                message="Database query returned no result"
            )
            
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return HealthDatabaseResponse(
            status="error",
            database="disconnected",
            message=f"Database connection failed: {type(e).__name__}"
        )
