#!/usr/bin/env python3
"""
Test script to verify HTML reports work with the updated RaschPy and Scoring Engine pipeline.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import required modules
from reports.report_generator import generate_comprehensive_report, generate_batch_reports
from scoring.scoring_engine import PersonScore, ConstructScore

def create_test_person_data():
    """Create a mock PersonScore object for testing."""
    
    # Create mock construct scores
    construct_scores = [
        ConstructScore(
            construct_id="RT",
            construct_name="Risk Taking",
            score=0.75,
            percentile=75.0
        ),
        ConstructScore(
            construct_id="DA",
            construct_name="Drive & Ambition",
            score=0.85,
            percentile=85.0
        ),
        ConstructScore(
            construct_id="IO",
            construct_name="Innovation Orientation",
            score=0.65,
            percentile=65.0
        ),
        ConstructScore(
            construct_id="SL",
            construct_name="Servant Leadership",
            score=0.70,
            percentile=70.0
        ),
        ConstructScore(
            construct_id="RG",
            construct_name="Resilience & Grit",
            score=0.80,
            percentile=80.0
        ),
        ConstructScore(
            construct_id="EI",
            construct_name="Emotional Intelligence",
            score=0.60,
            percentile=60.0
        ),
        ConstructScore(
            construct_id="PS",
            construct_name="Problem Solving",
            score=0.55,
            percentile=55.0
        ),
        ConstructScore(
            construct_id="A",
            construct_name="Accountability",
            score=0.90,
            percentile=90.0
        )
    ]
    
    # Create mock person score
    person = PersonScore(
        person_id="test_person_001",
        overall_score=0.72,
        overall_percentile=72.0,
        construct_scores=construct_scores,
        item_scores={},
        completion_rate=0.95,
        reliability_scores={},
        percentile_ranks={},
        raw_responses={}
    )
    
    return person

def create_test_cluster_data():
    """Create mock cluster data for testing."""
    
    class MockCluster:
        def __init__(self):
            self.archetype_name = "Strategic Innovator"
            self.description = "Balances strategic thinking with creative problem-solving. Demonstrates strong leadership potential with a focus on sustainable innovation."
            self.size = 15
            self.person_ids = ["test_person_001"]
            # Add characteristics attribute to avoid template errors
            self.characteristics = type('obj', (object,), {'archetype_key': 'strategic_innovator'})()
    
    return MockCluster()

def create_test_raw_data():
    """Create mock raw data for RaschPy processing."""
    
    # Create sample assessment data
    data = {
        'Measure': [1.37, 0.85, 1.92, 0.65, 1.45, 0.90, 1.25, 0.75],
        'E1': [1, 1, 1, 1, 1, 1, 1, 1],
        'E2': [1, 2, 3, 4, 5, 6, 7, 8],
        'Persons': ['test_person_001'] * 8,
        'Assessment_Items': [
            'RiskTaking_Q1', 'DriveAmbition_Q1', 'Innovation_Q1', 'Leadership_Q1',
            'Resilience_Q1', 'EmotionalIntel_Q1', 'ProblemSolving_Q1', 'Accountability_Q1'
        ]
    }
    
    return pd.DataFrame(data)

def test_html_report_generation():
    """Test HTML report generation with visualizations."""
    
    print("🧪 Testing HTML Report Generation...")
    
    # Create test data
    person = create_test_person_data()
    cluster = create_test_cluster_data()
    raw_data = create_test_raw_data()
    
    # Test 1: Generate comprehensive report without raw data
    print("\n1. Testing comprehensive report generation (no raw data)...")
    try:
        html_content = generate_comprehensive_report(
            person=person,
            cluster=cluster,
            include_visuals=True,
            output_format="html"
        )
        
        if html_content and len(html_content) > 1000:
            print("✅ HTML report generated successfully (no raw data)")
            print(f"   Report length: {len(html_content)} characters")
        else:
            print("❌ HTML report generation failed (too short)")
        
    except Exception as e:
        print(f"❌ Error generating HTML report: {e}")
    
    # Test 2: Generate comprehensive report with raw data (RaschPy integration)
    print("\n2. Testing comprehensive report generation (with raw data)...")
    try:
        html_content = generate_comprehensive_report(
            person=person,
            cluster=cluster,
            include_visuals=True,
            output_format="html",
            raw_data=raw_data
        )
        
        if html_content and len(html_content) > 1000:
            print("✅ HTML report generated successfully (with raw data)")
            print(f"   Report length: {len(html_content)} characters")
        else:
            print("❌ HTML report generation failed (too short)")
        
    except Exception as e:
        print(f"❌ Error generating HTML report with raw data: {e}")
    
    # Test 3: Generate batch reports
    print("\n3. Testing batch report generation...")
    try:
        # Create output directory
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate batch reports
        generated_files = generate_batch_reports(
            person_scores=[person],
            cluster_results=[cluster],
            output_directory=output_dir,
            format="html"
        )
        
        if generated_files and generated_files.get('html'):
            print("✅ Batch reports generated successfully")
            for file_path in generated_files['html']:
                print(f"   Generated: {file_path}")
                
                # Check if file exists and has content
                if os.path.exists(file_path) and os.path.getsize(file_path) > 1000:
                    print(f"   ✅ File verified: {os.path.getsize(file_path)} bytes")
                else:
                    print(f"   ❌ File verification failed")
        else:
            print("❌ Batch report generation failed")
        
    except Exception as e:
        print(f"❌ Error generating batch reports: {e}")

def test_visualization_generation():
    """Test visualization generation specifically."""
    
    print("\n🎨 Testing Visualization Generation...")
    
    person = create_test_person_data()
    
    # Import visualization engine
    try:
        from visualization.visualization_engine import PsychometricVisualizationEngine
        
        viz_engine = PsychometricVisualizationEngine()
        
        # Test embedded chart generation
        print("\n1. Testing embedded chart generation...")
        try:
            chart_html = viz_engine.create_embedded_chart_html(person)
            
            if chart_html and len(chart_html) > 100:
                print("✅ Embedded chart generated successfully")
                print(f"   Chart HTML length: {len(chart_html)} characters")
            else:
                print("❌ Embedded chart generation failed")
                
        except Exception as e:
            print(f"❌ Error generating embedded chart: {e}")
        
        # Test radar chart generation
        print("\n2. Testing radar chart generation...")
        try:
            radar_path = "test_output/test_radar.html"
            success = viz_engine.create_radar_chart(person, radar_path)
            
            if success and os.path.exists(radar_path):
                print("✅ Radar chart generated successfully")
                print(f"   File: {radar_path}")
            else:
                print("❌ Radar chart generation failed")
                
        except Exception as e:
            print(f"❌ Error generating radar chart: {e}")
    
    except ImportError as e:
        print(f"❌ Could not import visualization engine: {e}")

def test_pipeline_integration():
    """Test the complete pipeline integration."""
    
    print("\n🔄 Testing Pipeline Integration...")
    
    # Test RaschAnalyzer integration
    print("\n1. Testing RaschAnalyzer integration...")
    try:
        from data.rasch_analysis import RaschAnalyzer
        
        analyzer = RaschAnalyzer()
        raw_data = create_test_raw_data()
        
        # Test individual person analysis
        results = analyzer.analyze_person_data("test_person_001", raw_data)
        
        if results.success:
            print("✅ RaschAnalyzer integration successful")
            print(f"   Transformed data shape: {results.transformed_data.shape if results.transformed_data is not None else 'N/A'}")
        else:
            print("❌ RaschAnalyzer integration failed")
            print(f"   Errors: {results.errors}")
        
    except Exception as e:
        print(f"❌ Error testing RaschAnalyzer: {e}")
    
    # Test ScoringEngine integration
    print("\n2. Testing ScoringEngine integration...")
    try:
        from scoring.scoring_engine import PsychometricScoringEngine
        
        scoring_engine = PsychometricScoringEngine()
        raw_data = create_test_raw_data()
        
        # Test individual scoring
        scores = scoring_engine.calculate_individual_scores("test_person_001", raw_data)
        
        if scores:
            print("✅ ScoringEngine integration successful")
            print(f"   Overall score: {scores.get('overall_score', 'N/A')}")
            print(f"   Construct scores: {len(scores.get('construct_scores', {}))}")
        else:
            print("❌ ScoringEngine integration failed")
        
    except Exception as e:
        print(f"❌ Error testing ScoringEngine: {e}")

def main():
    """Run all tests."""
    
    print("🚀 Starting HTML Reports Integration Test")
    print("=" * 60)
    
    # Run tests
    test_html_report_generation()
    test_visualization_generation()
    test_pipeline_integration()
    
    print("\n" + "=" * 60)
    print("✅ Test completed! Check the output above for results.")
    print("📁 Generated test files are in the 'test_output' directory.")

if __name__ == "__main__":
    main()