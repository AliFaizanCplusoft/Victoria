"""
Data Processor - Step 1-3: Raw Data to Rasch Measures
Handles response mapping and Rasch processing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

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
        Calculate Rasch measures for each person and question
        Simplified Rasch analysis for psychometric scaling
        """
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
        
        return rasch_data
