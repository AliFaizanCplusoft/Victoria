"""
FastAPI application for Victoria Project - Psychometric Assessment API
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add the project root and src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from .routes.assessment import router as assessment_router
from .routes.reports import router as reports_router
from .utils.exceptions import PsychometricAPIException

# Configure logging - Docker-compatible
handlers = [logging.StreamHandler(sys.stdout)]
if not os.getenv('DOCKER_ENV') and os.path.exists('logs'):
    try:
        handlers.append(logging.FileHandler('logs/api.log'))
    except PermissionError:
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Victoria Project API...")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    yield
    
    logger.info("Shutting down Victoria Project API...")

# Create FastAPI application
app = FastAPI(
    title="Victoria Project - Psychometric Assessment API",
    description="API for processing psychometric assessment data with clustering and reporting capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler
@app.exception_handler(PsychometricAPIException)
async def psychometric_exception_handler(request: Request, exc: PsychometricAPIException):
    """Handle custom API exceptions."""
    logger.error(f"API Error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "type": exc.error_type}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "type": "server_error"}
    )

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Victoria Project API",
        "version": "1.0.0"
    }

# Include routers
app.include_router(assessment_router, prefix="/api/v1", tags=["Assessment"])
app.include_router(reports_router, prefix="/api/v1", tags=["Reports"])

# Mount static files for serving generated reports and visualizations
if os.path.exists("output"):
    app.mount("/static", StaticFiles(directory="output"), name="static")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Victoria Project - Psychometric Assessment API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/api/v1/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )