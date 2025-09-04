"""
Pydantic models for API response validation
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Status of assessment processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorType(str, Enum):
    """Types of errors that can occur."""
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    FILE_ERROR = "file_error"
    SYSTEM_ERROR = "system_error"
    NOT_FOUND = "not_found"


class APIError(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_type: ErrorType = Field(..., description="Type of error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessingStage(BaseModel):
    """Information about a processing stage."""
    stage_name: str = Field(..., description="Name of the processing stage")
    status: ProcessingStatus = Field(..., description="Status of this stage")
    started_at: Optional[datetime] = Field(None, description="When stage started")
    completed_at: Optional[datetime] = Field(None, description="When stage completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class AssessmentMetrics(BaseModel):
    """Metrics from assessment processing."""
    total_participants: int = Field(..., description="Total number of participants")
    completion_rate: float = Field(..., description="Average completion rate")
    processing_time: float = Field(..., description="Total processing time in seconds")
    records_processed: int = Field(..., description="Number of records processed")
    clusters_created: int = Field(..., description="Number of clusters created")


class ArchetypeInfo(BaseModel):
    """Information about a psychological archetype."""
    archetype_name: str = Field(..., description="Name of the archetype")
    participant_count: int = Field(..., description="Number of participants in this archetype")
    percentage: float = Field(..., description="Percentage of total participants")
    description: Optional[str] = Field(None, description="Description of the archetype")


class OutputFiles(BaseModel):
    """Information about generated output files."""
    html_reports: List[str] = Field(default_factory=list, description="Generated HTML report files")
    pdf_reports: List[str] = Field(default_factory=list, description="Generated PDF report files")
    visualizations: List[str] = Field(default_factory=list, description="Generated visualization files")
    dashboard: Optional[str] = Field(None, description="Dashboard file path")
    archetype_map: Optional[str] = Field(None, description="Archetype map file path")
    individual_profiles: List[str] = Field(default_factory=list, description="Individual profile files")


class AssessmentResult(BaseModel):
    """Result of assessment processing."""
    assessment_id: str = Field(..., description="Unique assessment identifier")
    status: ProcessingStatus = Field(..., description="Processing status")
    file_path: str = Field(..., description="Path to processed file")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None, description="When processing completed")
    
    # Processing information
    stages: List[ProcessingStage] = Field(default_factory=list, description="Processing stages")
    metrics: Optional[AssessmentMetrics] = Field(None, description="Assessment metrics")
    
    # Results
    archetypes: List[ArchetypeInfo] = Field(default_factory=list, description="Identified archetypes")
    output_files: OutputFiles = Field(default_factory=OutputFiles, description="Generated files")
    
    # Error information
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")


class BatchAssessmentResult(BaseModel):
    """Result of batch assessment processing."""
    batch_id: str = Field(..., description="Unique batch identifier")
    status: ProcessingStatus = Field(..., description="Overall batch status")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None, description="When batch completed")
    
    # Batch summary
    total_files: int = Field(..., description="Total number of files")
    successful_files: int = Field(..., description="Number of successfully processed files")
    failed_files: int = Field(..., description="Number of failed files")
    
    # Individual results
    file_results: List[AssessmentResult] = Field(default_factory=list, description="Individual file results")
    
    # Batch metrics
    batch_metrics: Optional[AssessmentMetrics] = Field(None, description="Aggregated batch metrics")
    
    # Combined outputs
    combined_outputs: Optional[OutputFiles] = Field(None, description="Combined batch outputs")


class ReportResponse(BaseModel):
    """Response for report generation."""
    report_id: str = Field(..., description="Unique report identifier")
    assessment_id: str = Field(..., description="Associated assessment ID")
    format: str = Field(..., description="Report format")
    file_path: str = Field(..., description="Path to generated report")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(default_factory=datetime.now)
    download_url: Optional[str] = Field(None, description="URL for downloading report")


class VisualizationResponse(BaseModel):
    """Response for visualization generation."""
    visualization_id: str = Field(..., description="Unique visualization identifier")
    assessment_id: str = Field(..., description="Associated assessment ID")
    visualization_type: str = Field(..., description="Type of visualization")
    file_path: str = Field(..., description="Path to generated visualization")
    created_at: datetime = Field(default_factory=datetime.now)
    view_url: Optional[str] = Field(None, description="URL for viewing visualization")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.now)
    components: Optional[Dict[str, str]] = Field(None, description="Component health status")


class StatusResponse(BaseModel):
    """Processing status response."""
    assessment_id: str = Field(..., description="Assessment ID")
    status: ProcessingStatus = Field(..., description="Current processing status")
    progress: float = Field(..., description="Processing progress (0-100)")
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    details: Optional[Dict[str, Any]] = Field(None, description="Detailed processing information")


class FileUploadResponse(BaseModel):
    """Response for file upload."""
    upload_id: str = Field(..., description="Unique upload identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    temp_path: str = Field(..., description="Temporary file path")
    uploaded_at: datetime = Field(default_factory=datetime.now)


class BatchUploadResponse(BaseModel):
    """Response for batch file upload."""
    batch_upload_id: str = Field(..., description="Unique batch upload identifier")
    files: List[FileUploadResponse] = Field(..., description="Individual file upload responses")
    total_files: int = Field(..., description="Total number of files")
    total_size: int = Field(..., description="Total size of all files")
    uploaded_at: datetime = Field(default_factory=datetime.now)


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Union[
        AssessmentResult,
        BatchAssessmentResult,
        ReportResponse,
        VisualizationResponse,
        HealthResponse,
        StatusResponse,
        FileUploadResponse,
        BatchUploadResponse
    ]] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    errors: List[APIError] = Field(default_factory=list, description="Error information")
    timestamp: datetime = Field(default_factory=datetime.now)


class ConfigResponse(BaseModel):
    """Configuration response."""
    config: Dict[str, Any] = Field(..., description="Current configuration")
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(..., description="Configuration version")