"""
Comprehensive Data Processor - Complete pipeline orchestrator
Coordinates all steps of the Victoria Project data processing flow
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from pathlib import Path

from .response_mapper import ResponseMapper
from .rasch_processor import RaschPyProcessor
from victoria.config.settings import config

logger = logging.getLogger(__name__)

class ComprehensiveDataProcessor:
    """
    Orchestrates the complete data processing pipeline:
    1. Raw CSV input (Likert responses)
    2. Response mapping (text -> numeric)
    3. RaschPy processing (numeric -> measures)
    4. Output ready for trait scoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.response_mapper = ResponseMapper()
        self.rasch_processor = RaschPyProcessor()
        
        # Pipeline state
        self.raw_data = None
        self.mapped_data = None
        self.processed_data = None
        self.processing_summary = {}
    
    def load_raw_data(self, file_path: str) -> pd.DataFrame:
        """
        Load raw CSV data with Likert text responses
        Step 1: Raw Data Input
        """
        self.logger.info(f"Loading raw data from: {file_path}")
        
        try:
            # Load CSV
            df = pd.read_csv(file_path)
            
            self.logger.info(f"Raw data loaded:")
            self.logger.info(f"  - Shape: {df.shape}")
            self.logger.info(f"  - Columns: {len(df.columns)}")
            
            # Store raw data
            self.raw_data = df
            
            # Update processing summary
            self.processing_summary['step_1_raw_input'] = {
                'file_path': file_path,
                'shape': df.shape,
                'columns_count': len(df.columns),
                'rows_count': len(df)
            }
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading raw data: {e}")
            raise
    
    def map_responses(self) -> pd.DataFrame:
        """
        Convert Likert text responses to numeric values
        Step 2: Response Mapping
        """
        if self.raw_data is None:
            raise ValueError("No raw data loaded. Call load_raw_data() first.")
        
        self.logger.info("Starting response mapping...")
        
        # Process responses
        self.mapped_data = self.response_mapper.process_responses(self.raw_data)
        
        # Get conversion summary
        conversion_summary = self.response_mapper.get_conversion_summary(
            self.raw_data, self.mapped_data
        )
        
        # Update processing summary
        self.processing_summary['step_2_response_mapping'] = conversion_summary
        
        return self.mapped_data
    
    def apply_rasch_processing(self) -> pd.DataFrame:
        """
        Apply RaschPy psychometric scaling
        Step 3: RaschPy Processing
        """
        if self.mapped_data is None:
            raise ValueError("No mapped data available. Call map_responses() first.")
        
        self.logger.info("Starting RaschPy processing...")
        
        # Get assessment columns from response mapper
        assessment_columns = self.response_mapper.assessment_columns
        
        # Apply Rasch processing
        self.processed_data = self.rasch_processor.process_to_measures(
            self.mapped_data, assessment_columns
        )
        
        # Get processing summary
        rasch_summary = self.rasch_processor.get_processing_summary(
            self.mapped_data, self.processed_data, assessment_columns
        )
        
        # Update processing summary
        self.processing_summary['step_3_rasch_processing'] = rasch_summary
        
        return self.processed_data
    
    def process_complete_pipeline(self, file_path: str) -> pd.DataFrame:
        """
        Run the complete pipeline from raw CSV to processed measures
        """
        self.logger.info("Starting complete data processing pipeline...")
        
        try:
            # Step 1: Load raw data
            self.load_raw_data(file_path)
            
            # Step 2: Map responses
            self.map_responses()
            
            # Step 3: Apply RaschPy processing
            self.apply_rasch_processing()
            
            self.logger.info("Complete pipeline processing successful!")
            
            return self.processed_data
            
        except Exception as e:
            self.logger.error(f"Pipeline processing failed: {e}")
            raise
    
    def save_processed_data(self, output_path: Optional[str] = None) -> str:
        """
        Save processed data to file
        """
        if self.processed_data is None:
            raise ValueError("No processed data to save. Run pipeline first.")
        
        if output_path is None:
            output_path = config.get_file_path("processed_data.csv")
        
        self.processed_data.to_csv(output_path, index=False)
        self.logger.info(f"Processed data saved to: {output_path}")
        
        return output_path
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of the entire pipeline
        """
        summary = {
            'pipeline_status': 'complete' if self.processed_data is not None else 'incomplete',
            'steps_completed': len(self.processing_summary),
            'processing_details': self.processing_summary,
        }
        
        # Add data flow summary
        if self.raw_data is not None:
            summary['data_flow'] = {
                'raw_shape': self.raw_data.shape,
                'mapped_shape': self.mapped_data.shape if self.mapped_data is not None else None,
                'processed_shape': self.processed_data.shape if self.processed_data is not None else None,
            }
        
        # Add sample transformation
        if (self.raw_data is not None and 
            self.processed_data is not None and 
            self.response_mapper.assessment_columns):
            
            sample_col = self.response_mapper.assessment_columns[0]
            if sample_col in self.raw_data.columns and sample_col in self.processed_data.columns:
                # Get first non-null values
                raw_sample = self.raw_data[sample_col].dropna().iloc[0] if not self.raw_data[sample_col].dropna().empty else None
                processed_sample = self.processed_data[sample_col].dropna().iloc[0] if not self.processed_data[sample_col].dropna().empty else None
                
                summary['sample_transformation'] = {
                    'column': sample_col,
                    'raw_value': raw_sample,
                    'processed_value': processed_sample
                }
        
        return summary
    
    def prepare_for_trait_scoring(self) -> Tuple[pd.DataFrame, str]:
        """
        Prepare processed data for trait scoring
        Returns the data in format expected by TraitScorer
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Run pipeline first.")
        
        # The TraitScorer expects tab-separated data with 'Item' column
        # We need to transpose our data so items are rows and persons are columns
        
        assessment_columns = self.response_mapper.assessment_columns
        
        # Get only assessment data
        assessment_data = self.processed_data[assessment_columns].copy()
        
        # Transpose: items as rows, persons as columns
        transposed = assessment_data.T
        
        # Add Item column (item names)
        transposed.insert(0, 'Item', transposed.index)
        
        # Reset index
        transposed.reset_index(drop=True, inplace=True)
        
        # Rename person columns
        person_columns = [f'Person_{i+1}' for i in range(len(transposed.columns) - 1)]
        transposed.columns = ['Item'] + person_columns
        
        # Save in format expected by TraitScorer
        output_path = config.get_file_path("processed_for_trait_scoring.txt")
        transposed.to_csv(output_path, sep='\t', index=False)
        
        self.logger.info(f"Data prepared for trait scoring: {output_path}")
        self.logger.info(f"Format: {transposed.shape} (items × persons)")
        
        return transposed, output_path
    
    def validate_pipeline_flow(self) -> Dict[str, bool]:
        """
        Validate that the described pipeline flow is working correctly
        """
        validation = {
            'step_1_raw_csv_load': self.raw_data is not None,
            'step_2_likert_to_numeric': False,
            'step_3_rasch_processing': False,
            'step_4_ready_for_traits': False,
            'overall_pipeline': False
        }
        
        # Check Step 2: Likert conversion
        if (self.raw_data is not None and self.mapped_data is not None):
            # Check if we have actual Likert text that was converted
            assessment_cols = self.response_mapper.assessment_columns
            if assessment_cols:
                sample_col = assessment_cols[0]
                raw_sample = str(self.raw_data[sample_col].dropna().iloc[0])
                if '(' in raw_sample and '%' in raw_sample:
                    validation['step_2_likert_to_numeric'] = True
        
        # Check Step 3: Rasch processing
        if (self.mapped_data is not None and self.processed_data is not None):
            # Check if values changed (indicating processing occurred)
            assessment_cols = self.response_mapper.assessment_columns
            if assessment_cols:
                sample_col = assessment_cols[0]
                mapped_mean = self.mapped_data[sample_col].mean()
                processed_mean = self.processed_data[sample_col].mean()
                if abs(mapped_mean - processed_mean) > 0.1:  # Significant change
                    validation['step_3_rasch_processing'] = True
        
        # Check Step 4: Ready for trait scoring
        try:
            if self.processed_data is not None:
                transposed, _ = self.prepare_for_trait_scoring()
                validation['step_4_ready_for_traits'] = True
        except:
            pass
        
        # Overall pipeline
        validation['overall_pipeline'] = all(validation.values())
        
        return validation