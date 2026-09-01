"""Pydantic response schemas for CyberShield AI."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


class ErrorDetail(BaseModel):
    """Error detail item."""
    code: str
    message: str
    details: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy"
        }
    })
    
    status: str = Field(..., description="Health status: 'healthy', 'degraded', or 'error'")


class HealthDatabaseResponse(BaseModel):
    """Health check response with database status."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "database": "connected",
            "message": "Database connection successful"
        }
    })
    
    status: str = Field(..., description="Health status: 'healthy', 'degraded', or 'error'")
    database: str = Field(..., description="Database connectivity status")
    message: Optional[str] = Field(None, description="Additional status message")


class RootResponse(BaseModel):
    """Root endpoint response."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "CyberShield AI",
            "version": "0.1.0",
            "status": "running"
        }
    })
    
    name: str
    version: str
    status: str


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of items to return")


# Response envelopes for future use
class ListResponse(BaseModel):
    """Generic list response envelope."""
    items: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int


class CreatedResponse(BaseModel):
    """Generic created resource response."""
    id: str
    created_at: str
