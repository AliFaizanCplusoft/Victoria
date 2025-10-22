#!/usr/bin/env python3
"""
Victoria Project - Unified Main Entry Point
Comprehensive psychometric assessment analysis system with Vertria archetype integration

Usage:
    python main.py                    # Show help and options
    python main.py streamlit          # Run Streamlit web interface
    python main.py api                # Run FastAPI server
    python main.py process <file>     # Process data directly
    python main.py report <file>      # Generate individual report
    python main.py cluster <file>     # Perform cluster analysis
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Victoria imports
from victoria.config.settings import config, app_config, brand_config
from victoria.utils.logging_config import setup_logging
from victoria.scoring.trait_scorer import TraitScorer
from victoria.clustering.trait_clustering_engine import TraitClusteringEngine
from victoria.clustering.archetype_mapper import ArchetypeMapper
from victoria.reporting.dynamic_report_generator import DynamicReportGenerator

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

class VictoriaProject:
    """Main Victoria Project application class"""
    
    def __init__(self):
        """Initialize Victoria Project components"""
        self.trait_scorer = TraitScorer()
        self.clustering_engine = TraitClusteringEngine()
        self.archetype_mapper = ArchetypeMapper()
        self.report_generator = DynamicReportGenerator()
        
    def run_streamlit(self):
        """Run Streamlit web interface"""
        print("Starting Victoria Project Streamlit Interface...")
        print("URL: http://localhost:8501")
        print("Features: Individual Analysis, Clustering, Reports")
        print("=" * 60)
        
        import subprocess
        app_path = project_root / "app" / "streamlit" / "main.py"
        
        if not app_path.exists():
            print(f"❌ Error: Streamlit app not found at {app_path}")
            return 1
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ]
        
        return subprocess.run(cmd).returncode
    
    def run_api(self):
        """Run FastAPI server"""
        print("Starting Victoria Project API Server...")
        print("API URL: http://localhost:8000")
        print("Docs URL: http://localhost:8000/docs")
        print("Features: REST API, Individual Analysis, Clustering")
        print("=" * 60)
        
        # Import and run API
        api_path = project_root / "app" / "api" / "main.py"
        
        if not api_path.exists():
            print(f"❌ Error: API app not found at {api_path}")
            return 1
        
        # Add the API directory to path and import the app
        sys.path.insert(0, str(api_path.parent))
        from main import app
        
        try:
            import uvicorn
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=8000,
                reload=False,  # Disable reload to avoid file watching issues
                log_level="info"
            )
            return 0
        except KeyboardInterrupt:
            print("\n👋 API server stopped by user")
            return 0
        except Exception as e:
            print(f"❌ API Error: {e}")
            return 1
    
    def process_data(self, responses_file: str) -> Dict[str, Any]:
        """Process psychometric data directly"""
        print(f"Processing data from: {responses_file}")
        
        try:
            # Check files exist
            if not Path(responses_file).exists():
                raise FileNotFoundError(f"Responses file not found: {responses_file}")
            
            traits_file = config.traits_file_path
            if not Path(traits_file).exists():
                raise FileNotFoundError(f"Traits file not found: {traits_file}")
            
            # Calculate trait scores
            print("Calculating trait scores...")
            profiles = self.trait_scorer.calculate_trait_scores(responses_file, traits_file)
            
            if not profiles:
                raise ValueError("No profiles could be processed from the data")
            
            print(f"Processed {len(profiles)} individual profiles")
            
            # Perform clustering
            print("Performing trait clustering...")
            cluster_results = self.clustering_engine.analyze_trait_clusters(profiles)
            
            print(f"Generated {cluster_results.n_clusters} clusters")
            print(f"Silhouette Score: {cluster_results.silhouette_score:.3f}")
            
            # Summary
            results = {
                'profiles_count': len(profiles),
                'clusters_count': cluster_results.n_clusters,
                'silhouette_score': cluster_results.silhouette_score,
                'profiles': profiles,
                'cluster_results': cluster_results
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Data processing error: {e}")
            raise
    
    def generate_report(self, responses_file: str, person_id: Optional[str] = None):
        """Generate individual HTML report"""
        print(f"Generating individual report from: {responses_file}")
        
        try:
            # Process data first
            results = self.process_data(responses_file)
            profiles = results['profiles']
            
            # Select individual
            if person_id and person_id in profiles:
                profile = profiles[person_id]
                print(f"Selected individual: {person_id}")
            else:
                profile = next(iter(profiles.values()))
                print(f"Using first individual: {profile.person_id}")
            
            # Generate HTML report
            print("Generating branded HTML report...")
            report_path = self.report_generator.generate_individual_report(
                profile, 
                output_dir="output"
            )
            
            print(f"Report saved to: {report_path}")
            print(f"Open in browser: file://{Path(report_path).absolute()}")
            
            return report_path
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            raise
    
    def analyze_clusters(self, responses_file: str):
        """Perform comprehensive cluster analysis"""
        print(f"🎯 Performing cluster analysis on: {responses_file}")
        
        try:
            # Process data
            results = self.process_data(responses_file)
            cluster_results = results['cluster_results']
            
            # Display cluster details
            print("\n" + "=" * 60)
            print("📊 CLUSTER ANALYSIS RESULTS")
            print("=" * 60)
            
            print(f"Number of Clusters: {cluster_results.n_clusters}")
            print(f"Silhouette Score: {cluster_results.silhouette_score:.3f}")
            print(f"Explained Variance: {cluster_results.explained_variance:.1%}")
            print(f"Method Used: {cluster_results.method_used}")
            
            print("\n🎯 CLUSTER DETAILS:")
            for i, cluster in enumerate(cluster_results.clusters):
                print(f"\nCluster {i+1}: {cluster.cluster_name}")
                print(f"  Size: {cluster.size} individuals")
                print(f"  Description: {cluster.description}")
                print(f"  Dominant Traits: {', '.join(cluster.traits)}")
                if cluster.archetype_mapping:
                    archetype_name = cluster.archetype_mapping.value.replace('_', ' ').title()
                    print(f"  Archetype: {archetype_name}")
            
            # Archetype distribution
            print("\n🏆 ARCHETYPE MAPPINGS:")
            for cluster_id, archetype in cluster_results.archetype_mappings.items():
                archetype_name = archetype.value.replace('_', ' ').title()
                print(f"  Cluster {cluster_id + 1}: {archetype_name}")
            
            return cluster_results
            
        except Exception as e:
            logger.error(f"Cluster analysis error: {e}")
            raise
    
    def show_info(self):
        """Display comprehensive project information"""
        print("""
