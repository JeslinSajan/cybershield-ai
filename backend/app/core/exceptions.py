"""Centralized exception handling for CyberShield AI."""

from fastapi import HTTPException, status
from typing import Optional, Any, Dict, List


class CyberShieldException(Exception):
    """Base exception for all CyberShield AI errors."""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[List[str]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(self.message)


class ValidationException(CyberShieldException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[List[str]] = None
    ):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class NotAuthenticatedException(CyberShieldException):
    """Exception for authentication failures (reserved for Phase 8)."""
    
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(
            code="NOT_AUTHENTICATED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class NotAuthorizedException(CyberShieldException):
    """Exception for authorization failures (reserved for Phase 8)."""
    
    def __init__(self, message: str = "Not authorized"):
        super().__init__(
            code="NOT_AUTHORIZED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(CyberShieldException):
    """Exception when a resource is not found."""
    
    def __init__(
        self,
        resource: str = "Resource",
        message: Optional[str] = None
    ):
        msg = message or f"{resource} not found"
        super().__init__(
            code="NOT_FOUND",
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictException(CyberShieldException):
    """Exception for resource conflicts."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[List[str]] = None
    ):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class DatabaseException(CyberShieldException):
    """Exception for database errors."""
    
    def __init__(self, message: str = "Database error"):
        super().__init__(
            code="DATABASE_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ExternalServiceException(CyberShieldException):
    """Exception for external service failures."""
    
    def __init__(
        self,
        service: str,
        message: Optional[str] = None
    ):
        msg = message or f"External service '{service}' error"
        super().__init__(
            code="EXTERNAL_SERVICE_ERROR",
            message=msg,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ErrorResponse:
    """Standardized error response format."""
    
    @staticmethod
    def to_dict(
        code: str,
        message: str,
        details: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Convert error to response dictionary."""
        return {
            "error": {
                "code": code,
                "message": message,
                "details": details or []
            }
        }


def exception_to_http_exception(exc: CyberShieldException) -> HTTPException:
    """Convert CyberShieldException to HTTPException."""
    return HTTPException(
        status_code=exc.status_code,
        detail=ErrorResponse.to_dict(exc.code, exc.message, exc.details)
    )
