"""
Report and visualization endpoints for the psychometric API
"""

import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..models.request_models import ReportRequest, VisualizationRequest
from ..models.response_models import ReportResponse, VisualizationResponse
from ..utils.exceptions import (
    AssessmentNotFoundError, ReportNotFoundError, FileProcessingError
)
from ..utils.validators import validate_assessment_id, validate_file_path

# Initialize router
router = APIRouter()

# Logger
logger = logging.getLogger(__name__)

# Output directory for reports and visualizations
OUTPUT_DIR = Path("output")
REPORTS_DIR = OUTPUT_DIR / "reports"
VISUALIZATIONS_DIR = OUTPUT_DIR


@router.get("/reports/{assessment_id}", response_model=ReportResponse)
async def get_report(
    assessment_id: str,
    format: str = Query("html", description="Report format (html or pdf)"),
    download: bool = Query(False, description="Download file instead of returning metadata")
):
    """
    Get a generated report for an assessment.
    
    Args:
        assessment_id: Unique assessment identifier
        format: Report format (html or pdf)
        download: Whether to download the file
        
    Returns:
        Report metadata or file download
        
    Raises:
        HTTPException: If report not found or invalid parameters
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        if format not in ["html", "pdf"]:
            raise HTTPException(status_code=400, detail="Format must be 'html' or 'pdf'")
        
        # Find report file
        report_pattern = f"report_{assessment_id}.{format}"
        report_path = None
        
        # Search in reports directory
        if REPORTS_DIR.exists():
            for file_path in REPORTS_DIR.glob(f"*{assessment_id}*.{format}"):
                report_path = file_path
                break
        
        if not report_path or not report_path.exists():
            logger.warning(f"Report not found: {assessment_id}, format: {format}")
            raise ReportNotFoundError(f"{assessment_id}_{format}")
        
        # Return file download
        if download:
            return FileResponse(
                path=str(report_path),
                filename=f"psychometric_report_{assessment_id}.{format}",
                media_type="application/octet-stream"
            )
        
        # Return metadata
        file_size = report_path.stat().st_size
        return ReportResponse(
            report_id=f"{assessment_id}_{format}",
            assessment_id=assessment_id,
            format=format,
            file_path=str(report_path),
            file_size=file_size,
            download_url=f"/api/v1/reports/{assessment_id}?format={format}&download=true"
        )
        
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail=f"Report not found for assessment {assessment_id}")
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reports/{assessment_id}/download")
async def download_report(
    assessment_id: str,
    format: str = Query("html", description="Report format (html or pdf)")
):
    """
    Download a generated report file.
    
    Args:
        assessment_id: Unique assessment identifier
        format: Report format (html or pdf)
        
    Returns:
        File download response
        
    Raises:
        HTTPException: If report not found
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        if format not in ["html", "pdf"]:
            raise HTTPException(status_code=400, detail="Format must be 'html' or 'pdf'")
        
        # Find report file
        report_path = None
        
        # Search in reports directory
        if REPORTS_DIR.exists():
            for file_path in REPORTS_DIR.glob(f"*{assessment_id}*.{format}"):
                report_path = file_path
                break
        
        if not report_path or not report_path.exists():
            raise ReportNotFoundError(f"{assessment_id}_{format}")
        
        # Determine media type
        media_type = "text/html" if format == "html" else "application/pdf"
        
        return FileResponse(
            path=str(report_path),
            filename=f"psychometric_report_{assessment_id}.{format}",
            media_type=media_type
        )
        
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail=f"Report not found for assessment {assessment_id}")
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reports/{assessment_id}/view")
async def view_report(
    assessment_id: str,
    format: str = Query("html", description="Report format (html only for viewing)")
):
    """
    View a generated HTML report in the browser.
    
    Args:
        assessment_id: Unique assessment identifier
        format: Report format (must be html for viewing)
        
    Returns:
        HTML content response
        
    Raises:
        HTTPException: If report not found or invalid format
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        if format != "html":
            raise HTTPException(status_code=400, detail="Only HTML reports can be viewed in browser")
        
        # Find HTML report file
        report_path = None
        
        # Search in reports directory
        if REPORTS_DIR.exists():
            for file_path in REPORTS_DIR.glob(f"*{assessment_id}*.html"):
                report_path = file_path
                break
        
        if not report_path or not report_path.exists():
            raise ReportNotFoundError(f"{assessment_id}_html")
        
        # Read and return HTML content
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail=f"HTML report not found for assessment {assessment_id}")
    except Exception as e:
        logger.error(f"Error viewing report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/visualizations/{assessment_id}", response_model=VisualizationResponse)
async def get_visualization(
    assessment_id: str,
    viz_type: str = Query("dashboard", description="Visualization type"),
    download: bool = Query(False, description="Download file instead of returning metadata")
):
    """
    Get a generated visualization for an assessment.
    
    Args:
        assessment_id: Unique assessment identifier
        viz_type: Type of visualization (dashboard, archetype_map, etc.)
        download: Whether to download the file
        
    Returns:
        Visualization metadata or file download
        
    Raises:
        HTTPException: If visualization not found
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        allowed_types = ["dashboard", "archetype_map", "individual_profile", "cluster_analysis"]
        if viz_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Visualization type must be one of: {allowed_types}"
            )
        
        # Find visualization file
        viz_path = None
        
        # Search for visualization files
        if viz_type == "dashboard":
            viz_path = OUTPUT_DIR / "dashboard.html"
        elif viz_type == "archetype_map":
            viz_path = OUTPUT_DIR / "archetype_map.html"
        else:
            # Search in profiles directory
            profiles_dir = OUTPUT_DIR / "profiles"
            if profiles_dir.exists():
                for file_path in profiles_dir.glob(f"*{assessment_id}*.html"):
                    viz_path = file_path
                    break
        
        if not viz_path or not viz_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Visualization '{viz_type}' not found for assessment {assessment_id}"
            )
        
        # Return file download
        if download:
            return FileResponse(
                path=str(viz_path),
                filename=f"{viz_type}_{assessment_id}.html",
                media_type="text/html"
            )
        
        # Return metadata
        file_size = viz_path.stat().st_size
        return VisualizationResponse(
            visualization_id=f"{assessment_id}_{viz_type}",
            assessment_id=assessment_id,
            visualization_type=viz_type,
            file_path=str(viz_path),
            view_url=f"/api/v1/visualizations/{assessment_id}/view?viz_type={viz_type}"
        )
        
    except Exception as e:
        logger.error(f"Error getting visualization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/visualizations/{assessment_id}/view")
