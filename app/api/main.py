"""
Vetria Project API - Streamlined Assessment Pipeline
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

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
from dotenv import load_dotenv
import pandas as pd
import tempfile
import os
from pydantic import BaseModel
from typing import Optional, Any
import json

# Load environment variables
load_dotenv()

# Import Vetria Pipeline
from victoria_pipeline import VetriaPipeline
from victoria.utils.csv_utils import convert_raw_text_to_csv_format, convert_csv_to_pipeline_format

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

# Request models
class CSVReportRequest(BaseModel):
    csv_content: str
    person_index: Optional[int] = 0

# Utility functions for request parsing
async def parse_request_body(request: Request) -> tuple[str, int]:
    """Parse request body to extract CSV content and person index"""
    try:
        body = await request.body()
        
        # Try to parse as JSON with error handling for malformed JSON
        try:
            body_str = body.decode('utf-8')
            data = json.loads(body_str)
            csv_content = data.get('csv_content', '')
            person_index = data.get('person_index', 0)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract from raw body
            logger.warning("JSON parsing failed, trying to extract from raw body")
            body_str = body.decode('utf-8')
            # Try to find csv_content in the body string
            if 'csv_content' in body_str:
                # Extract the content after "csv_content": "
                import re
                match = re.search(r'"csv_content"\s*:\s*"(.*)"', body_str, re.DOTALL)
                if match:
                    csv_content = match.group(1).replace('\\"', '"')
                    csv_content = csv_content.encode('utf-8').decode('unicode_escape')
                
                # Extract person_index
                match2 = re.search(r'"person_index"\s*:\s*(\d+)', body_str)
                if match2:
                    person_index = int(match2.group(1))
                else:
                    person_index = 0
            else:
                raise HTTPException(status_code=400, detail="Could not parse request")
        
        logger.info(f"Processing request - csv_content length: {len(csv_content)}, person_index: {person_index}")
        return csv_content, person_index
        
    except Exception as e:
        logger.error(f"Error parsing request: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing request: {str(e)}")


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Vetria Assessment API...")
    yield
    logger.info("Shutting down Vetria Assessment API...")

# Create FastAPI application
app = FastAPI(
    title="VERTRIA Assessment API",
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
        "message": "Vetria Assessment API",
        "version": "1.0.0",
        "status": "running",
        "description": "Complete psychometric assessment pipeline with HTML report generation",
        "endpoints": {
            "generate_report": "POST /api/v1/generate-report",
            "generate_report_from_csv": "POST /api/v1/generate-report-from-csv",
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
            pipeline = VetriaPipeline()
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
    Generate a complete Vetria assessment report from uploaded CSV data
    
    This endpoint processes the uploaded CSV file through the complete Vetria pipeline:
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
            logger.info("Initializing Vetria Pipeline...")
            pipeline = VetriaPipeline()
        
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

@app.post("/api/v1/generate-report-from-csv")
async def generate_report_from_csv_data(request: Request):
    """
    Generate a complete Vetria assessment report from CSV content or raw text
    
    This endpoint processes CSV content or raw text (### formatted) and converts it 
    to the format expected by the pipeline:
    1. Parses CSV content or raw text with ### formatted questions
    2. Extracts questions as columns and answers as rows
    3. Maps responses to numeric values
    4. Converts to the expected format
    5. Runs through the complete Vetria pipeline
    6. Generates a comprehensive HTML report
    
    Args:
        request: FastAPI Request object
    
    Returns:
        HTML report file as response
    """
    global pipeline
    
    try:
        # Parse request body using utility function
        csv_content, person_index = await parse_request_body(request)
        
        # Initialize pipeline if not already done
        if pipeline is None:
            logger.info("Initializing Vetria Pipeline...")
            pipeline = VetriaPipeline()
        
        # Convert CSV content to the expected format using utility function
        processed_csv = convert_csv_to_pipeline_format(csv_content)
        
        # Save to temporary CSV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_file:
            processed_csv.to_csv(tmp_file.name, index=False)
            tmp_file_path = tmp_file.name
        
        try:
            logger.info(f"Processing CSV data for person index: {person_index}")
            
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
        logger.error(f"CSV report generation error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate report from CSV: {str(e)}"
        )

@app.post("/api/v1/generate-report-from-csv-json")
async def generate_report_from_csv_data_json(request: Request):
    """Generate assessment report and return HTML as JSON (for Zapier email)"""
    
    logger.info("Received request for CSV report generation (JSON format)")
    
    try:
        # Parse request body using utility function
        csv_content, person_index = await parse_request_body(request)
        
        global pipeline
        # Initialize pipeline if not already done
        if pipeline is None:
            logger.info("Initializing Vetria Pipeline...")
            pipeline = VetriaPipeline()
        
        # Convert CSV content to the expected format using utility function
        processed_csv = convert_csv_to_pipeline_format(csv_content)
        
        # Save to temporary CSV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_file:
            processed_csv.to_csv(tmp_file.name, index=False)
            tmp_file_path = tmp_file.name
        
        try:
            logger.info(f"Processing CSV data for person index: {person_index}")
            
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
            
            # Read the HTML content
            with open(report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            logger.info(f"Report generated successfully: {report_path}")
            
            # Return as JSON with HTML content
            return {
                "status": "success",
                "report_html": html_content,
                "filename": os.path.basename(report_path)
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"CSV report generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate report from CSV: {str(e)}"
        )



# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    try:
        body = await request.body()
        logger.error(f"Request body (first 500 chars): {body[:500]}")
    except Exception as e:
        logger.error(f"Could not read body: {e}")
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Request validation failed", "errors": exc.errors()}
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"status": "error", "message": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )

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