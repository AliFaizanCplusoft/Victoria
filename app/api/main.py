"""
Victoria Project API - Streamlined Assessment Pipeline
Single endpoint for complete psychometric assessment and HTML report generation
"""

import sys
import os
import tempfile
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Victoria Pipeline
from victoria_pipeline import VictoriaPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Victoria Assessment API...")
    yield
    logger.info("Shutting down Victoria Assessment API...")

# Create FastAPI application
app = FastAPI(
    title="Victoria Assessment API",
    description="Complete psychometric assessment pipeline with HTML report generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
pipeline = None

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Victoria Assessment API",
        "version": "1.0.0",
        "status": "running",
        "description": "Complete psychometric assessment pipeline with HTML report generation",
        "endpoints": {
            "generate_report": "POST /api/v1/generate-report",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global pipeline
    try:
        if pipeline is None:
            pipeline = VictoriaPipeline()
        return {
            "status": "healthy",
            "pipeline": "ready",
            "openai_client": "ready" if pipeline.openai_client else "not_available"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/api/v1/generate-report")
async def generate_assessment_report(
    responses_file: UploadFile = File(...),
    person_index: int = 0
):
    """
    Generate a complete Victoria assessment report from uploaded CSV data
    
    This endpoint processes the uploaded CSV file through the complete Victoria pipeline:
    1. Loads and processes raw assessment data
    2. Maps responses to numeric values
    3. Calculates Rasch measures for psychometric analysis
    4. Calculates trait scores using the FixedTraitScorer
    5. Detects entrepreneurial archetype based on trait patterns
    6. Extracts and analyzes open-ended responses
    7. Generates visualizations and inspiring content
    8. Creates a comprehensive HTML report
    
    Args:
        responses_file: CSV file containing assessment responses
        person_index: Index of person to process (default: 0)
    
    Returns:
        HTML report file as response
    """
    global pipeline
    
    try:
        # Initialize pipeline if not already done
        if pipeline is None:
            logger.info("Initializing Victoria Pipeline...")
            pipeline = VictoriaPipeline()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await responses_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            logger.info(f"Processing assessment data for person index: {person_index}")
            
            # Generate the complete report using the pipeline
            report_path = pipeline.generate_report(
                csv_path=tmp_file_path,
                output_dir="output/reports",
                person_index=person_index
            )
            
            if not os.path.exists(report_path):
                raise HTTPException(
                    status_code=500, 
                    detail="Report generation failed - file not created"
                )
            
            logger.info(f"Report generated successfully: {report_path}")
            
            # Return the HTML file
            return FileResponse(
                path=report_path,
                media_type="text/html",
                filename=os.path.basename(report_path),
                headers={
                    "Content-Disposition": f"attachment; filename={os.path.basename(report_path)}"
                }
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate report: {str(e)}"
        )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"status": "error", "message": "Endpoint not found"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {"status": "error", "message": "Internal server error"}

def main():
    """Run the API server"""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()