async def view_visualization(
    assessment_id: str,
    viz_type: str = Query("dashboard", description="Visualization type")
):
    """
    View a generated visualization in the browser.
    
    Args:
        assessment_id: Unique assessment identifier
        viz_type: Type of visualization
        
    Returns:
        HTML content response
        
    Raises:
        HTTPException: If visualization not found
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        allowed_types = ["dashboard", "archetype_map", "individual_profile", "cluster_analysis"]
        if viz_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Visualization type must be one of: {allowed_types}"
            )
        
        # Find visualization file
        viz_path = None
        
        # Search for visualization files
        if viz_type == "dashboard":
            viz_path = OUTPUT_DIR / "dashboard.html"
        elif viz_type == "archetype_map":
            viz_path = OUTPUT_DIR / "archetype_map.html"
        else:
            # Search in profiles directory
            profiles_dir = OUTPUT_DIR / "profiles"
            if profiles_dir.exists():
                for file_path in profiles_dir.glob(f"*{assessment_id}*.html"):
                    viz_path = file_path
                    break
        
        if not viz_path or not viz_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Visualization '{viz_type}' not found for assessment {assessment_id}"
            )
        
        # Read and return HTML content
        with open(viz_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error viewing visualization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/visualizations/{assessment_id}/download")
async def download_visualization(
    assessment_id: str,
    viz_type: str = Query("dashboard", description="Visualization type")
):
    """
    Download a generated visualization file.
    
    Args:
        assessment_id: Unique assessment identifier
        viz_type: Type of visualization
        
    Returns:
        File download response
        
    Raises:
        HTTPException: If visualization not found
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        allowed_types = ["dashboard", "archetype_map", "individual_profile", "cluster_analysis"]
        if viz_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Visualization type must be one of: {allowed_types}"
            )
        
        # Find visualization file
        viz_path = None
        
        # Search for visualization files
        if viz_type == "dashboard":
            viz_path = OUTPUT_DIR / "dashboard.html"
        elif viz_type == "archetype_map":
            viz_path = OUTPUT_DIR / "archetype_map.html"
        else:
            # Search in profiles directory
            profiles_dir = OUTPUT_DIR / "profiles"
            if profiles_dir.exists():
                for file_path in profiles_dir.glob(f"*{assessment_id}*.html"):
                    viz_path = file_path
                    break
        
        if not viz_path or not viz_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Visualization '{viz_type}' not found for assessment {assessment_id}"
            )
        
        return FileResponse(
            path=str(viz_path),
            filename=f"{viz_type}_{assessment_id}.html",
            media_type="text/html"
        )
        
    except Exception as e:
        logger.error(f"Error downloading visualization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reports")
