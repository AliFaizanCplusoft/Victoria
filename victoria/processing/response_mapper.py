"""
Response Mapper - Convert Likert text responses to numeric values
Step 2 of the Victoria Project pipeline
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
import re

logger = logging.getLogger(__name__)

class ResponseMapper:
    """
    Maps Likert scale text responses to numeric values
    Handles the conversion from text like 'Always (91-100%)' to numeric values
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define Likert scale mappings
        self.likert_mappings = {
            # Standard Likert responses
            'Always (91-100%)': 1.0,
            'Often (66-90%)': 0.7,
            'Sometimes (36-65%)': 0.5,
            'Seldom (11-35%)': 0.2,
            'Never (0-10%)': 0.0,
            
            # Alternative patterns
            'Always': 1.0,
            'Often': 0.7,
            'Sometimes': 0.5,
            'Seldom': 0.2,
            'Never': 0.0,
            
            # Numeric responses (already processed)
            '5': 1.0,
            '4': 0.7,
            '3': 0.5,
            '2': 0.2,
            '1': 0.0,
        }
        
        # Question columns that contain assessment responses
        # These will be detected automatically
        self.assessment_columns = []
        
    def detect_assessment_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Automatically detect which columns contain assessment responses
        Based on the presence of Likert scale text
        """
        assessment_cols = []
        
        # Skip metadata columns
        skip_columns = {
            'Please enter your prolific ID', 'In what country do you currently reside?',
            'Are you interested in entrepreneurship?', 'Thanks in advance for confirming your email address.',
            'Select the statement that resonates with you the most.',
            'Response Type', 'Start Date (UTC)', 'Submit Date (UTC)', 'Network ID', 'Tags', 'Ending'
        }
        
        # Also skip enrichment columns
        skip_patterns = ['enrich_', 'Stage Date']
        
        for col in df.columns:
            # Skip known metadata columns
            if col in skip_columns:
                continue
                
            # Skip enrichment columns
            if any(pattern in col for pattern in skip_patterns):
                continue
            
            # Check if column contains Likert responses
            sample_values = df[col].dropna().astype(str).head(10)
            if any('(' in str(val) and '%' in str(val) for val in sample_values):
                assessment_cols.append(col)
                
        self.assessment_columns = assessment_cols
        self.logger.info(f"Detected {len(assessment_cols)} assessment columns")
        
        return assessment_cols
    
    def map_response_to_numeric(self, response: Union[str, float, int]) -> float:
        """
        Convert a single response to numeric value
        """
        if pd.isna(response):
            return np.nan
            
        response_str = str(response).strip()
        
        # Direct mapping
        if response_str in self.likert_mappings:
            return self.likert_mappings[response_str]
        
        # Try to extract numeric value if already numeric
        try:
            numeric_val = float(response_str)
            if 0 <= numeric_val <= 5:
                # Assume 5-point scale, normalize to 0-1
                return numeric_val / 5.0
            elif 0 <= numeric_val <= 1:
                # Already normalized
                return numeric_val
        except ValueError:
            pass
        
        # Pattern matching for percentage ranges
        percentage_pattern = r'\((\d+)-(\d+)%\)'
        match = re.search(percentage_pattern, response_str)
        if match:
            start_pct = int(match.group(1))
            end_pct = int(match.group(2))
            avg_pct = (start_pct + end_pct) / 2
            return avg_pct / 100.0
        
        # Fallback: try to find keywords
        response_lower = response_str.lower()
        if 'always' in response_lower:
            return 1.0
        elif 'often' in response_lower:
            return 0.7
        elif 'sometimes' in response_lower:
            return 0.5
        elif 'seldom' in response_lower or 'rarely' in response_lower:
            return 0.2
        elif 'never' in response_lower:
            return 0.0
        
        # If all else fails, return NaN
        self.logger.warning(f"Could not map response: '{response_str}'")
        return np.nan
    
    def process_responses(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process entire DataFrame, converting Likert responses to numeric
        Returns DataFrame with numeric responses ready for RaschPy processing
        """
        self.logger.info("Starting response mapping process...")
        
        # Make a copy to avoid modifying original
        processed_df = df.copy()
        
        # Auto-detect assessment columns if not set
        if not self.assessment_columns:
            self.detect_assessment_columns(processed_df)
        
        # Convert each assessment column
        conversion_stats = {}
        
        for col in self.assessment_columns:
            if col in processed_df.columns:
                original_values = processed_df[col].copy()
                
                # Apply mapping
                processed_df[col] = original_values.apply(self.map_response_to_numeric)
                
                # Track conversion statistics
                non_null_original = original_values.notna().sum()
                non_null_converted = processed_df[col].notna().sum()
                conversion_rate = non_null_converted / non_null_original if non_null_original > 0 else 0
                
                conversion_stats[col] = {
                    'original_count': non_null_original,
                    'converted_count': non_null_converted,
                    'conversion_rate': conversion_rate
                }
                
                if conversion_rate < 0.8:
                    self.logger.warning(f"Low conversion rate for {col}: {conversion_rate:.2%}")
        
        # Log summary
        total_responses = sum(stats['original_count'] for stats in conversion_stats.values())
        total_converted = sum(stats['converted_count'] for stats in conversion_stats.values())
        overall_rate = total_converted / total_responses if total_responses > 0 else 0
        
        self.logger.info(f"Response mapping completed:")
        self.logger.info(f"  - {len(self.assessment_columns)} assessment columns processed")
        self.logger.info(f"  - {total_responses} total responses")
        self.logger.info(f"  - {total_converted} successfully converted ({overall_rate:.2%})")
        
        return processed_df
    
    def get_conversion_summary(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary of the conversion process
        """
        summary = {
            'assessment_columns': len(self.assessment_columns),
            'total_columns': len(original_df.columns),
            'sample_mappings': {},
            'likert_patterns_found': []
        }
        
        # Show sample mappings
        for col in self.assessment_columns[:3]:  # First 3 columns
            if col in original_df.columns:
                sample_original = original_df[col].dropna().iloc[:3].tolist()
                sample_converted = processed_df[col].dropna().iloc[:3].tolist()
                summary['sample_mappings'][col] = list(zip(sample_original, sample_converted))
        
        # Find unique Likert patterns
        all_responses = []
        for col in self.assessment_columns:
            if col in original_df.columns:
                all_responses.extend(original_df[col].dropna().astype(str).unique())
        
        likert_patterns = [resp for resp in set(all_responses) if '(' in resp and '%' in resp]
        summary['likert_patterns_found'] = sorted(likert_patterns)[:10]  # Top 10
        
        return summary