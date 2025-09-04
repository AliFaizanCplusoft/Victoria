"""
Custom exception classes for the psychometric assessment API
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException


class PsychometricAPIException(HTTPException):
    """Base exception for psychometric API errors."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_type: str = "api_error",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_type = error_type


class FileValidationError(PsychometricAPIException):
    """Exception raised when file validation fails."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            detail=detail,
            error_type="file_validation_error",
            headers=headers
        )


class FileProcessingError(PsychometricAPIException):
    """Exception raised when file processing fails."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=422,
            detail=detail,
            error_type="file_processing_error",
            headers=headers
        )


class AssessmentNotFoundError(PsychometricAPIException):
    """Exception raised when assessment is not found."""
    
    def __init__(self, assessment_id: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=404,
            detail=f"Assessment with ID '{assessment_id}' not found",
            error_type="assessment_not_found",
            headers=headers
        )


class ReportNotFoundError(PsychometricAPIException):
    """Exception raised when report is not found."""
    
    def __init__(self, report_id: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=404,
            detail=f"Report with ID '{report_id}' not found",
            error_type="report_not_found",
            headers=headers
        )


class PipelineProcessingError(PsychometricAPIException):
    """Exception raised when pipeline processing fails."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=500,
            detail=detail,
            error_type="pipeline_processing_error",
            headers=headers
        )


class InvalidConfigurationError(PsychometricAPIException):
    """Exception raised when configuration is invalid."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            detail=detail,
            error_type="invalid_configuration",
            headers=headers
        )


class ServiceUnavailableError(PsychometricAPIException):
    """Exception raised when service is temporarily unavailable."""
    
    def __init__(self, detail: str = "Service temporarily unavailable", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=503,
            detail=detail,
            error_type="service_unavailable",
            headers=headers
        )


class RateLimitExceededError(PsychometricAPIException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=429,
            detail=detail,
            error_type="rate_limit_exceeded",
            headers=headers
        )


class DataValidationError(PsychometricAPIException):
    """Exception raised when data validation fails."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            detail=detail,
            error_type="data_validation_error",
            headers=headers
        )


class InsufficientDataError(PsychometricAPIException):
    """Exception raised when there's insufficient data for analysis."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=400,
            detail=detail,
            error_type="insufficient_data_error",
            headers=headers
        )


class ConcurrencyError(PsychometricAPIException):
    """Exception raised when there's a concurrency issue."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=409,
            detail=detail,
            error_type="concurrency_error",
            headers=headers
        )


class AuthenticationError(PsychometricAPIException):
    """Exception raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication required", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=401,
            detail=detail,
            error_type="authentication_error",
            headers=headers
        )


class AuthorizationError(PsychometricAPIException):
    """Exception raised when authorization fails."""
    
    def __init__(self, detail: str = "Insufficient permissions", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=403,
            detail=detail,
            error_type="authorization_error",
            headers=headers
        )


class ResourceLimitError(PsychometricAPIException):
    """Exception raised when resource limits are exceeded."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=413,
            detail=detail,
            error_type="resource_limit_error",
            headers=headers
        )


class UnsupportedOperationError(PsychometricAPIException):
    """Exception raised when an operation is not supported."""
    
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=405,
            detail=detail,
            error_type="unsupported_operation_error",
            headers=headers
        )