"""
Pydantic models for API request validation
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class AssessmentType(str, Enum):
    """Types of psychometric assessments."""
    SINGLE = "single"
    BATCH = "batch"


class FileType(str, Enum):
    """Supported file types for upload."""
    CSV = "csv"
    TXT = "txt"
    TYPEFORM = "typeform"


class ScoringMethod(str, Enum):
    """Available scoring methods."""
    RASCH = "rasch"
    STANDARDIZED = "standardized"


class ReportFormat(str, Enum):
    """Available report formats."""
    HTML = "html"
    PDF = "pdf"
    BOTH = "both"


class AssessmentConfigModel(BaseModel):
    """Configuration for assessment processing."""
    use_rasch_scoring: bool = Field(True, description="Use Rasch scoring method")
    min_completion_rate: float = Field(0.8, ge=0.0, le=1.0, description="Minimum completion rate")
    validation_enabled: bool = Field(True, description="Enable data validation")
    n_clusters: int = Field(5, ge=2, le=20, description="Number of clusters for analysis")
    optimize_clusters: bool = Field(True, description="Optimize cluster number automatically")
    generate_visualizations: bool = Field(True, description="Generate visualization files")
    generate_pdf: bool = Field(True, description="Generate PDF reports")
    include_narratives: bool = Field(True, description="Include narrative descriptions")
    
    @validator('min_completion_rate')
    def validate_completion_rate(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Completion rate must be between 0.0 and 1.0')
        return v


class SingleAssessmentRequest(BaseModel):
    """Request model for single person assessment."""
    file_type: Optional[FileType] = Field(None, description="Type of uploaded file")
    config: Optional[AssessmentConfigModel] = Field(None, description="Assessment configuration")
    
    class Config:
        json_encoders = {
            FileType: lambda v: v.value,
            AssessmentConfigModel: lambda v: v.dict()
        }


class BatchAssessmentRequest(BaseModel):
    """Request model for batch assessment."""
    file_type: Optional[FileType] = Field(None, description="Type of uploaded files")
    config: Optional[AssessmentConfigModel] = Field(None, description="Assessment configuration")
    
    class Config:
        json_encoders = {
            FileType: lambda v: v.value,
            AssessmentConfigModel: lambda v: v.dict()
        }


class ReportRequest(BaseModel):
    """Request model for report generation."""
    assessment_id: str = Field(..., description="Assessment ID")
    format: ReportFormat = Field(ReportFormat.HTML, description="Report format")
    include_visualizations: bool = Field(True, description="Include visualizations in report")
    
    class Config:
        json_encoders = {
            ReportFormat: lambda v: v.value
        }


class VisualizationRequest(BaseModel):
    """Request model for visualization generation."""
    assessment_id: str = Field(..., description="Assessment ID")
    visualization_type: str = Field("dashboard", description="Type of visualization")
    theme: str = Field("plotly_white", description="Chart theme")
    
    @validator('visualization_type')
    def validate_visualization_type(cls, v):
        allowed_types = ["dashboard", "archetype_map", "individual_profile", "cluster_analysis"]
        if v not in allowed_types:
            raise ValueError(f'Visualization type must be one of: {allowed_types}')
        return v


class FileUploadMetadata(BaseModel):
    """Metadata for file uploads."""
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    
    @validator('file_size')
    def validate_file_size(cls, v):
        # Maximum file size: 50MB
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        if v > max_size:
            raise ValueError(f'File size must be less than 50MB (got {v} bytes)')
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = ['text/csv', 'text/plain', 'application/csv']
        if v not in allowed_types:
            raise ValueError(f'Content type must be one of: {allowed_types}')
        return v


class BatchFileMetadata(BaseModel):
    """Metadata for batch file uploads."""
    files: List[FileUploadMetadata] = Field(..., description="List of file metadata")
    total_size: int = Field(..., description="Total size of all files")
    
    @validator('total_size')
    def validate_total_size(cls, v):
        # Maximum total size: 200MB
        max_size = 200 * 1024 * 1024  # 200MB in bytes
        if v > max_size:
            raise ValueError(f'Total file size must be less than 200MB (got {v} bytes)')
        return v
    
    @validator('files')
    def validate_files_count(cls, v):
        if len(v) > 50:
            raise ValueError('Cannot process more than 50 files in a single batch')
        return v


class ConfigUpdateRequest(BaseModel):
    """Request model for updating assessment configuration."""
    config: AssessmentConfigModel = Field(..., description="Updated configuration")


class StatusRequest(BaseModel):
    """Request model for checking processing status."""
    assessment_id: str = Field(..., description="Assessment ID to check")
    include_details: bool = Field(False, description="Include detailed processing information")