VICTORIA PROJECT - Psychometric Assessment Analysis System
===============================================================

FEATURES:
  * Individual psychometric trait analysis 
  * Advanced trait clustering with ML algorithms
  * Vertria's 5 entrepreneurial archetype integration
  * Professional branded HTML reports
  * REST API for integration
  * Streamlit web interface

VERTRIA ENTREPRENEURIAL ARCHETYPES:
  * Strategic Innovation    - Risk Taking + Innovation + Strategic Thinking
  * Resilient Leadership    - Leadership + Resilience + Adaptability  
  * Collaborative Responsibility - Accountability + Team Building + Trust
  * Ambitious Drive        - Passion/Drive + Resilience + Problem Solving
  * Adaptive Intelligence  - Critical Thinking + EQ + Adaptability

USAGE OPTIONS:
  
  Web Interface:
    python main.py streamlit
    -> Opens interactive dashboard at http://localhost:8501
  
  API Server:
    python main.py api  
    -> REST API at http://localhost:8000 (docs: /docs)
  
  Direct Processing:
    python main.py process responses.csv
    -> Process data and show summary
  
  Generate Report:
    python main.py report responses.csv [person_id]
    -> Create individual HTML report
  
  Cluster Analysis:
    python main.py cluster responses.csv
    -> Comprehensive clustering analysis

PROJECT STRUCTURE:
  victoria/              # Core business logic
  |-- config/            # Configuration & settings
  |-- core/              # Domain models & enums
  |-- scoring/           # Psychometric trait scoring
  |-- clustering/        # ML clustering & archetypes
  |-- processing/        # Data processing pipeline
  |-- reporting/         # HTML report generation
  '-- utils/             # Shared utilities
  
  app/                   # Application interfaces
  |-- streamlit/         # Web dashboard
  '-- api/               # REST API

BRAND INTEGRATION:
  * Vertria color palette (Burgundy #570F27, Navy #151A4A, Yellow #FFDC58)
  * Professional typography (Blair ITC, Outfit)
  * Branded report templates with responsive design

For support and documentation, visit the project repository.
        """)

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="Victoria Project - Psychometric Assessment Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Show this help
  python main.py streamlit                    # Run web interface  
  python main.py api                          # Run API server
  python main.py process data/responses.csv   # Process data
  python main.py report data/responses.csv    # Generate report
  python main.py cluster data/responses.csv   # Analyze clusters
        """
    )
    
    parser.add_argument(
        "command",
        choices=["streamlit", "api", "process", "report", "cluster", "info"],
        nargs="?",
        default="info",
        help="Command to execute"
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        help="Input file path for process/report/cluster commands"
    )
    
    parser.add_argument(
        "person_id", 
        nargs="?",
        help="Person ID for individual report generation"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup debug logging if requested
    if args.debug:
        setup_logging(log_level="DEBUG")
    
    # Initialize Victoria Project
    victoria = VictoriaProject()
    
    try:
        if args.command == "streamlit":
            return victoria.run_streamlit()
            
        elif args.command == "api":
            return victoria.run_api()
            
        elif args.command == "process":
            if not args.file:
                print("❌ Error: File path required for process command")
                print("Usage: python main.py process <responses_file>")
                return 1
            
            results = victoria.process_data(args.file)
            print(f"\n✅ Processing completed successfully!")
            print(f"📊 Processed {results['profiles_count']} profiles")
            print(f"🎯 Generated {results['clusters_count']} clusters")
            return 0
            
        elif args.command == "report":
            if not args.file:
                print("❌ Error: File path required for report command")
                print("Usage: python main.py report <responses_file> [person_id]")
                return 1
            
            report_path = victoria.generate_report(args.file, args.person_id)
            print(f"\nReport generation completed!")
            return 0
            
        elif args.command == "cluster":
            if not args.file:
                print("❌ Error: File path required for cluster command")
                print("Usage: python main.py cluster <responses_file>")
                return 1
            
            cluster_results = victoria.analyze_clusters(args.file)
            print(f"\n✅ Cluster analysis completed!")
            return 0
            
        else:  # info or default
            victoria.show_info()
            return 0
            
    except KeyboardInterrupt:
        print("\nOperation stopped by user")
        return 0
        
    except FileNotFoundError as e:
        print(f"FILE ERROR: {e}")
        return 1
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"ERROR: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())