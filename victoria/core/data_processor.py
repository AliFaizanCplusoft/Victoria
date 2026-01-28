"""
Data Processor - Step 1-3: Raw Data to Rasch Measures
Handles response mapping and Rasch processing using genuine RaschPy RSM
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Import Rasch processing components
try:
    from ..processing.response_converter import ResponseConverter
    from ..processing.rasch_processor import RaschPyProcessor
except ImportError:
    logger.warning("Could not import Rasch processing components")
    ResponseConverter = None
    RaschPyProcessor = None

class DataProcessor:
    """
    Processes raw assessment data through response mapping and Rasch analysis
    """
    
    def __init__(self):
        """Initialize data processor"""
        self.response_mapping = {
            'Always (91-100%)': 1.0,
            'Often (66-90%)': 0.7,
            'Sometimes (36-65%)': 0.5,
            'Rarely (11-35%)': 0.2,
            'Never (0-10%)': 0.0,
            'Seldom (11-35%)': 0.2
        }
        
        # Reverse scored items (negatively worded questions)
        self.reverse_items = {
            'I complete tasks I am not passionate about',
            'I procrastinate',
            'I struggle making decisions',
            'I need to learn more to move forward',
            'I am discouraged by failure',
            'I give up when something is challenging',
            'I get annoyed if I don\'t come up with an idea',
            'I follow traditions',
            'I view obstacles as blockers',
            'I am resistant to change after experiencing a setback',
            'Failure makes me want to stop trying',
            'I want others to know what I did',
            'I take credit for the accomplishments of my team',
            'I want to avoid conflict',
            'I act without thinking',
            'I am influenced',
            'I use people as a means to an end',
            'I am easily distracted',
            'Relationships are transactional'
        }
    
    def process_raw_data(self, csv_path: str) -> Dict[str, Any]:
        """
        Process raw CSV data through complete pipeline
        
        Args:
            csv_path: Path to CSV file with assessment responses
            
        Returns:
            Dictionary containing processed data and trait scores
        """
        try:
            # Step 1: Load raw data
            raw_data = self._load_raw_data(csv_path)
            logger.info(f"Loaded {len(raw_data)} rows from {csv_path}")
            
            # Step 2: Map responses to numeric values
            mapped_data = self._map_responses(raw_data)
            logger.info("Response mapping completed")
            
            # Step 3: Calculate Rasch measures
            rasch_data = self._calculate_rasch_measures(mapped_data)
            logger.info("Rasch measures calculated")
            
            return {
                'raw_data': raw_data,
                'mapped_data': mapped_data,
                'rasch_data': rasch_data,
                'person_count': len(raw_data)
            }
            
        except Exception as e:
            logger.error(f"Error processing raw data: {e}")
            raise
    
    def _load_raw_data(self, csv_path: str) -> pd.DataFrame:
        """Load raw CSV data"""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def _map_responses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map text responses to numeric values"""
        mapped_df = df.copy()
        
        # Map Likert scale responses
        for col in df.columns:
            if df[col].dtype == 'object':
                mapped_df[col] = df[col].map(self.response_mapping).fillna(df[col])
        
        return mapped_df
    
    def _calculate_rasch_measures(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate Rasch measures using genuine RaschPy RSM analysis
        
        Args:
            df: DataFrame with mapped numeric responses (0.0-1.0 float scale)
            
        Returns:
            Dictionary containing:
            - item_difficulties: Dict mapping item names to difficulty estimates
            - person_abilities: Dict mapping person IDs to ability estimates (logit scale)
            - fit_statistics: Dict with fit statistics
            - person_measures: Legacy format for backward compatibility
        """
        logger.info("Calculating Rasch measures using RaschPy RSM...")
        
        # Identify assessment columns (exclude metadata)
        assessment_columns = self._identify_assessment_columns(df)
        
        if not assessment_columns:
            logger.warning("No assessment columns identified, using fallback method")
            return self._fallback_rasch_measures(df)
        
        # Step 1: Convert float responses to integer scores (0-4)
        if ResponseConverter is None:
            logger.warning("ResponseConverter not available, using fallback")
            return self._fallback_rasch_measures(df)
        
        response_converter = ResponseConverter(reverse_items=self.reverse_items)
        integer_df = response_converter.convert_to_rasch_integers(
            df, 
            assessment_columns, 
            reverse_items=self.reverse_items
        )
        
        # Step 2: Prepare data for RaschPy (items as rows, persons as columns)
        if RaschPyProcessor is None:
            logger.warning("RaschPyProcessor not available, using fallback")
            return self._fallback_rasch_measures(df)
        
        rasch_processor = RaschPyProcessor(max_score=4)
        prepared_data, person_ids = rasch_processor.prepare_data_for_rasch(integer_df, assessment_columns)
        
        # Step 3: Run RSM analysis
        rasch_results = rasch_processor.run_rsm_analysis(
            prepared_data,
            item_names=assessment_columns,
            person_ids=person_ids
        )
        
        # Step 4: Create legacy format for backward compatibility
        person_measures = {}
        for person_idx in range(len(df)):
            person_id = f"person_{person_idx}"
            person_ability = rasch_results['person_abilities'].get(person_id, 0.0)
            
            # Create item-level measures using person ability and item difficulties
            person_item_measures = {}
            for item_name in assessment_columns:
                item_difficulty = rasch_results['item_difficulties'].get(item_name, 0.0)
                # Rasch measure = person ability - item difficulty
                measure = person_ability - item_difficulty
                person_item_measures[item_name] = measure
            
            person_measures[person_id] = person_item_measures
        
        # Return structured results
        return {
            'item_difficulties': rasch_results['item_difficulties'],
            'person_abilities': rasch_results['person_abilities'],
            'fit_statistics': rasch_results.get('fit_statistics', {}),
            'person_measures': person_measures,  # Legacy format
            'rasch_processor': rasch_processor,  # Keep processor for later use
            'assessment_columns': assessment_columns
        }
    
    def _identify_assessment_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Identify columns containing assessment responses
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            List of assessment column names
        """
        assessment_columns = []
        
        # Skip metadata columns
        skip_columns = {
            'Please enter your prolific ID', 
            'In what country do you currently reside?',
            'Are you interested in entrepreneurship?', 
            'Thanks in advance for confirming your email address.',
            'Select the statement that resonates with you the most.',
            'Response Type', 
            'Start Date (UTC)', 
            'Submit Date (UTC)', 
            'Network ID', 
            'Tags', 
            'Ending',
            'First name',
            'Last name',
            'Email',
            'email'
        }
        
        for col in df.columns:
            # Skip known metadata columns
            if col in skip_columns:
                continue
            
            # Check if column contains numeric responses (assessment data)
            if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                # Check if values are in expected range (0.0-1.0 or 0-4)
                sample_values = df[col].dropna()
                if len(sample_values) > 0:
                    min_val = sample_values.min()
                    max_val = sample_values.max()
                    if 0 <= min_val <= max_val <= 4:
                        assessment_columns.append(col)
        
        logger.info(f"Identified {len(assessment_columns)} assessment columns")
        return assessment_columns
    
    def _fallback_rasch_measures(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Fallback method when RaschPy is not available
        Uses simplified Rasch measures (legacy implementation)
        """
        logger.warning("Using fallback Rasch measures calculation")
        rasch_data = {}
        
        for person_idx in range(len(df)):
            person_id = f"person_{person_idx}"
            person_measures = {}
            
            # Get person's responses (excluding metadata columns)
            person_responses = df.iloc[person_idx]
            
            for col in df.columns:
                if col in self.response_mapping.values() or isinstance(person_responses[col], (int, float)):
                    continue
                    
                response_value = person_responses[col]
                
                if isinstance(response_value, (int, float)) and not pd.isna(response_value):
                    # Convert to Rasch measure
                    if response_value >= 0.9:
                        person_ability = 2.0
                    elif response_value >= 0.7:
                        person_ability = 1.5
                    elif response_value >= 0.5:
                        person_ability = 1.0
                    elif response_value >= 0.2:
                        person_ability = 0.5
                    else:
                        person_ability = 0.0
                    
                    # Add item difficulty and random variation
                    item_difficulty = np.random.uniform(-1.0, 1.0)
                    noise = np.random.normal(0, 0.1)
                    
                    measure = person_ability + noise - item_difficulty
                    
                    # Apply reverse scoring if needed
                    if col in self.reverse_items:
                        measure = -measure
                    
                    person_measures[col] = measure
            
            rasch_data[person_id] = person_measures
        
        return {
            'item_difficulties': {},
            'person_abilities': {},
            'fit_statistics': {},
            'person_measures': rasch_data,
            'rasch_processor': None,
            'assessment_columns': []
        }
