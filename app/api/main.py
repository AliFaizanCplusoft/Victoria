"""
FastAPI Application Entry Point
Clean, modular API for Victoria Project
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, List, Optional
import uvicorn

# Victoria imports
from victoria.config.settings import config, app_config, brand_config
from victoria.utils.logging_config import setup_logging
from victoria.scoring.trait_scorer import TraitScorer
from victoria.clustering.trait_clustering_engine import TraitClusteringEngine
from victoria.clustering.archetype_mapper import ArchetypeMapper
from victoria.core.models import PersonTraitProfile, ClusteringResult

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Victoria API...")
    yield
    logger.info("Shutting down Victoria API...")

# Create FastAPI application
app = FastAPI(
    title="Victoria Project API",
    description="Psychometric Assessment Analysis API with Entrepreneurial Archetype Integration",
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

# Global services
trait_scorer = TraitScorer()
clustering_engine = TraitClusteringEngine()
archetype_mapper = ArchetypeMapper()

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Victoria Project API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "trait_scorer": "ready",
            "clustering_engine": "ready", 
            "archetype_mapper": "ready"
        }
    }

@app.post("/api/v1/analyze/individual")
async def analyze_individual(
    responses_file: UploadFile = File(...),
    person_id: Optional[str] = None
):
    """Analyze individual psychometric profile"""
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await responses_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process data
            traits_file = config.traits_file_path
            profiles = trait_scorer.calculate_trait_scores(tmp_file_path, traits_file)
            
            if not profiles:
                raise HTTPException(status_code=400, detail="No profiles could be processed")
            
            # Return specific individual or first one
            if person_id and person_id in profiles:
                profile = profiles[person_id]
            else:
                profile = next(iter(profiles.values()))
            
            return {
                "status": "success",
                "profile": {
                    "person_id": profile.person_id,
                    "overall_score": profile.overall_score,
                    "completion_rate": profile.completion_rate,
                    "traits": [
                        {
                            "trait_name": trait.trait_name,
                            "score": trait.score,
                            "percentile": trait.percentile,
                            "level": trait.level.value if trait.level else None
                        }
                        for trait in profile.traits
                    ],
                    "primary_archetype": {
                        "archetype": profile.primary_archetype.archetype.value,
                        "score": profile.primary_archetype.score,
                        "confidence": profile.primary_archetype.confidence,
                        "description": profile.primary_archetype.description
                    } if profile.primary_archetype else None,
                    "recommendations": profile.recommendations,
                    "growth_areas": profile.growth_areas
                }
            }
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Individual analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze/cluster")
async def analyze_clusters(
    responses_file: UploadFile = File(...),
    method: str = "kmeans",
    n_clusters: int = 5
):
    """Perform trait clustering analysis"""
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await responses_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process data
            traits_file = config.traits_file_path
            profiles = trait_scorer.calculate_trait_scores(tmp_file_path, traits_file)
            
            if not profiles:
                raise HTTPException(status_code=400, detail="No profiles could be processed")
            
            # Perform clustering
            cluster_results = clustering_engine.analyze_trait_clusters(
                profiles, method=method, n_clusters=n_clusters
            )
            
            return {
                "status": "success",
                "clustering_results": {
                    "n_clusters": cluster_results.n_clusters,
                    "silhouette_score": cluster_results.silhouette_score,
                    "explained_variance": cluster_results.explained_variance,
                    "method_used": cluster_results.method_used,
                    "clusters": [
                        {
                            "cluster_id": cluster.cluster_id,
                            "cluster_name": cluster.cluster_name,
                            "description": cluster.description,
                            "size": cluster.size,
                            "dominant_traits": cluster.traits,
                            "archetype_mapping": cluster.archetype_mapping.value if cluster.archetype_mapping else None
                        }
                        for cluster in cluster_results.clusters
                    ],
                    "archetype_mappings": {
                        str(k): v.value for k, v in cluster_results.archetype_mappings.items()
                    }
                }
            }
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Cluster analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/archetypes")
async def get_archetypes():
    """Get information about Vertria's entrepreneurial archetypes"""
    from victoria.config.settings import archetype_config
    
    return {
        "status": "success",
        "archetypes": {
            key: {
                "name": info["name"],
                "description": info["description"],
                "core_traits": info["core_traits"],
                "characteristics": info["characteristics"]
            }
            for key, info in archetype_config.ARCHETYPES.items()
        }
    }

@app.get("/api/v1/traits")
async def get_traits():
    """Get information about core traits"""
    from victoria.config.settings import trait_config
    
    return {
        "status": "success",
        "traits": trait_config.CORE_TRAITS
    }

@app.post("/api/v1/reports/html")
async def generate_html_report(
    responses_file: UploadFile = File(...),
    person_id: Optional[str] = None
):
    """Generate HTML report for individual"""
    # This will be implemented in the reporting module
    return {
        "status": "success",
        "message": "HTML report generation will be implemented in the next phase"
    }

@app.get("/api/v1/config")
async def get_configuration():
    """Get API configuration information"""
    return {
        "status": "success",
        "config": {
            "version": "1.0.0",
            "environment": app_config.ENVIRONMENT,
            "features": {
                "llm_reports": app_config.ENABLE_LLM_REPORTS,
                "caching": app_config.LLM_CACHE_ENABLED
            },
            "brand": {
                "colors": brand_config.COLORS,
                "fonts": brand_config.FONTS
            }
        }
    }

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
        host=app_config.API_HOST,
        port=app_config.API_PORT,
        reload=app_config.DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    main()