async def list_reports(
    assessment_id: Optional[str] = Query(None, description="Filter by assessment ID"),
    format: Optional[str] = Query(None, description="Filter by format (html or pdf)")
):
    """
    List all available reports.
    
    Args:
        assessment_id: Optional assessment ID filter
        format: Optional format filter
        
    Returns:
        List of available reports
    """
    try:
        reports = []
        
        if not REPORTS_DIR.exists():
            return {"reports": reports}
        
        # Search for report files
        for file_path in REPORTS_DIR.glob("*.html"):
            if assessment_id and assessment_id not in file_path.stem:
                continue
            if format and format != "html":
                continue
            
            reports.append({
                "file_name": file_path.name,
                "file_path": str(file_path),
                "format": "html",
                "file_size": file_path.stat().st_size,
                "modified_time": file_path.stat().st_mtime
            })
        
        for file_path in REPORTS_DIR.glob("*.pdf"):
            if assessment_id and assessment_id not in file_path.stem:
                continue
            if format and format != "pdf":
                continue
            
            reports.append({
                "file_name": file_path.name,
                "file_path": str(file_path),
                "format": "pdf",
                "file_size": file_path.stat().st_size,
                "modified_time": file_path.stat().st_mtime
            })
        
        return {"reports": reports, "total": len(reports)}
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/visualizations")
async def list_visualizations(
    assessment_id: Optional[str] = Query(None, description="Filter by assessment ID"),
    viz_type: Optional[str] = Query(None, description="Filter by visualization type")
):
    """
    List all available visualizations.
    
    Args:
        assessment_id: Optional assessment ID filter
        viz_type: Optional visualization type filter
        
    Returns:
        List of available visualizations
    """
    try:
        visualizations = []
        
        # Search for visualization files
        viz_files = []
        
        # Dashboard files
        if OUTPUT_DIR.exists():
            for file_path in OUTPUT_DIR.glob("dashboard*.html"):
                viz_files.append(("dashboard", file_path))
            
            for file_path in OUTPUT_DIR.glob("archetype_map*.html"):
                viz_files.append(("archetype_map", file_path))
        
        # Profile files
        profiles_dir = OUTPUT_DIR / "profiles"
        if profiles_dir.exists():
            for file_path in profiles_dir.glob("*.html"):
                viz_files.append(("individual_profile", file_path))
        
        # Filter and format results
        for viz_type_found, file_path in viz_files:
            if assessment_id and assessment_id not in file_path.stem:
                continue
            if viz_type and viz_type != viz_type_found:
                continue
            
            visualizations.append({
                "file_name": file_path.name,
                "file_path": str(file_path),
                "visualization_type": viz_type_found,
                "file_size": file_path.stat().st_size,
                "modified_time": file_path.stat().st_mtime
            })
        
        return {"visualizations": visualizations, "total": len(visualizations)}
        
    except Exception as e:
        logger.error(f"Error listing visualizations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/reports/{assessment_id}")
