"""
Response Converter - Convert Likert responses to integer scores for RaschPy
Converts float scores (0.0-1.0) to integer scores (0-4) for Rasch analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)


class ResponseConverter:
    """
    Converts Likert scale responses to integer scores suitable for RaschPy RSM
    Handles reverse-scored items and standardizes response mapping
    """
    
    def __init__(self, reverse_items: Set[str] = None):
        """
        Initialize response converter
        
        Args:
            reverse_items: Set of question texts that are reverse-scored
        """
        self.logger = logging.getLogger(__name__)
        self.reverse_items = reverse_items or set()
        
        # Standardized mapping: float (0.0-1.0) to integer (0-4)
        # Never (0-10%) → 0.0 → 0
        # Seldom (11-35%) → 0.2 → 1
        # Sometimes (36-65%) → 0.5 → 2
        # Often (66-90%) → 0.8 → 3 (standardized, was inconsistent 0.7/0.8)
        # Always (91-100%) → 1.0 → 4
        self.float_to_int_mapping = {
            0.0: 0,   # Never
            0.2: 1,   # Seldom
            0.5: 2,   # Sometimes
            0.7: 3,   # Often (legacy)
            0.8: 3,   # Often (standardized)
            1.0: 4    # Always
        }
    
    def convert_float_to_integer(self, float_value: float) -> int:
        """
        Convert float score (0.0-1.0) to integer score (0-4)
        
        Args:
            float_value: Float score between 0.0 and 1.0
            
        Returns:
            Integer score between 0 and 4
        """
        if pd.isna(float_value):
            return np.nan
        
        # Round to nearest mapped value
        if float_value in self.float_to_int_mapping:
            return self.float_to_int_mapping[float_value]
        
        # Handle values between mapped points
        if float_value < 0.1:
            return 0  # Never
        elif float_value < 0.35:
            return 1  # Seldom
        elif float_value < 0.65:
            return 2  # Sometimes
        elif float_value < 0.9:
            return 3  # Often
        else:
            return 4  # Always
    
    def reverse_score(self, integer_score: int) -> int:
        """
        Reverse score an integer (0-4 scale)
        Inverts: 0↔4, 1↔3, 2 stays 2
        
        Args:
            integer_score: Integer score between 0 and 4
            
        Returns:
            Reversed integer score
        """
        if pd.isna(integer_score):
            return np.nan
        
        # Reverse mapping: 0→4, 1→3, 2→2, 3→1, 4→0
        reverse_map = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0}
        return reverse_map.get(int(integer_score), integer_score)
    
    def convert_to_rasch_integers(
        self, 
        df: pd.DataFrame, 
        assessment_columns: List[str],
        reverse_items: Set[str] = None
    ) -> pd.DataFrame:
        """
        Convert DataFrame with float responses to integer scores for RaschPy
        
        Args:
            df: DataFrame with float responses (0.0-1.0)
            assessment_columns: List of column names containing assessment responses
            reverse_items: Optional set of reverse-scored items (overrides instance default)
            
        Returns:
            DataFrame with integer responses (0-4)
        """
        self.logger.info("Converting float responses to integer scores for RaschPy...")
        
        # Use provided reverse_items or instance default
        reverse_set = reverse_items if reverse_items is not None else self.reverse_items
        
        # Make a copy to avoid modifying original
        integer_df = df.copy()
        
        converted_count = 0
        reverse_count = 0
        
        for col in assessment_columns:
            if col not in integer_df.columns:
                continue
            
            # Convert float to integer
            integer_df[col] = integer_df[col].apply(self.convert_float_to_integer)
            converted_count += 1
            
            # Apply reverse scoring if needed
            if col in reverse_set:
                integer_df[col] = integer_df[col].apply(self.reverse_score)
                reverse_count += 1
                self.logger.debug(f"Applied reverse scoring to: {col}")
        
        self.logger.info(f"Response conversion completed:")
        self.logger.info(f"  - {converted_count} columns converted to integers")
        self.logger.info(f"  - {reverse_count} columns reverse-scored")
        self.logger.info(f"  - Score range: {integer_df[assessment_columns].min().min()} to {integer_df[assessment_columns].max().max()}")
        
        return integer_df
    
    def get_conversion_stats(
        self, 
        original_df: pd.DataFrame, 
        converted_df: pd.DataFrame,
        assessment_columns: List[str]
    ) -> Dict[str, any]:
        """
        Get statistics about the conversion process
        
        Args:
            original_df: Original DataFrame with float responses
            converted_df: Converted DataFrame with integer responses
            assessment_columns: List of assessment column names
            
        Returns:
            Dictionary with conversion statistics
        """
        stats = {
            'columns_converted': len(assessment_columns),
            'score_distribution': {},
            'sample_conversions': {}
        }
        
        # Calculate score distribution
        all_scores = []
        for col in assessment_columns:
            if col in converted_df.columns:
                scores = converted_df[col].dropna().tolist()
                all_scores.extend(scores)
        
        if all_scores:
            unique_scores, counts = np.unique(all_scores, return_counts=True)
            stats['score_distribution'] = {
                int(score): int(count) 
                for score, count in zip(unique_scores, counts)
            }
        
        # Sample conversions for first 3 columns
        for col in assessment_columns[:3]:
            if col in original_df.columns and col in converted_df.columns:
                sample_original = original_df[col].dropna().head(5).tolist()
                sample_converted = converted_df[col].dropna().head(5).tolist()
                stats['sample_conversions'][col] = list(zip(sample_original, sample_converted))
        
        return stats
