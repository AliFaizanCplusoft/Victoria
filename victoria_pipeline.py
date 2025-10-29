#!/usr/bin/env python3
"""
Vetria Entrepreneurial Assessment Pipeline
Main pipeline script that orchestrates all modules to generate comprehensive reports
"""

import sys
import os
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('victoria_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Override system environment variable with .env file value
# This ensures our .env file takes precedence over system environment variables
env_file_path = Path(__file__).parent / ".env"
if env_file_path.exists():
    with open(env_file_path, 'r', encoding='utf-8-sig') as f:  # Handle BOM
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                # Force override the environment variable
                os.environ[key] = value
                logger.info(f"Set environment variable: {key}={value[:20]}...")
    
    # Explicitly verify the override worked
    final_key = os.getenv("OPENAI_API_KEY")
    logger.info(f"Final API key after override: {final_key[:20] if final_key else 'None'}...")

# Import core modules
from victoria.core import DataProcessor, ArchetypeDetector, VisualizationEngine, ReportGenerator
from victoria.scoring.fixed_trait_scorer import FixedTraitScorer

# OpenAI API key should be set via environment variable
# Set it in your .env file or export OPENAI_API_KEY=your_key_here
# This ensures no hardcoded API keys are committed to the repository

class VetriaPipeline:
    """
    Main pipeline class that orchestrates the complete Vetria assessment process
    """
    
    def __init__(self):
        """Initialize the Vetria pipeline with all core components"""
        self.data_processor = DataProcessor()
        self.trait_scorer = FixedTraitScorer()
        self.archetype_detector = ArchetypeDetector()
        self.visualization_engine = VisualizationEngine()
        self.report_generator = ReportGenerator()
        
        # Initialize OpenAI client
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            logger.info(f"DEBUG - API Key from environment: {api_key[:20] if api_key else 'None'}...")
            logger.info(f"DEBUG - Full API Key: {api_key}")
            
            # Check all environment variables that start with OPENAI
            openai_vars = {k: v for k, v in os.environ.items() if k.startswith('OPENAI')}
            logger.info(f"DEBUG - All OPENAI environment variables: {openai_vars}")
            
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                self.report_generator.openai_client = self.openai_client
                logger.info("OpenAI client initialized with API key from environment")
            else:
                logger.warning("OPENAI_API_KEY not found in environment variables")
                self.openai_client = None
        except ImportError:
            logger.warning("OpenAI not available, using fallback content generation")
            self.openai_client = None
    
    def extract_open_ended_responses(self, df: pd.DataFrame, person_index: int = 0) -> Dict[str, str]:
        """Extract open-ended text responses from the dataframe and organize them by category"""
        # Define the open-ended question columns (A to Z range in the CSV)
        open_ended_columns = [
            "What inspired your business idea, and how did it first come to you?",
            "What specific problem does your business solve, and who benefits most from it?",
            "Where are you in the process—idea stage, prototype, launch, or beyond?",
            "What is one decision you've already made that challenged you?",
            "How do your personal values show up in your business idea?",
            "What kind of impact do you hope your business will create—in your life or for others?",
            "What kind of support would help you move forward right now?",
            "What is drawing you toward entrepreneurship at this moment in your life?",
            "What does \"entrepreneurship\" mean to you personally?",
            "What's a time when you took initiative or built something from scratch?",
            "What fears or uncertainties do you have about starting something of your own?",
            "What kind of work energizes you most—and why?",
            "When you imagine your future, what role (if any) does building something yourself play?",
            "What questions are you hoping this experience will help you answer?",
            "What would success look like for you in this phase of exploration?",
            "What kinds of work or challenges bring out the best in you?",
            "When have you taken the lead without being asked—and what happened?",
            "Where do you feel most confident in how you contribute?",
            "What's something others often rely on you for?",
            "How do you typically approach uncertainty or change?",
            "What are you learning about yourself right now—and what are you still figuring out?",
            "If you were to fully embrace your entrepreneurial energy, what might become possible?"
        ]
        
        responses = {}
        for col in open_ended_columns:
            if col in df.columns:
                response = df.iloc[person_index][col]
                # Only add if response exists and is not empty
                if pd.notna(response) and str(response).strip() and str(response).strip() != '':
                    responses[col] = str(response).strip()
                    print(f"DEBUG - Found response for '{col}': {str(response).strip()[:50]}...")
                else:
                    print(f"DEBUG - Skipping empty response for '{col}'")
        
        # Also check for the journey question which might be in a different column
        journey_question = "Which of the following best describes where you are in your entrepreneurial journey?"
        if journey_question in df.columns:
            response = df.iloc[person_index][journey_question]
            if pd.notna(response) and str(response).strip() and str(response).strip() != '':
                responses[journey_question] = str(response).strip()
                print(f"DEBUG - Found journey response: {str(response).strip()[:50]}...")
        
        print(f"DEBUG - Total open-ended responses found: {len(responses)}")
        return responses
    
    def process_single_person(self, csv_path: str, person_index: int = 0) -> Dict[str, Any]:
        """
        Process a single person's assessment data through the complete pipeline
        
        Args:
            csv_path: Path to CSV file with assessment responses
            person_index: Index of person to process (default: 0)
            
        Returns:
            Dictionary containing complete profile data
        """
        try:
            logger.info("=" * 80)
            logger.info("VETRIA ENTREPRENEURIAL ASSESSMENT PIPELINE")
            logger.info("=" * 80)
            
            # Step 1: Load and process raw data
            logger.info("Step 1: Loading raw data...")
            raw_data = self.data_processor._load_raw_data(csv_path)
            logger.info(f"Loaded {len(raw_data)} rows, {len(raw_data.columns)} columns")
            
            # Step 2: Map responses to numeric values
            logger.info("Step 2: Mapping responses to numeric values...")
            mapped_data = self.data_processor._map_responses(raw_data)
            logger.info("Response mapping completed")
            
            # Step 3: Calculate Rasch measures
            logger.info("Step 3: Calculating Rasch measures...")
            rasch_data = self.data_processor._calculate_rasch_measures(mapped_data)
            logger.info("Rasch measures calculated")
            
            # Step 4: Calculate trait scores
            logger.info("Step 4: Calculating trait scores...")
            trait_profiles = self.trait_scorer.calculate_trait_scores(raw_data)
            person_id = f"person_{person_index}"
            
            if person_id not in trait_profiles:
                raise ValueError(f"Person {person_id} not found in trait profiles")
            
            trait_scores = trait_profiles[person_id]
            logger.info(f"Trait scores calculated for {len(trait_scores)} traits")
            
            # Step 5: Detect archetype
            logger.info("Step 5: Detecting entrepreneurial archetype...")
            archetype_result = self.archetype_detector.detect_archetype(trait_scores)
            logger.info(f"Detected archetype: {archetype_result['archetype_name']} (confidence: {archetype_result['confidence']:.1%})")
            
            # Step 6: Extract open-ended responses
            logger.info("Step 6: Extracting open-ended responses...")
            open_ended_responses = self.extract_open_ended_responses(raw_data, person_index)
            logger.info(f"Extracted {len(open_ended_responses)} open-ended responses")
            
            # Step 7: Calculate overall score
            overall_score = sum(trait_scores.values()) / len(trait_scores)
            
            # Step 8: Prepare profile data
            profile_data = {
                'person_name': f"{raw_data.iloc[person_index].get('First name', 'Unknown')} {raw_data.iloc[person_index].get('Last name', '')}".strip(),
                'person_email': raw_data.iloc[person_index].get('Email', ''),
                'trait_scores': trait_scores,
                'archetype_name': archetype_result['archetype_name'],
                'archetype_description': archetype_result['archetype_description'],
                'archetype_color': archetype_result['archetype_color'],
                'archetype_score': round(archetype_result['archetype_score'] * 100, 1),  # Convert to percentage
                'confidence': archetype_result['confidence'],
                'overall_score': overall_score,
                'open_ended_responses': open_ended_responses,
                'entrepreneurial_stage': 'Discover',  # Default stage
                'entrepreneurial_stage_class': 'discover',
                'entrepreneurial_stage_description': 'You want to understand how entrepreneurial energy shapes your path. This stage is about self-discovery, building awareness, and connecting your natural strengths to potential opportunities.',
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'archetype_match_explanation': f'Your strongest alignment is with {archetype_result["archetype_name"]}, showing high potential to lead through creativity and forward vision'
            }
            
            # Step 9: Generate visualizations
            logger.info("Step 9: Generating visualizations...")
            visualizations = self.visualization_engine.generate_all_visualizations(profile_data)
            profile_data.update(visualizations)
            
            # Step 10: Generate inspiring content
            logger.info("Step 10: Generating inspiring content...")
            inspiring_content = self.report_generator.generate_inspiring_content(profile_data)
            profile_data.update(inspiring_content)
            
            logger.info("SUCCESS: Profile processing completed!")
            return profile_data
                
        except Exception as e:
            logger.error(f"Error processing person {person_index}: {e}")
            raise
    
    def generate_report(self, csv_path: str, output_dir: str = "output/reports", person_index: int = 0) -> str:
        """
        Generate a complete assessment report for a single person
        
        Args:
            csv_path: Path to CSV file with assessment responses
            output_dir: Directory to save the report
            person_index: Index of person to process
            
        Returns:
            Path to the generated report file
        """
        try:
            # Process the person's data
            profile_data = self.process_single_person(csv_path, person_index)
            
            # Generate report filename
            person_name = profile_data['person_name'].replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"vetria_report_{person_name}_{timestamp}.html"
            report_path = os.path.join(output_dir, report_filename)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate the report
            logger.info("Generating comprehensive report...")
            result = self.report_generator.generate_comprehensive_report(profile_data, report_path)
            
            if result['success']:
                logger.info(f"SUCCESS: Report generated!")
                logger.info(f"Report file: {report_filename}")
                logger.info(f"File path: {result['file_path']}")
                logger.info(f"Open in browser: file://{os.path.abspath(result['file_path'])}")
                return result['file_path']
            else:
                raise Exception(f"Report generation failed: {result['error']}")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

def main():
    """Main function to run the Victoria pipeline"""
    if len(sys.argv) < 2:
        print("Usage: python victoria_pipeline.py <csv_file> [person_index]")
        print("Example: python victoria_pipeline.py responses.csv 0")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    person_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found")
        sys.exit(1)
    
    try:
        # Initialize pipeline
        pipeline = VetriaPipeline()
        
        # Generate report
        report_path = pipeline.generate_report(csv_path, person_index=person_index)
        
        print(f"\nReport successfully generated!")
        print(f"Report: {report_path}")
        print(f"Open in browser: file://{os.path.abspath(report_path)}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()