async def delete_report(
    assessment_id: str,
    format: Optional[str] = Query(None, description="Format to delete (html or pdf)")
):
    """
    Delete a report file.
    
    Args:
        assessment_id: Assessment ID
        format: Optional format filter
        
    Returns:
        Deletion confirmation
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        deleted_files = []
        
        if not REPORTS_DIR.exists():
            raise HTTPException(status_code=404, detail="No reports found")
        
        # Delete specific format or all formats
        formats_to_delete = [format] if format else ["html", "pdf"]
        
        for fmt in formats_to_delete:
            if fmt not in ["html", "pdf"]:
                continue
            
            for file_path in REPORTS_DIR.glob(f"*{assessment_id}*.{fmt}"):
                try:
                    file_path.unlink()
                    deleted_files.append(str(file_path))
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {str(e)}")
        
        if not deleted_files:
            raise HTTPException(status_code=404, detail=f"No reports found for assessment {assessment_id}")
        
        return {
            "message": f"Deleted {len(deleted_files)} report file(s)",
            "deleted_files": deleted_files
        }
        
    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/visualizations/{assessment_id}")
async def delete_visualization(
    assessment_id: str,
    viz_type: Optional[str] = Query(None, description="Visualization type to delete")
):
    """
    Delete a visualization file.
    
    Args:
        assessment_id: Assessment ID
        viz_type: Optional visualization type filter
        
    Returns:
        Deletion confirmation
    """
    try:
        if not validate_assessment_id(assessment_id):
            raise HTTPException(status_code=400, detail="Invalid assessment ID format")
        
        deleted_files = []
        
        # Delete specific visualization or all visualizations
        if viz_type:
            # Delete specific type
            if viz_type == "dashboard":
                viz_path = OUTPUT_DIR / "dashboard.html"
                if viz_path.exists():
                    viz_path.unlink()
                    deleted_files.append(str(viz_path))
            elif viz_type == "archetype_map":
                viz_path = OUTPUT_DIR / "archetype_map.html"
                if viz_path.exists():
                    viz_path.unlink()
                    deleted_files.append(str(viz_path))
            else:
                # Delete from profiles directory
                profiles_dir = OUTPUT_DIR / "profiles"
                if profiles_dir.exists():
                    for file_path in profiles_dir.glob(f"*{assessment_id}*.html"):
                        file_path.unlink()
                        deleted_files.append(str(file_path))
        else:
            # Delete all visualizations for assessment
            for viz_path in [OUTPUT_DIR / "dashboard.html", OUTPUT_DIR / "archetype_map.html"]:
                if viz_path.exists():
                    viz_path.unlink()
                    deleted_files.append(str(viz_path))
            
            profiles_dir = OUTPUT_DIR / "profiles"
            if profiles_dir.exists():
                for file_path in profiles_dir.glob(f"*{assessment_id}*.html"):
                    file_path.unlink()
                    deleted_files.append(str(file_path))
        
        if not deleted_files:
            raise HTTPException(status_code=404, detail=f"No visualizations found for assessment {assessment_id}")
        
        return {
            "message": f"Deleted {len(deleted_files)} visualization file(s)",
            "deleted_files": deleted_files
        }
        
    except Exception as e:
        logger.error(f"Error deleting visualization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")