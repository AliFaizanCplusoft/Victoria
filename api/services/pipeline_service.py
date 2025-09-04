"""
Pipeline service for integrating with the existing psychometric pipeline
"""

import uuid
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import sys

# Add the project root and src directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.pipeline.main_orchestrator import PsychometricPipeline, PipelineConfig
except ImportError:
    # Fallback import path
    from pipeline.main_orchestrator import PsychometricPipeline, PipelineConfig
from ..models.response_models import (
    AssessmentResult, BatchAssessmentResult, ProcessingStatus, 
    ProcessingStage, AssessmentMetrics, ArchetypeInfo, OutputFiles
)
from ..utils.exceptions import PipelineProcessingError, InsufficientDataError


class PipelineService:
    """Service for running psychometric pipeline operations."""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize pipeline service.
        
        Args:
            max_workers: Maximum number of concurrent pipeline executions
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger(__name__)
        
        # Track running assessments
        self.running_assessments: Dict[str, Dict[str, Any]] = {}
        
        # Default pipeline configuration
        self.default_config = PipelineConfig(
            use_rasch_scoring=True,
            min_completion_rate=0.8,
            validation_enabled=True,
            n_clusters=5,
            optimize_clusters=True,
            generate_visualizations=True,
            generate_pdf=True,
            include_narratives=True,
            output_directory="output",
            save_intermediate_results=True
        )
    
    async def process_single_assessment(
        self, 
        file_path: str, 
        assessment_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AssessmentResult:
        """
        Process a single assessment file.
        
        Args:
            file_path: Path to the assessment file
            assessment_id: Unique assessment identifier
            config: Optional pipeline configuration
            
        Returns:
            Assessment result
            
        Raises:
            PipelineProcessingError: If processing fails
        """
        try:
            self.logger.info(f"Starting single assessment processing: {assessment_id}")
            
            # Create pipeline configuration
            pipeline_config = self._create_pipeline_config(config)
            
            # Initialize assessment tracking
            self.running_assessments[assessment_id] = {
                "status": ProcessingStatus.PROCESSING,
                "started_at": datetime.now(),
                "current_stage": "initialization",
                "progress": 0.0
            }
            
            # Run pipeline in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_pipeline,
                file_path,
                assessment_id,
                pipeline_config
            )
            
            # Convert to API response format
            assessment_result = self._convert_to_assessment_result(result, assessment_id)
            
            # Update tracking
            self.running_assessments[assessment_id]["status"] = ProcessingStatus.COMPLETED
            self.running_assessments[assessment_id]["completed_at"] = datetime.now()
            
            self.logger.info(f"Single assessment completed: {assessment_id}")
            return assessment_result
            
        except Exception as e:
            self.logger.error(f"Error processing single assessment {assessment_id}: {str(e)}")
            
            # Update tracking
            if assessment_id in self.running_assessments:
                self.running_assessments[assessment_id]["status"] = ProcessingStatus.FAILED
                self.running_assessments[assessment_id]["error"] = str(e)
            
            raise PipelineProcessingError(f"Failed to process assessment: {str(e)}")
    
    async def process_batch_assessment(
        self, 
        file_paths: List[str], 
        batch_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BatchAssessmentResult:
        """
        Process multiple assessment files in batch.
        
        Args:
            file_paths: List of file paths to process
            batch_id: Unique batch identifier
            config: Optional pipeline configuration
            
        Returns:
            Batch assessment result
            
        Raises:
            PipelineProcessingError: If processing fails
        """
        try:
            self.logger.info(f"Starting batch assessment processing: {batch_id}")
            
            # Create pipeline configuration
            pipeline_config = self._create_pipeline_config(config)
            
            # Initialize batch tracking
            self.running_assessments[batch_id] = {
                "status": ProcessingStatus.PROCESSING,
                "started_at": datetime.now(),
                "current_stage": "batch_initialization",
                "progress": 0.0,
                "total_files": len(file_paths)
            }
            
            # Run batch pipeline in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_batch_pipeline,
                file_paths,
                batch_id,
                pipeline_config
            )
            
            # Convert to API response format
            batch_result = self._convert_to_batch_result(result, batch_id)
            
            # Update tracking
            self.running_assessments[batch_id]["status"] = ProcessingStatus.COMPLETED
            self.running_assessments[batch_id]["completed_at"] = datetime.now()
            
            self.logger.info(f"Batch assessment completed: {batch_id}")
            return batch_result
            
        except Exception as e:
            self.logger.error(f"Error processing batch assessment {batch_id}: {str(e)}")
            
            # Update tracking
            if batch_id in self.running_assessments:
                self.running_assessments[batch_id]["status"] = ProcessingStatus.FAILED
                self.running_assessments[batch_id]["error"] = str(e)
            
            raise PipelineProcessingError(f"Failed to process batch: {str(e)}")
    
    def _run_pipeline(self, file_path: str, assessment_id: str, config: PipelineConfig) -> Dict[str, Any]:
        """
        Run the psychometric pipeline (blocking operation).
        
        Args:
            file_path: Path to assessment file
            assessment_id: Assessment identifier
            config: Pipeline configuration
            
        Returns:
            Pipeline result dictionary
        """
        try:
            self.logger.info(f"Starting pipeline for file: {file_path}")
            self.logger.info(f"Assessment ID: {assessment_id}")
            self.logger.info(f"Config: {config}")
            
            # Create pipeline instance
            pipeline = PsychometricPipeline(config)
            self.logger.info("Pipeline instance created successfully")
            
            # Update tracking
            self.running_assessments[assessment_id]["current_stage"] = "data_ingestion"
            self.running_assessments[assessment_id]["progress"] = 20.0
            
            # Process file
            result = pipeline.process_file(file_path)
            
            # Update tracking throughout processing
            self.running_assessments[assessment_id]["current_stage"] = "scoring"
            self.running_assessments[assessment_id]["progress"] = 40.0
            
            # Check if processing was successful
            if not result.get("success", False):
                raise PipelineProcessingError(
                    f"Pipeline processing failed: {'; '.join(result.get('errors', []))}"
                )
            
            # Update tracking
            self.running_assessments[assessment_id]["current_stage"] = "clustering"
            self.running_assessments[assessment_id]["progress"] = 60.0
            
            # Generate summary report
            summary_path = pipeline.generate_summary_report(result)
            result["summary_report"] = summary_path
            
            # Update tracking
            self.running_assessments[assessment_id]["current_stage"] = "report_generation"
            self.running_assessments[assessment_id]["progress"] = 80.0
            
            # Cleanup
            pipeline.cleanup()
            
            # Update tracking
            self.running_assessments[assessment_id]["progress"] = 100.0
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline execution error: {str(e)}")
            raise
    
    def _run_batch_pipeline(self, file_paths: List[str], batch_id: str, config: PipelineConfig) -> Dict[str, Any]:
        """
        Run the batch psychometric pipeline (blocking operation).
        
        Args:
            file_paths: List of file paths
            batch_id: Batch identifier
            config: Pipeline configuration
            
        Returns:
            Batch pipeline result dictionary
        """
        try:
            # Create pipeline instance
            pipeline = PsychometricPipeline(config)
            
            # Update tracking
            self.running_assessments[batch_id]["current_stage"] = "batch_processing"
            self.running_assessments[batch_id]["progress"] = 10.0
            
            # Process files in batch
            result = pipeline.batch_process_files(file_paths)
            
            # Update tracking
            self.running_assessments[batch_id]["progress"] = 90.0
            
            # Cleanup
            pipeline.cleanup()
            
            # Update tracking
            self.running_assessments[batch_id]["progress"] = 100.0
            
            return result
            
        except Exception as e:
            self.logger.error(f"Batch pipeline execution error: {str(e)}")
            raise
    
    def _create_pipeline_config(self, config: Optional[Dict[str, Any]]) -> PipelineConfig:
        """
        Create pipeline configuration from API request.
        
        Args:
            config: Configuration dictionary from API request
            
        Returns:
            Pipeline configuration object
        """
        if not config:
            return self.default_config
        
        # Merge with default config
        config_dict = {
            "use_rasch_scoring": config.get("use_rasch_scoring", self.default_config.use_rasch_scoring),
            "min_completion_rate": config.get("min_completion_rate", self.default_config.min_completion_rate),
            "validation_enabled": config.get("validation_enabled", self.default_config.validation_enabled),
            "n_clusters": config.get("n_clusters", self.default_config.n_clusters),
            "optimize_clusters": config.get("optimize_clusters", self.default_config.optimize_clusters),
            "generate_visualizations": config.get("generate_visualizations", self.default_config.generate_visualizations),
            "generate_pdf": config.get("generate_pdf", self.default_config.generate_pdf),
            "include_narratives": config.get("include_narratives", self.default_config.include_narratives),
            "output_directory": config.get("output_directory", self.default_config.output_directory),
            "save_intermediate_results": config.get("save_intermediate_results", self.default_config.save_intermediate_results),
            "chart_theme": config.get("chart_theme", self.default_config.chart_theme),
            "template_name": config.get("template_name", self.default_config.template_name)
        }
        
        return PipelineConfig(**config_dict)
    
    def _convert_to_assessment_result(self, pipeline_result: Dict[str, Any], assessment_id: str) -> AssessmentResult:
        """
        Convert pipeline result to API assessment result.
        
        Args:
            pipeline_result: Result from pipeline processing
            assessment_id: Assessment identifier
            
        Returns:
            Assessment result object
        """
        # Extract stages information
        stages = []
        for stage_name in pipeline_result.get("stages_completed", []):
            stages.append(ProcessingStage(
                stage_name=stage_name,
                status=ProcessingStatus.COMPLETED,
                started_at=datetime.now(),  # Placeholder
                completed_at=datetime.now()  # Placeholder
            ))
        
        # Extract metrics
        metrics = None
        if "outputs" in pipeline_result:
            outputs = pipeline_result["outputs"]
            metrics = AssessmentMetrics(
                total_participants=outputs.get("scoring", {}).get("persons_scored", 0),
                completion_rate=0.8,  # Placeholder
                processing_time=pipeline_result.get("processing_time", 0),
                records_processed=outputs.get("ingestion", {}).get("records_processed", 0),
                clusters_created=outputs.get("clustering", {}).get("clusters_created", 0)
            )
        
        # Extract archetypes
        archetypes = []
        if "outputs" in pipeline_result and "clustering" in pipeline_result["outputs"]:
            archetype_assignments = pipeline_result["outputs"]["clustering"].get("archetype_assignments", {})
            total_participants = sum(archetype_assignments.values())
            
            for archetype_name, count in archetype_assignments.items():
                percentage = (count / total_participants * 100) if total_participants > 0 else 0
                archetypes.append(ArchetypeInfo(
                    archetype_name=archetype_name,
                    participant_count=count,
                    percentage=percentage
                ))
        
        # Extract output files
        output_files = OutputFiles()
        if "outputs" in pipeline_result:
            if "reports" in pipeline_result["outputs"]:
                reports = pipeline_result["outputs"]["reports"]
                output_files.html_reports = reports.get("html", [])
                output_files.pdf_reports = reports.get("pdf", [])
            
            if "visualizations" in pipeline_result["outputs"]:
                viz = pipeline_result["outputs"]["visualizations"]
                output_files.dashboard = viz.get("dashboard")
                output_files.archetype_map = viz.get("archetype_map")
                output_files.visualizations = list(viz.values())
        
        return AssessmentResult(
            assessment_id=assessment_id,
            status=ProcessingStatus.COMPLETED if pipeline_result.get("success") else ProcessingStatus.FAILED,
            file_path=pipeline_result.get("file_path", ""),
            created_at=datetime.now(),
            completed_at=datetime.now(),
            stages=stages,
            metrics=metrics,
            archetypes=archetypes,
            output_files=output_files,
            errors=pipeline_result.get("errors", []),
            warnings=pipeline_result.get("warnings", [])
        )
    
    def _convert_to_batch_result(self, pipeline_result: Dict[str, Any], batch_id: str) -> BatchAssessmentResult:
        """
        Convert batch pipeline result to API batch result.
        
        Args:
            pipeline_result: Result from batch pipeline processing
            batch_id: Batch identifier
            
        Returns:
            Batch assessment result object
        """
        # Convert individual file results
        file_results = []
        for file_result in pipeline_result.get("file_results", []):
            # Generate assessment ID for each file
            file_assessment_id = f"{batch_id}_{uuid.uuid4().hex[:8]}"
            assessment_result = self._convert_to_assessment_result(file_result, file_assessment_id)
            file_results.append(assessment_result)
        
        # Calculate batch metrics
        batch_metrics = None
        if "batch_summary" in pipeline_result:
            summary = pipeline_result["batch_summary"]
            batch_metrics = AssessmentMetrics(
                total_participants=summary.get("total_participants", 0),
                completion_rate=0.8,  # Placeholder
                processing_time=summary.get("average_processing_time", 0),
                records_processed=summary.get("total_participants", 0),
                clusters_created=summary.get("total_clusters", 0)
            )
        
        return BatchAssessmentResult(
            batch_id=batch_id,
            status=ProcessingStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            total_files=pipeline_result.get("total_files", 0),
            successful_files=pipeline_result.get("successful", 0),
            failed_files=pipeline_result.get("failed", 0),
            file_results=file_results,
            batch_metrics=batch_metrics
        )
    
    def get_assessment_status(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of an assessment.
        
        Args:
            assessment_id: Assessment identifier
            
        Returns:
            Status information or None if not found
        """
        return self.running_assessments.get(assessment_id)
    
    def cancel_assessment(self, assessment_id: str) -> bool:
        """
        Cancel a running assessment.
        
        Args:
            assessment_id: Assessment identifier
            
        Returns:
            True if cancelled successfully
        """
        if assessment_id in self.running_assessments:
            self.running_assessments[assessment_id]["status"] = ProcessingStatus.CANCELLED
            # Note: Actual cancellation of running threads is complex
            # This just marks the status as cancelled
            return True
        return False
    
    def cleanup_completed_assessments(self, max_age_hours: int = 24) -> int:
        """
        Clean up completed assessment tracking data.
        
        Args:
            max_age_hours: Maximum age of completed assessments to keep
            
        Returns:
            Number of assessments cleaned up
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        completed_assessments = []
        for assessment_id, info in self.running_assessments.items():
            if (info.get("status") in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED] and
                info.get("completed_at", datetime.now()) < cutoff_time):
                completed_assessments.append(assessment_id)
        
        for assessment_id in completed_assessments:
            del self.running_assessments[assessment_id]
            cleaned_count += 1
        
        return cleaned_count