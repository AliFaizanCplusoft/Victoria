"""
Main Pipeline Orchestrator for Victoria Project
Coordinates the entire psychometric assessment pipeline
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

# Set up logging
import os

# Configure logging - Docker-compatible (console-only if in Docker environment)
handlers = [logging.StreamHandler(sys.stdout)]
if not os.getenv('DOCKER_ENV') and os.path.exists('logs'):
    try:
        handlers.append(logging.FileHandler('logs/pipeline.log'))
    except PermissionError:
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

@dataclass
class PipelineConfig:
    """Configuration for the psychometric assessment pipeline."""
    # Data processing settings
    use_rasch_scoring: bool = True
    min_completion_rate: float = 0.8
    validation_enabled: bool = True
    
    # Clustering settings
    n_clusters: int = 5
    optimize_clusters: bool = True
    
    # Visualization settings
    generate_visualizations: bool = True
    chart_theme: str = "plotly_white"
    
    # Report settings
    generate_pdf: bool = True
    include_narratives: bool = True
    template_name: str = "comprehensive_report_template.html"
    
    # Output settings
    output_directory: str = "output"
    save_intermediate_results: bool = True

class PsychometricPipeline:
    """
    Main orchestrator for the complete psychometric assessment pipeline.
    
    Coordinates:
    1. Data ingestion and validation
    2. Psychometric scoring
    3. Clustering and archetype assignment
    4. Visualization generation
    5. Report creation and PDF generation
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline orchestrator.
        
        Args:
            config: Pipeline configuration object
        """
        self.config = config or PipelineConfig()
        self.logger = logging.getLogger(__name__)
        
        # Create output directory
        self.output_dir = Path(self.config.output_directory)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self._initialize_components()
        
        self.logger.info("PsychometricPipeline initialized")
    
    def _initialize_components(self):
        """Initialize all pipeline components."""
        try:
            # Import components with error handling - add src directory to path
            import sys
            import os
            
            # Add src directory to Python path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(current_dir)
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            
            try:
                from data.item_mapper import ItemMapper
                from data.data_ingestion import PsychometricDataProcessor
                from data.data_validator import DataValidator
                from scoring.scoring_engine import PsychometricScoringEngine
                from clustering.clustering_engine import PsychometricClusteringEngine
                from visualization.visualization_engine import PsychometricVisualizationEngine
                from reports.report_generator import generate_batch_reports
            except ImportError as e:
                # If that fails, try relative imports
                self.logger.warning(f"Absolute imports failed: {e}, trying relative imports")
                from ..data.item_mapper import ItemMapper
                from ..data.data_ingestion import PsychometricDataProcessor
                from ..data.data_validator import DataValidator
                from ..scoring.scoring_engine import PsychometricScoringEngine
                from ..clustering.clustering_engine import PsychometricClusteringEngine
                from ..visualization.visualization_engine import PsychometricVisualizationEngine
                from ..reports.report_generator import generate_batch_reports
            
            # Try to import PDF generator with fallback
            try:
                try:
                    from reports.pdf_generator import PsychometricPDFGenerator
                except ImportError:
                    from ..reports.pdf_generator import PsychometricPDFGenerator
                self.pdf_generator = PsychometricPDFGenerator()
                self.pdf_available = True
            except ImportError as e:
                self.logger.warning(f"PDF generator not available: {e}")
                self.pdf_generator = None
                self.pdf_available = False
            
            # Initialize core components
            self.item_mapper = ItemMapper()
            self.data_validator = DataValidator(self.item_mapper)
            self.data_processor = PsychometricDataProcessor(
                self.item_mapper, self.data_validator
            )
            self.scoring_engine = PsychometricScoringEngine(
                self.item_mapper,
                use_rasch_scoring=self.config.use_rasch_scoring
            )
            self.clustering_engine = PsychometricClusteringEngine(
                n_clusters=self.config.n_clusters
            )
            self.visualization_engine = PsychometricVisualizationEngine(
                theme=self.config.chart_theme
            )
            
            self.logger.info("All pipeline components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def process_file(self, file_path: str, 
                    file_type: str = "auto") -> Dict[str, Any]:
        """
        Process a single assessment file through the complete pipeline.
        
        Args:
            file_path: Path to the assessment data file
            file_type: Type of file ("typeform", "csv", or "auto")
            
        Returns:
            Dictionary with pipeline results and generated files
        """
        pipeline_start = datetime.now()
        self.logger.info(f"Starting pipeline processing for: {file_path}")
        
        results = {
            "success": False,
            "file_path": file_path,
            "processing_time": None,
            "stages_completed": [],
            "errors": [],
            "warnings": [],
            "outputs": {}
        }
        
        try:
            # Stage 1: Data Ingestion
            results["stages_completed"].append("data_ingestion_start")
            ingestion_result = self._stage_data_ingestion(file_path, file_type)
            
            if not ingestion_result.success:
                results["errors"].extend(ingestion_result.errors)
                return results
            
            results["stages_completed"].append("data_ingestion_complete")
            results["outputs"]["ingestion"] = {
                "records_processed": len(ingestion_result.data),
                "validation_summary": ingestion_result.validation_summary
            }
            
            # Stage 2: Psychometric Scoring
            results["stages_completed"].append("scoring_start")
            scoring_result = self._stage_scoring(ingestion_result.data)
            
            if not scoring_result.success:
                results["errors"].extend(scoring_result.errors)
                return results
            
            results["stages_completed"].append("scoring_complete")
            results["outputs"]["scoring"] = {
                "persons_scored": len(scoring_result.person_scores),
                "group_statistics": scoring_result.group_statistics,
                "construct_reliabilities": scoring_result.construct_reliabilities
            }
            
            # Stage 3: Clustering and Archetype Assignment
            results["stages_completed"].append("clustering_start")
            cluster_results = self._stage_clustering(scoring_result.person_scores)
            
            results["stages_completed"].append("clustering_complete")
            results["outputs"]["clustering"] = {
                "clusters_created": len(cluster_results),
                "archetype_assignments": {
                    cluster.archetype_name: cluster.size 
                    for cluster in cluster_results
                }
            }
            
            # Stage 4: Visualization Generation
            if self.config.generate_visualizations:
                results["stages_completed"].append("visualization_start")
                visualization_files = self._stage_visualization(
                    scoring_result.person_scores, cluster_results
                )
                results["stages_completed"].append("visualization_complete")
                results["outputs"]["visualizations"] = visualization_files
            
            # Stage 5: Report Generation
            results["stages_completed"].append("report_generation_start")
            report_files = self._stage_report_generation(
                scoring_result.person_scores, cluster_results
            )
            results["stages_completed"].append("report_generation_complete")
            results["outputs"]["reports"] = report_files
            
            # Success!
            results["success"] = True
            processing_time = datetime.now() - pipeline_start
            results["processing_time"] = processing_time.total_seconds()
            
            self.logger.info(f"Pipeline completed successfully in {processing_time.total_seconds():.2f} seconds")
            
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
        
        return results
    
    def _stage_data_ingestion(self, file_path: str, file_type: str):
        """Stage 1: Data ingestion and validation."""
        self.logger.info("Stage 1: Data ingestion and validation")
        
        # Determine processing method
        if file_type == "typeform" or "typeform" in file_path.lower():
            return self.data_processor.process_typeform_export(file_path)
        else:
            return self.data_processor.process_file(file_path)
    
    def _stage_scoring(self, data):
        """Stage 2: Psychometric scoring."""
        self.logger.info("Stage 2: Psychometric scoring")
        
        scoring_method = "rasch" if self.config.use_rasch_scoring else "standardized"
        return self.scoring_engine.score_assessment_data(
            data, 
            scoring_method=scoring_method,
            calculate_percentiles=True
        )
    
    def _stage_clustering(self, person_scores):
        """Stage 3: Clustering and archetype assignment."""
        self.logger.info("Stage 3: Clustering and archetype assignment")
        
        # Optimize cluster number if requested
        if self.config.optimize_clusters and len(person_scores) >= 10:
            optimal_clusters = self.clustering_engine.optimize_clusters(person_scores)
            self.clustering_engine.n_clusters = optimal_clusters
            self.logger.info(f"Optimal number of clusters: {optimal_clusters}")
        
        return self.clustering_engine.cluster_persons(person_scores)
    
    def _stage_visualization(self, person_scores, cluster_results):
        """Stage 4: Visualization generation."""
        self.logger.info("Stage 4: Visualization generation")
        
        visualization_files = {}
        
        try:
            # Create dashboard
            dashboard_path = self.output_dir / "dashboard.html"
            if self.visualization_engine.create_comprehensive_dashboard(
                person_scores, str(dashboard_path)
            ):
                visualization_files["dashboard"] = str(dashboard_path)
            
            # Create archetype map
            if cluster_results:
                archetype_path = self.output_dir / "archetype_map.html"
                if self.visualization_engine.create_archetype_map(
                    cluster_results, str(archetype_path)
                ):
                    visualization_files["archetype_map"] = str(archetype_path)
            
            # Create individual profiles for first few participants
            profiles_dir = self.output_dir / "profiles"
            profiles_dir.mkdir(exist_ok=True)
            
            for i, person in enumerate(person_scores[:5]):  # Limit to first 5
                profile_path = profiles_dir / f"profile_{person.person_id}.html"
                if self.visualization_engine.create_person_profile(
                    person, str(profile_path)
                ):
                    visualization_files[f"profile_{person.person_id}"] = str(profile_path)
            
        except Exception as e:
            self.logger.warning(f"Some visualizations failed: {e}")
        
        return visualization_files
    
    def _stage_report_generation(self, person_scores, cluster_results):
        """Stage 5: Report generation."""
        self.logger.info("Stage 5: Report generation")
        
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Import report generation with fallback
        try:
            from reports.report_generator import generate_batch_reports
        except ImportError:
            try:
                from ..reports.report_generator import generate_batch_reports
            except ImportError:
                self.logger.warning("Report generator not available")
                return []
        
        # Generate reports - adjust format based on PDF availability
        if self.pdf_available and self.config.generate_pdf:
            format_type = "both"
        else:
            format_type = "html"
            if self.config.generate_pdf:
                self.logger.warning("PDF generation requested but not available - generating HTML only")
        
        generated_files = generate_batch_reports(
            person_scores=person_scores,
            cluster_results=cluster_results,
            output_directory=str(reports_dir),
            format=format_type
        )
        
        return generated_files
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a pipeline summary report.
        
        Args:
            results: Pipeline results dictionary
            
        Returns:
            Path to summary report file
        """
        summary_path = self.output_dir / "pipeline_summary.txt"
        
        with open(summary_path, 'w') as f:
            f.write("VICTORIA PROJECT - PIPELINE EXECUTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Input File: {results.get('file_path', 'N/A')}\n")
            f.write(f"Success: {'✓' if results.get('success') else '✗'}\n")
            f.write(f"Processing Time: {results.get('processing_time', 0):.2f} seconds\n\n")
            
            # PDF availability status
            f.write(f"PDF Generation Available: {'✓' if self.pdf_available else '✗'}\n\n")
            
            # Stages completed
            f.write("STAGES COMPLETED:\n")
            for stage in results.get('stages_completed', []):
                f.write(f"  ✓ {stage}\n")
            f.write("\n")
            
            # Outputs
            outputs = results.get('outputs', {})
            if outputs:
                f.write("OUTPUTS GENERATED:\n")
                
                if 'ingestion' in outputs:
                    f.write(f"  📊 Records Processed: {outputs['ingestion']['records_processed']}\n")
                
                if 'scoring' in outputs:
                    f.write(f"  🎯 Persons Scored: {outputs['scoring']['persons_scored']}\n")
                
                if 'clustering' in outputs:
                    f.write(f"  👥 Clusters Created: {outputs['clustering']['clusters_created']}\n")
                    f.write("  📋 Archetype Distribution:\n")
                    for archetype, count in outputs['clustering']['archetype_assignments'].items():
                        f.write(f"    - {archetype}: {count} participants\n")
                
                if 'reports' in outputs:
                    reports = outputs['reports']
                    f.write(f"  📄 HTML Reports: {len(reports.get('html', []))}\n")
                    f.write(f"  📑 PDF Reports: {len(reports.get('pdf', []))}\n")
                
                f.write("\n")
            
            # Errors and warnings
            if results.get('errors'):
                f.write("ERRORS:\n")
                for error in results['errors']:
                    f.write(f"  ❌ {error}\n")
                f.write("\n")
            
            if results.get('warnings'):
                f.write("WARNINGS:\n")
                for warning in results['warnings']:
                    f.write(f"  ⚠️ {warning}\n")
                f.write("\n")
            
            f.write("END OF REPORT\n")
        
        return str(summary_path)
    
    def batch_process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Process multiple files in batch.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary with batch processing results
        """
        self.logger.info(f"Starting batch processing of {len(file_paths)} files")
        
        batch_results = {
            "total_files": len(file_paths),
            "successful": 0,
            "failed": 0,
            "file_results": [],
            "batch_summary": {}
        }
        
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                batch_results["file_results"].append(result)
                
                if result["success"]:
                    batch_results["successful"] += 1
                else:
                    batch_results["failed"] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                batch_results["failed"] += 1
                batch_results["file_results"].append({
                    "success": False,
                    "file_path": file_path,
                    "errors": [str(e)]
                })
        
        # Generate batch summary
        batch_results["batch_summary"] = self._generate_batch_summary(batch_results)
        
        self.logger.info(f"Batch processing complete: {batch_results['successful']} successful, {batch_results['failed']} failed")
        
        return batch_results
    
    def _generate_batch_summary(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for batch processing."""
        summary = {
            "total_participants": 0,
            "total_clusters": 0,
            "archetype_distribution": {},
            "average_processing_time": 0
        }
        
        processing_times = []
        
        for result in batch_results["file_results"]:
            if result["success"]:
                if "outputs" in result and "scoring" in result["outputs"]:
                    summary["total_participants"] += result["outputs"]["scoring"]["persons_scored"]
                
                if result.get("processing_time"):
                    processing_times.append(result["processing_time"])
        
        if processing_times:
            summary["average_processing_time"] = sum(processing_times) / len(processing_times)
        
        return summary
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            if self.pdf_generator:
                self.pdf_generator.cleanup_temp_files()
            self.logger.info("Pipeline cleanup completed")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")

# Convenience function for simple pipeline execution
def run_psychometric_pipeline(file_path: str, 
                             config: Optional[PipelineConfig] = None) -> Dict[str, Any]:
    """
    Run the complete psychometric pipeline on a single file.
    
    Args:
        file_path: Path to assessment data file
        config: Pipeline configuration
        
    Returns:
        Pipeline results dictionary
    """
    pipeline = PsychometricPipeline(config)
    try:
        results = pipeline.process_file(file_path)
        summary_path = pipeline.generate_summary_report(results)
        results["summary_report"] = summary_path
        return results
    finally:
        pipeline.cleanup()