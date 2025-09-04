#!/usr/bin/env python3
"""
Test script to generate a refined report with all enhancements
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from victoria.core.models import PersonTraitProfile, ArchetypeScore, TraitScore
from victoria.core.enums import ArchetypeType, TraitType
from victoria.reporting.dynamic_report_generator import DynamicReportGenerator

def create_test_profile():
    """Create a test profile for demonstration"""
    
    # Create trait scores - using realistic values
    traits = [
        TraitScore(trait_name="Risk Taking", score=0.73, percentile=72.60, items_count=8, description="Willingness to pursue opportunities despite uncertainty"),
        TraitScore(trait_name="Innovation", score=0.88, percentile=87.79, items_count=7, description="Ability to generate creative solutions"),
        TraitScore(trait_name="Leadership", score=0.89, percentile=89.36, items_count=9, description="Capacity to inspire and guide others"),
        TraitScore(trait_name="Resilience", score=0.79, percentile=79.37, items_count=6, description="Ability to bounce back from setbacks"),
        TraitScore(trait_name="Accountability", score=0.89, percentile=89.29, items_count=5, description="Taking ownership of outcomes"),
        TraitScore(trait_name="Decision Making", score=0.92, percentile=92.06, items_count=7, description="Making effective choices quickly"),
        TraitScore(trait_name="Adaptability", score=0.94, percentile=93.57, items_count=8, description="Flexibility to adjust strategies"),
        TraitScore(trait_name="Continuous Learning", score=0.94, percentile=94.05, items_count=6, description="Commitment to ongoing skill development"),
        TraitScore(trait_name="Passion/Drive", score=0.77, percentile=77.20, items_count=7, description="Intrinsic motivation toward goals"),
        TraitScore(trait_name="Problem Solving", score=0.87, percentile=87.34, items_count=8, description="Systematic approach to challenges"),
        TraitScore(trait_name="Emotional Intelligence", score=0.94, percentile=93.62, items_count=9, description="Understanding and managing emotions"),
    ]
    
    # Create primary archetype
    primary_archetype = ArchetypeScore(
        archetype=ArchetypeType.ADAPTIVE_INTELLIGENCE,
        score=1.0,
        confidence=0.95,
        matching_traits=["Continuous Learning", "Emotional Intelligence", "Adaptability"],
        description="Logical problem-solvers who understand team/customer needs",
        characteristics=["Analytical", "Empathetic", "Flexible", "Customer-focused"]
    )
    
    # Create profile
    profile = PersonTraitProfile(
        person_id="TestUser_Refined",
        traits=traits,
        primary_archetype=primary_archetype,
        overall_score=0.87,
        completion_rate=1.0
    )
    
    return profile

def main():
    """Generate and save the refined report"""
    print("Generating refined Victoria Project report...")
    
    try:
        # Create test profile
        profile = create_test_profile()
        
        # Initialize generator
        generator = DynamicReportGenerator()
        
        # Generate report
        html_content = generator.create_html_report(profile)
        
        # Create output directory if needed
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"vertria_refined_report_{profile.person_id}_{timestamp}.html"
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"SUCCESS: Refined report generated successfully!")
        print(f"File: {output_path}")
        print(f"Profile: {profile.person_id}")
        print(f"Archetype: {profile.primary_archetype.archetype.value.replace('_', ' ').title()}")
        print(f"Overall Score: {int(profile.overall_score * 100)}%")
        
        # Report enhancements summary
        print("\nReport Enhancements Applied:")
        print("  - Enhanced visual hierarchy with professional typography")
        print("  - Improved data visualization with interactive charts") 
        print("  - Advanced insights with performance analysis")
        print("  - Archetype comparison visualization")
        print("  - Contextual growth recommendations")
        print("  - Modern UI with hover effects and animations")
        print("  - Responsive design for all devices")
        print("  - Professional Vertria brand integration")
        
    except Exception as e:
        print(f"ERROR: Error generating report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()