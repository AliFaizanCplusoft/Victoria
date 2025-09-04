"""
Assessment endpoints for the psychometric API
"""

import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.request_models import SingleAssessmentRequest, BatchAssessmentRequest, AssessmentConfigModel
from ..models.response_models import (
    AssessmentResult, BatchAssessmentResult, StatusResponse, 
    FileUploadResponse, BatchUploadResponse, ProcessingStatus
)
from ..services.file_handler import FileHandler
from ..services.pipeline_service import PipelineService
from ..utils.exceptions import (
    FileValidationError, FileProcessingError, AssessmentNotFoundError,
    PipelineProcessingError, InsufficientDataError
)
from ..utils.validators import validate_assessment_id

# Initialize router
router = APIRouter()

# Logger
logger = logging.getLogger(__name__)

# Global service instances (initialized lazily)
# Note: These are reset to None to force re-initialization after code changes
_file_handler = None
_pipeline_service = None


def get_file_handler() -> FileHandler:
    """Dependency to get file handler instance."""
    global _file_handler
    if _file_handler is None:
        _file_handler = FileHandler()
    return _file_handler


def get_pipeline_service() -> PipelineService:
    """Dependency to get pipeline service instance."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service


@router.post("/assess/single", response_model=AssessmentResult)
async def assess_single_person(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV or TXT file containing psychometric data"),
    config: Optional[str] = Form(None, description="JSON configuration for assessment"),
    file_handler: FileHandler = Depends(get_file_handler),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Process a single person's psychometric assessment.
    
    This endpoint accepts a CSV or TXT file containing psychometric assessment data
    and processes it through the complete pipeline including scoring, clustering,
    visualization, and report generation.
    
    Args:
        file: Uploaded file containing assessment data
        config: Optional JSON configuration for processing
        background_tasks: Background task manager
        file_handler: File handling service
        pipeline_service: Pipeline processing service
        
    Returns:
        Assessment result with processing status and output files
        
    Raises:
        HTTPException: If file validation or processing fails
    """
    try:
        # Generate assessment ID
        assessment_id = str(uuid.uuid4())
        
        logger.info(f"Starting single assessment: {assessment_id}")
        
        # Save uploaded file
        file_info = await file_handler.save_uploaded_file(file, assessment_id)
        
        # Parse configuration if provided
        assessment_config = None
        if config and config.strip() and config.strip() != "string":
            import json
            try:
                config_dict = json.loads(config)
                assessment_config = AssessmentConfigModel(**config_dict).dict()
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Invalid configuration JSON, using defaults: {str(e)}")
                # Use default configuration instead of failing
                assessment_config = None
        
        # Move file to processing directory
        processing_path = file_handler.move_to_processing(
            file_info["temp_path"], 
            assessment_id
        )
        
        # Process assessment
        result = await pipeline_service.process_single_assessment(
            processing_path,
            assessment_id,
            assessment_config
        )
        
        # Schedule cleanup
        background_tasks.add_task(
            file_handler.delete_file, 
            processing_path
        )
        
        logger.info(f"Single assessment completed: {assessment_id}")
        return result
        
    except FileValidationError as e:
        logger.error(f"File validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileProcessingError as e:
        logger.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except PipelineProcessingError as e:
        logger.error(f"Pipeline processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in single assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/assess/batch", response_model=BatchAssessmentResult)
async def assess_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="List of CSV or TXT files"),
    config: Optional[str] = Form(None, description="JSON configuration for assessment"),
    file_handler: FileHandler = Depends(get_file_handler),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Process multiple psychometric assessments in batch.
    
    This endpoint accepts multiple CSV or TXT files and processes them through
    the complete pipeline, generating combined reports and visualizations.
    
    Args:
        files: List of uploaded files containing assessment data
        config: Optional JSON configuration for processing
        background_tasks: Background task manager
        file_handler: File handling service
        pipeline_service: Pipeline processing service
        
    Returns:
        Batch assessment result with processing status and output files
        
    Raises:
        HTTPException: If file validation or processing fails
    """
    try:
        # Generate batch ID
        batch_id = str(uuid.uuid4())
        
        logger.info(f"Starting batch assessment: {batch_id}, files: {len(files)}")
        
        # Save uploaded files
        batch_info = await file_handler.save_batch_files(files, batch_id)
        
        # Parse configuration if provided
        assessment_config = None
        if config and config.strip() and config.strip() != "string":
            import json
            try:
                config_dict = json.loads(config)
                assessment_config = AssessmentConfigModel(**config_dict).dict()
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Invalid configuration JSON, using defaults: {str(e)}")
                # Use default configuration instead of failing
                assessment_config = None
        
        # Move files to processing directory
        processing_paths = []
        for file_info in batch_info["files"]:
            processing_path = file_handler.move_to_processing(
                file_info["temp_path"], 
                batch_id
            )
            processing_paths.append(processing_path)
        
        # Process batch assessment
        result = await pipeline_service.process_batch_assessment(
            processing_paths,
            batch_id,
            assessment_config
        )
        
        # Schedule cleanup
        for path in processing_paths:
            background_tasks.add_task(file_handler.delete_file, path)
        
        logger.info(f"Batch assessment completed: {batch_id}")
        return result
        
    except FileValidationError as e:
        logger.error(f"File validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileProcessingError as e:
        logger.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except PipelineProcessingError as e:
        logger.error(f"Pipeline processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in batch assessment: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/assess/{assessment_id}/status", response_model=StatusResponse)
async def get_assessment_status(
    assessment_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Get the current processing status of an assessment.
    
    Args:
        assessment_id: Unique assessment identifier
        pipeline_service: Pipeline processing service
        
    Returns:
        Current processing status and progress information
        
    Raises:
        HTTPException: If assessment not found
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        status_info = pipeline_service.get_assessment_status(assessment_id)
        
        if not status_info:
            raise AssessmentNotFoundError(assessment_id)
        
        return StatusResponse(
            assessment_id=assessment_id,
            status=status_info.get("status", ProcessingStatus.PENDING),
            progress=status_info.get("progress", 0.0),
            current_stage=status_info.get("current_stage"),
            estimated_completion=status_info.get("estimated_completion"),
            details=status_info
        )
        
    except AssessmentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Assessment {assessment_id} not found")
    except Exception as e:
        logger.error(f"Error getting assessment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/assess/{assessment_id}")
async def cancel_assessment(
    assessment_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Cancel a running assessment.
    
    Args:
        assessment_id: Unique assessment identifier
        pipeline_service: Pipeline processing service
        
    Returns:
        Cancellation confirmation
        
    Raises:
        HTTPException: If assessment not found or cannot be cancelled
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        success = pipeline_service.cancel_assessment(assessment_id)
        
        if not success:
            raise AssessmentNotFoundError(assessment_id)
        
        return {"message": f"Assessment {assessment_id} cancelled successfully"}
        
    except AssessmentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Assessment {assessment_id} not found")
    except Exception as e:
        logger.error(f"Error cancelling assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload/single", response_model=FileUploadResponse)
async def upload_single_file(
    file: UploadFile = File(..., description="CSV or TXT file to upload"),
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Upload a single file for later processing.
    
    Args:
        file: File to upload
        file_handler: File handling service
        
    Returns:
        File upload information
        
    Raises:
        HTTPException: If file upload fails
    """
    try:
        file_info = await file_handler.save_uploaded_file(file)
        
        return FileUploadResponse(
            upload_id=file_info["file_id"],
            filename=file_info["original_name"],
            file_size=file_info["file_size"],
            content_type=file_info["content_type"],
            temp_path=file_info["temp_path"]
        )
        
    except FileValidationError as e:
        logger.error(f"File validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileProcessingError as e:
        logger.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_batch_files(
    files: List[UploadFile] = File(..., description="List of CSV or TXT files to upload"),
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Upload multiple files for later processing.
    
    Args:
        files: List of files to upload
        file_handler: File handling service
        
    Returns:
        Batch file upload information
        
    Raises:
        HTTPException: If file upload fails
    """
    try:
        batch_info = await file_handler.save_batch_files(files)
        
        file_responses = []
        for file_info in batch_info["files"]:
            file_responses.append(FileUploadResponse(
                upload_id=file_info["file_id"],
                filename=file_info["original_name"],
                file_size=file_info["file_size"],
                content_type=file_info["content_type"],
                temp_path=file_info["temp_path"]
            ))
        
        return BatchUploadResponse(
            batch_upload_id=batch_info["batch_id"],
            files=file_responses,
            total_files=batch_info["total_files"],
            total_size=batch_info["total_size"]
        )
        
    except FileValidationError as e:
        logger.error(f"File validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileProcessingError as e:
        logger.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in batch upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_api_stats(
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Get API statistics and system information.
    
    Args:
        pipeline_service: Pipeline processing service
        file_handler: File handling service
        
    Returns:
        API statistics and system information
    """
    try:
        # Get running assessments count
        running_assessments = len(pipeline_service.running_assessments)
        
        # Get temp directory stats
        temp_stats = file_handler.get_temp_dir_stats()
        
        # Get assessment status breakdown
        status_breakdown = {}
        for assessment_info in pipeline_service.running_assessments.values():
            status = assessment_info.get("status", "unknown")
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        return {
            "running_assessments": running_assessments,
            "status_breakdown": status_breakdown,
            "temp_directory_stats": temp_stats,
            "max_workers": pipeline_service.max_workers,
            "system_info": {
                "temp_dir": str(file_handler.temp_dir),
                "uploads_dir": str(file_handler.uploads_dir),
                "processing_dir": str(file_handler.processing_dir)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting API stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cleanup")
async def cleanup_system(
    max_age_hours: int = 24,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Clean up old files and completed assessments.
    
    Args:
        max_age_hours: Maximum age of files/assessments to keep
        pipeline_service: Pipeline processing service
        file_handler: File handling service
        
    Returns:
        Cleanup statistics
    """
    try:
        # Clean up temp files
        file_cleanup = file_handler.cleanup_temp_files(max_age_hours)
        
        # Clean up completed assessments
        assessment_cleanup = pipeline_service.cleanup_completed_assessments(max_age_hours)
        
        return {
            "file_cleanup": file_cleanup,
            "assessments_cleaned": assessment_cleanup,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")