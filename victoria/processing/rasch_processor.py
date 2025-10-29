"""
RaschPy Processor - Apply psychometric scaling to numeric responses
Step 3 of the Victoria Project pipeline
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class RaschPyProcessor:
    """
    Processes numeric response data using Rasch measurement principles
    Converts raw numeric responses to psychometric measures
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.item_difficulties = {}
        self.person_abilities = {}
        
        # Define item difficulty estimates (can be calibrated with real data)
        # These are estimates - in production, you'd calibrate with RaschPy
        self.default_difficulties = {
            # Risk Taking items (generally easier to endorse)
            'I enjoy new challenges': -0.5,
            'I am adventurous': -0.3,
            'I am comfortable making decisions in uncertain environments': 0.2,
            
            # Innovation items 
            'I come up with good ideas': -0.2,
            'I am driven by my passion to innovate': 0.1,
            'I communicate my ideas': -0.1,
            
            # Difficult items (harder to strongly endorse)
            'I pursue perfection': 0.8,  # Reverse scored
            'I procrastinate': 0.7,     # Reverse scored
            'I give up when something is challenging': 1.2,  # Reverse scored
        }
    
    def _calculate_rasch_measure(self, response_value: float, item_difficulty: float = 0.0) -> float:
        """
        Convert response value to Rasch measure (logit scale)
        This is a simplified version - full RaschPy would be more sophisticated
        """
        if pd.isna(response_value):
            return np.nan
        
        # Convert response to person ability estimate
        if response_value >= 0.9:      # Always (91-100%)
            person_ability = 2.0
        elif response_value >= 0.7:    # Often (66-90%) 
            person_ability = 1.5
        elif response_value >= 0.5:    # Sometimes (36-65%)
            person_ability = 1.0
        elif response_value >= 0.2:    # Seldom (11-35%)
            person_ability = 0.5
        else:                          # Never (0-10%)
            person_ability = 0.0
        
        # Add some realistic variation
        noise = np.random.normal(0, 0.1)  # Small amount of measurement error
        
        # Rasch measure = person ability - item difficulty
        measure = person_ability + noise - item_difficulty
        
        return measure
    
    def estimate_item_difficulties(self, df: pd.DataFrame, assessment_columns: List[str]) -> Dict[str, float]:
        """
        Estimate item difficulties from the data
        In a full implementation, this would use proper Rasch calibration
        """
        difficulties = {}
        
        for col in assessment_columns:
            if col in df.columns:
                # Simple difficulty estimate: higher average response = easier item
                mean_response = df[col].mean()
                if pd.notna(mean_response):
                    # Convert mean response to difficulty (inverse relationship)
                    difficulty = 1.0 - mean_response
                    difficulties[col] = difficulty
                else:
                    difficulties[col] = 0.0
        
        self.item_difficulties = difficulties
        return difficulties
    
    def process_to_measures(self, df: pd.DataFrame, assessment_columns: List[str]) -> pd.DataFrame:
        """
        Convert numeric responses to Rasch measures
        Returns DataFrame with measures ready for trait scoring
        """
        self.logger.info("Starting RaschPy processing...")
        
        # Make copy
        measures_df = df.copy()
        
        # Estimate item difficulties if not set
        if not self.item_difficulties:
            self.estimate_item_difficulties(measures_df, assessment_columns)
        
        # Process each assessment column
        processed_count = 0
        
        for col in assessment_columns:
            if col in measures_df.columns:
                item_difficulty = self.item_difficulties.get(col, 0.0)
                
                # Apply Rasch transformation to each response
                measures_df[col] = measures_df[col].apply(
                    lambda x: self._calculate_rasch_measure(x, item_difficulty)
                )
                
                processed_count += 1
        
        self.logger.info(f"RaschPy processing completed:")
        self.logger.info(f"  - {processed_count} items processed")
        self.logger.info(f"  - Measures range from {measures_df[assessment_columns].min().min():.2f} to {measures_df[assessment_columns].max().max():.2f}")
        
        return measures_df
    
    def calculate_person_abilities(self, df: pd.DataFrame, assessment_columns: List[str]) -> Dict[str, float]:
        """
        Calculate overall person ability measures
        """
        person_abilities = {}
        
        # Assuming first column is person ID or index
        person_col = df.columns[0] if len(df.columns) > 0 else None
        
        for idx, row in df.iterrows():
            person_id = row[person_col] if person_col else f"Person_{idx}"
            
            # Calculate mean ability across all items
            measures = []
            for col in assessment_columns:
                if col in df.columns and pd.notna(row[col]):
                    measures.append(row[col])
            
            if measures:
                person_abilities[str(person_id)] = np.mean(measures)
            else:
                person_abilities[str(person_id)] = 0.0
        
        self.person_abilities = person_abilities
        return person_abilities
    
    def get_processing_summary(self, original_df: pd.DataFrame, measures_df: pd.DataFrame, 
                             assessment_columns: List[str]) -> Dict[str, Any]:
        """
        Get summary of RaschPy processing
        """
        summary = {
            'items_processed': len(assessment_columns),
            'persons_processed': len(measures_df),
            'item_difficulties': dict(list(self.item_difficulties.items())[:10]),  # First 10
            'measure_range': {
                'min': float(measures_df[assessment_columns].min().min()),
                'max': float(measures_df[assessment_columns].max().max()),
                'mean': float(measures_df[assessment_columns].mean().mean())
            },
            'processing_stats': {}
        }
        
        # Add processing stats for each item
        for col in assessment_columns[:5]:  # First 5 items
            if col in measures_df.columns:
                original_mean = original_df[col].mean() if col in original_df.columns else 0
                measure_mean = measures_df[col].mean()
                
                summary['processing_stats'][col] = {
                    'original_mean': float(original_mean),
                    'measure_mean': float(measure_mean),
                    'difficulty': float(self.item_difficulties.get(col, 0))
                }
        
        return summary
    
    def simulate_full_raschpy(self, df: pd.DataFrame, assessment_columns: List[str]) -> pd.DataFrame:
        """
        Simulate what full RaschPy processing would look like
        This creates more realistic psychometric measures
        """
        self.logger.info("Simulating full RaschPy analysis...")
        
        # This would normally involve:
        # 1. Item calibration
        # 2. Person measurement  
        # 3. Model fit assessment
        # 4. Reliability analysis
        
        # For simulation, we'll create measures that follow Rasch principles
        measures_df = df.copy()
        
        # Calibrate items (estimate difficulties)
        difficulties = {}
        for col in assessment_columns:
            if col in df.columns:
                # Items with higher endorsement rates are "easier"
                endorsement_rate = (df[col] > 0.5).mean()
                # Convert to logit difficulty
                if endorsement_rate > 0.99:
                    endorsement_rate = 0.99
                elif endorsement_rate < 0.01:
                    endorsement_rate = 0.01
                
                difficulty = np.log(endorsement_rate / (1 - endorsement_rate))
                difficulties[col] = difficulty
        
        self.item_difficulties = difficulties
        
        # Convert responses to measures
        for col in assessment_columns:
            if col in measures_df.columns:
                difficulty = difficulties.get(col, 0.0)
                
                # Apply more sophisticated Rasch transformation
                def rasch_transform(response):
                    if pd.isna(response):
                        return np.nan
                    
                    # Convert to probability of endorsement
                    prob = response
                    
                    # Convert to logit (person ability - item difficulty)
                    if prob >= 0.99:
                        prob = 0.99
                    elif prob <= 0.01:
                        prob = 0.01
                    
                    person_logit = np.log(prob / (1 - prob))
                    measure = person_logit + difficulty  # Add back item difficulty
                    
                    return measure
                
                measures_df[col] = measures_df[col].apply(rasch_transform)
        
        return measures_df












