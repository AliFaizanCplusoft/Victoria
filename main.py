"""
Main entry point for Victoria Project Psychometric Reporting Pipeline
Enhanced with personality dashboard capabilities
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import configuration
from config import config

# Setup basic logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import core pipeline components with error handling
try:
    from src.pipeline.main_orchestrator import PsychometricPipeline
    PIPELINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Pipeline not available: {e}")
    PIPELINE_AVAILABLE = False
    PsychometricPipeline = None

# Note: The main.py now uses the same comprehensive processing workflow as the Streamlit app:
# 1. ComprehensiveDataProcessor for raw data transformation
# 2. RaschPy analysis for psychometric scoring
# 3. TraitScorer for individual trait profile generation
# 4. All outputs match the Streamlit app functionality exactly

try:
    from src.visualization.personality_dashboard import PersonalityDashboard
    PERSONALITY_DASHBOARD_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Personality dashboard not available: {e}")
    PERSONALITY_DASHBOARD_AVAILABLE = False
    PersonalityDashboard = None

try:
    from src.visualization.dashboard_integration import DashboardIntegration
    DASHBOARD_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Dashboard integration not available: {e}")
    DASHBOARD_INTEGRATION_AVAILABLE = False
    DashboardIntegration = None

try:
    from src.reports.personality_report_generator import PersonalityReportGenerator, ReportConfig
    PERSONALITY_REPORTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Personality report generator not available: {e}")
    PERSONALITY_REPORTS_AVAILABLE = False
    PersonalityReportGenerator = None
    ReportConfig = None

try:
    from src.utils.logging_config import setup_logging
    setup_logging()
except ImportError:
    # Fallback logging setup
    logging.basicConfig(level=logging.INFO)

# Import API components
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Victoria Project - Psychometric Reporting Pipeline",
    description="Enhanced psychometric assessment reporting with Streamlit-like raw data processing, RaschPy analysis, and personality dashboard",
    version="2.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global components
orchestrator = PsychometricPipeline() if PIPELINE_AVAILABLE else None
dashboard_integration = DashboardIntegration() if DASHBOARD_INTEGRATION_AVAILABLE else None
personality_dashboard = PersonalityDashboard() if PERSONALITY_DASHBOARD_AVAILABLE else None
personality_report_generator = PersonalityReportGenerator() if PERSONALITY_REPORTS_AVAILABLE else None


@app.get("/")
async def root():
    """Root endpoint with dashboard overview"""
    return {
        "message": "Victoria Project - Enhanced Psychometric Reporting Pipeline",
        "version": "2.1.0",
        "features": [
            "Raw survey data processing (32 rows, 204 columns)",
            "Streamlit-like comprehensive data transformation",
            "RaschPy psychometric analysis",
            "Individual personality reports",
            "Interactive visualizations",
            "Trait clustering and correlation analysis",
            "Archetype analysis",
            "Comprehensive dashboards",
            "PDF/HTML reports"
        ],
        "processing_workflow": [
            "1. Raw CSV input processing",
            "2. Trait mapping and data transformation",
            "3. RaschPy analysis for psychometric scoring",
            "4. Comprehensive trait profile generation",
            "5. All outputs matching Streamlit app functionality"
        ],
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "psychometric-pipeline"}


@app.post("/api/v1/process")
async def process_assessment(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Process assessment file and generate comprehensive reports"""
    try:
        # Save uploaded file
        upload_dir = Path("temp/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process the file
        background_tasks.add_task(process_file_background, str(file_path))
        
        return {
            "message": "File uploaded and processing started",
            "filename": file.filename,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/dashboard")
async def get_dashboard():
    """Get main dashboard HTML"""
    try:
        dashboard_path = Path("ml_dashboard.html")
        if dashboard_path.exists():
            return FileResponse(str(dashboard_path), media_type="text/html")
        else:
            return HTMLResponse("<h1>Dashboard not found. Please process an assessment first.</h1>")
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reports")
async def list_reports():
    """List available reports"""
    try:
        reports_dir = Path("output/reports")
        if not reports_dir.exists():
            return {"reports": []}
        
        reports = []
        for report_file in reports_dir.glob("*.html"):
            reports.append({
                "filename": report_file.name,
                "path": str(report_file),
                "size": report_file.stat().st_size,
                "created": report_file.stat().st_mtime
            })
        
        return {"reports": reports}
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reports/{report_name}")
async def get_report(report_name: str):
    """Get specific report file"""
    try:
        report_path = Path("output/reports") / report_name
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        return FileResponse(str(report_path), media_type="text/html")
        
    except Exception as e:
        logger.error(f"Error serving report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_file_background(file_path: str):
    """Background task to process assessment file - now uses Streamlit-like processing"""
    try:
        logger.info(f"Processing file: {file_path}")
        
        # Try Streamlit-like processing first
        success = process_file_command_line(file_path)
        
        if success:
            logger.info("File processed successfully using Streamlit-like processing")
            
            # Try to process with main orchestrator for additional features
            if orchestrator:
                try:
                    # Use the processed output file for orchestrator
                    processed_file = config.output_file_path
                    if os.path.exists(processed_file):
                        results = orchestrator.process_file(processed_file)
                        
                        if results and results.get('success'):
                            logger.info("Additional orchestrator processing completed")
                            # Generate personality dashboard reports
                            await generate_personality_reports(results)
                        else:
                            logger.warning("Additional orchestrator processing failed")
                    else:
                        logger.warning("Processed output file not found for orchestrator")
                except Exception as e:
                    logger.warning(f"Additional orchestrator processing failed: {e}")
            
        else:
            logger.error("File processing failed")
            
    except Exception as e:
        logger.error(f"Error in background processing: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def generate_personality_reports(orchestrator_results: Dict[str, Any]):
    """Generate enhanced personality reports from orchestrator results"""
    try:
        # Extract assessment data from orchestrator results
        assessment_data = orchestrator_results.get('data', {})
        
        if not assessment_data:
            logger.warning("No assessment data found in orchestrator results")
            return
        
        # Convert orchestrator results to personality profiles
        profiles = []
        
        # If we have multiple people in the data
        if isinstance(assessment_data, list):
            for person_data in assessment_data:
                try:
                    profile = dashboard_integration.process_assessment_data(person_data)
                    profiles.append(profile)
                except Exception as e:
                    logger.warning(f"Error processing person data: {e}")
                    continue
        else:
            # Single person assessment
            try:
                profile = dashboard_integration.process_assessment_data(assessment_data)
                profiles.append(profile)
            except Exception as e:
                logger.warning(f"Error processing assessment data: {e}")
                return
        
        # Generate reports for each profile
        for profile in profiles:
            try:
                # Generate comprehensive dashboard
                logger.info(f"Generating dashboard for {profile.name}")
                
                viz_files = personality_dashboard.generate_comprehensive_dashboard(
                    profile=profile,
                    comparison_profiles=profiles[:3] if len(profiles) > 1 else None,
                    all_profiles=profiles,
                    output_dir=f"output/personality_dashboard_{profile.person_id}"
                )
                
                # Generate HTML report
                config = ReportConfig(
                    include_comparisons=True,
                    include_archetype_analysis=True,
                    include_development_plan=True,
                    color_theme="professional",
                    format="html"
                )
                
                html_report = personality_report_generator.generate_html_report(
                    profile=profile,
                    config=config,
                    all_profiles=profiles
                )
                
                logger.info(f"Generated personality report for {profile.name}")
                
            except Exception as e:
                logger.error(f"Error generating report for {profile.person_id}: {e}")
                continue
        
        logger.info(f"Completed personality report generation for {len(profiles)} profiles")
        
    except Exception as e:
        logger.error(f"Error generating personality reports: {e}")
        import traceback
        logger.error(traceback.format_exc())


def process_file_command_line(file_path: str, output_dir: str = None):
    """Process file from command line - replicates Streamlit app functionality"""
    try:
        logger.info(f"Processing file: {file_path}")
        
        # Validate file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # Import required modules for Streamlit-like processing
        try:
            from src.data.comprehensive_processor import ComprehensiveDataProcessor
            from trait_scorer import TraitScorer
            COMPREHENSIVE_PROCESSOR_AVAILABLE = True
        except ImportError as e:
            logger.error(f"Comprehensive processor not available: {e}")
            return False
        
        # Initialize processors (same as Streamlit app)
        comprehensive_processor = ComprehensiveDataProcessor()
        trait_scorer = TraitScorer()
        
        # Set paths using configuration
        traits_file_path = config.traits_file_path
        responses_file_path = config.responses_file_path
        output_path = config.output_file_path
        
        # Process with comprehensive processor (same as Streamlit app)
        logger.info("Using comprehensive processor for raw data processing")
        result = comprehensive_processor.process_complete_pipeline(
            raw_data_path=file_path,
            traits_file_path=traits_file_path,
            output_path=output_path,
            responses_file_path=responses_file_path
        )
        
        if not result.success:
            logger.error("Comprehensive processing failed")
            if result.errors:
                for error in result.errors:
                    logger.error(f"• {error}")
            return False
        
        logger.info("✅ Data loaded and processed successfully!")
        logger.info(f"📁 Output saved to: {result.output_file_path}")
        
        # Calculate trait scores from processed data (same as Streamlit app)
        logger.info("Calculating trait scores...")
        trait_profiles = trait_scorer.calculate_trait_scores(
            processed_data_path=result.output_file_path,
            traits_file_path=traits_file_path
        )
        
        if trait_profiles:
            logger.info("✅ Trait scores calculated successfully!")
            logger.info(f"📊 Calculated trait profiles for {len(trait_profiles)} individuals")
            
            # Create scoring results DataFrame for compatibility
            scoring_results = trait_scorer.create_scoring_dataframe(trait_profiles)
            logger.info(f"📋 Created scoring DataFrame with {len(scoring_results)} records")
            
            # Display summary information
            if result.output_file_path and os.path.exists(result.output_file_path):
                import pandas as pd
                processed_df = pd.read_csv(result.output_file_path, sep='\t')
                logger.info(f"📊 Processed Data Summary:")
                logger.info(f"   • Total Records: {len(processed_df)}")
                logger.info(f"   • Unique Persons: {processed_df['Persons'].nunique()}")
                logger.info(f"   • Unique Items: {processed_df['Assessment_Items'].nunique()}")
                logger.info(f"   • Average Measure: {processed_df['Measure'].mean():.3f}")
                
                # Show trait score summary
                if not scoring_results.empty:
                    trait_cols = [col for col in scoring_results.columns 
                                 if col not in ['overall_score', 'overall_percentile', 'completion_rate']]
                    logger.info(f"📈 Trait Scores Summary:")
                    logger.info(f"   • Traits Assessed: {len(trait_cols)}")
                    logger.info(f"   • Average Overall Score: {scoring_results['overall_score'].mean():.3f}")
                    logger.info(f"   • Average Completion Rate: {scoring_results['completion_rate'].mean():.1%}")
        else:
            logger.warning("No trait profiles generated")
        
        # Show processing log
        logger.info("📋 Processing Log:")
        for log_entry in result.processing_log:
            logger.info(f"   • {log_entry}")
        
        # Try to run the original orchestrator if available (for additional features)
        if orchestrator:
            logger.info("Running additional pipeline processing...")
            try:
                orchestrator_results = orchestrator.process_file(result.output_file_path)
                if orchestrator_results and orchestrator_results.get('success'):
                    logger.info("✅ Additional pipeline processing completed")
                    
                    # Generate comprehensive personality report if available
                    if dashboard_integration:
                        assessment_data = orchestrator_results.get('data', {})
                        if assessment_data:
                            comprehensive_results = dashboard_integration.generate_comprehensive_report(
                                assessment_data=assessment_data,
                                output_dir=output_dir
                            )
                            
                            if comprehensive_results:
                                logger.info("✅ Personality dashboard reports generated")
                                logger.info(f"📁 Output directory: {comprehensive_results.get('output_directory')}")
                                logger.info(f"📄 HTML report: {comprehensive_results.get('html_report')}")
                                logger.info(f"📊 Visualizations: {len(comprehensive_results.get('visualizations', {}))}")
                else:
                    logger.warning("Additional pipeline processing failed")
            except Exception as e:
                logger.warning(f"Additional pipeline processing failed: {e}")
        
        # Check for traditional ML dashboard
        dashboard_path = Path("ml_dashboard.html")
        if dashboard_path.exists():
            logger.info(f"📊 Traditional ML dashboard available at: {dashboard_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(
        description="Victoria Project Psychometric Reporting Pipeline - Enhanced with Streamlit-like Raw Data Processing"
    )
    parser.add_argument("--file", "-f", help="Path to raw assessment data file (CSV with 32 rows, 204 columns)")
    parser.add_argument("--output", "-o", help="Output directory for reports")
    parser.add_argument("--server", "-s", action="store_true", help="Start web server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # If file is provided, process it
    if args.file:
        logger.info("Command line file processing mode")
        logger.info("🔄 Processing raw survey data through comprehensive pipeline...")
        success = process_file_command_line(args.file, args.output)
        if success:
            logger.info("✅ File processing completed successfully")
            logger.info("Generated outputs:")
            logger.info("• 📄 Processed data (tab-separated): processed_output.txt")
            logger.info("• 📊 Trait scores and profiles calculated")
            logger.info("• 📈 Traditional ML dashboard: ml_dashboard.html")
            logger.info("• 📋 Personality reports: output/reports/")
            logger.info("• 🎨 Interactive visualizations: output/personality_dashboard_*/")
            logger.info("")
            logger.info("🎯 The main.py now processes raw survey data exactly like the Streamlit app:")
            logger.info("   1. Takes raw CSV input (32 rows, 204 columns)")
            logger.info("   2. Applies trait mapping and data transformation")
            logger.info("   3. Runs RaschPy analysis for psychometric scoring")
            logger.info("   4. Generates comprehensive trait profiles")
            logger.info("   5. Creates all the same outputs as Streamlit app")
        else:
            logger.error("❌ File processing failed")
        return
    
    # If server mode is requested or no file provided
    if args.server or not args.file:
        logger.info("Starting web server mode")
        logger.info("Enhanced Psychometric Reporting Pipeline with Streamlit-like Raw Data Processing")
        logger.info("=" * 80)
        logger.info("🎯 Features:")
        logger.info("• 📊 Raw survey data processing (32 rows, 204 columns)")
        logger.info("• 🔄 Comprehensive data transformation pipeline")
        logger.info("• 📈 RaschPy psychometric analysis")
        logger.info("• 🎨 Interactive personality visualizations")
        logger.info("• 📋 Comprehensive individual reports")
        logger.info("• 🎯 Archetype analysis and matching")
        logger.info("• 💪 Strengths & weaknesses analysis")
        logger.info("• 📄 HTML and PDF report generation")
        logger.info("• 📊 Population benchmarking")
        logger.info("• 🔍 Trait clustering and correlation analysis")
        logger.info("=" * 80)
        logger.info("")
        logger.info("💡 Usage Examples:")
        logger.info("   # Process raw survey data file:")
        logger.info("   python main.py --file path/to/raw_data.csv")
        logger.info("")
        logger.info("   # Start web server:")
        logger.info("   python main.py --server")
        logger.info("=" * 80)
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info"
        )


if __name__ == "__main__":
    main()