"""
Data processing helpers for Victoria Project
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Helper class for data processing operations"""
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess dataframe"""
        try:
            # Remove empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            # Reset index
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning dataframe: {e}")
            return df
    
    @staticmethod
    def validate_response_data(df: pd.DataFrame) -> bool:
        """Validate response data format"""
        try:
            # Check if dataframe is not empty
            if df.empty:
                return False
            
            # Check if there's at least one data column besides 'Item'
            if len(df.columns) < 2:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return False
    
    @staticmethod
    def normalize_scores(scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range"""
        try:
            if not scores:
                return []
            
            min_score = min(scores)
            max_score = max(scores)
            
            if max_score == min_score:
                return [0.5] * len(scores)
            
            return [(score - min_score) / (max_score - min_score) for score in scores]
            
        except Exception as e:
            logger.error(f"Error normalizing scores: {e}")
            return scores