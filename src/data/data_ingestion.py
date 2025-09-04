"""
Data Ingestion Module for Psychometric Assessment System

Handles CSV file ingestion, format detection, and initial data processing
for psychometric assessment responses.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path
import chardet
from io import StringIO
from dataclasses import dataclass

# Fix imports for your folder structure
try:
    from .item_mapper import ItemMapper
    from .data_validator import DataValidator, DatasetValidationSummary
except ImportError:
    try:
        from item_mapper import ItemMapper
        from data_validator import DataValidator, DatasetValidationSummary
    except ImportError:
        # Create fallback classes
        class ItemMapper:
            def __init__(self):
                self.constructs = {
                    'RT': 'Risk Taking',
                    'DA': 'Drive & Ambition',
                    'IO': 'Innovation Orientation',
                    'DM': 'Decision Making',
                    'RG': 'Resilience & Grit',
                    'SL': 'Servant Leadership',
                    'TB': 'Team Building',
                    'EI': 'Emotional Intelligence',
                    'A': 'Accountability',
                    'PS': 'Problem Solving',
                    'CT': 'Critical Thinking',
                    'F': 'Failure Response',
                    'AD': 'Adaptability',
                    'C': 'Conflict Management',
                    'N': 'Negotiation',
                    'RB': 'Relationship Building',
                    'IN': 'Influence',
                    'IIN': 'Interpersonal Intelligence'
                }
                self.item_construct_map = {}
                self.reverse_items = set()
            
            def get_all_constructs(self):
                return self.constructs
            
            def get_construct_for_item(self, item):
                return self.item_construct_map.get(item)
            
            def get_items_for_construct(self, construct):
                return [item for item, const in self.item_construct_map.items() if const == construct]
            
            def get_construct_name(self, construct_code):
                return self.constructs.get(construct_code, construct_code)
            
            def get_all_items(self):
                return list(self.item_construct_map.keys())
        
        class DataValidator:
            def __init__(self, item_mapper):
                self.item_mapper = item_mapper
            
            def validate_dataset(self, data):
                return type('ValidationSummary', (), {
                    'total_persons': data['Persons'].nunique() if 'Persons' in data.columns else 0,
                    'valid_persons': data['Persons'].nunique() if 'Persons' in data.columns else 0,
                    'invalid_persons': 0,
                    'overall_errors': [],
                    'overall_warnings': []
                })()
        
        DatasetValidationSummary = type('DatasetValidationSummary', (), {})


@dataclass
class IngestionResult:
    """Container for data ingestion results."""
    success: bool
    data: Optional[pd.DataFrame]
    validation_summary: Optional[DatasetValidationSummary]
    file_info: Dict[str, any]
    processing_log: List[str]
    errors: List[str]


class PsychometricDataProcessor:
    """
    Main data ingestion and processing class for psychometric assessments.
    
    Handles:
    - File format detection and reading
    - Data structure validation
    - Item mapping and construct assignment
    - Data quality assessment
    - Preprocessing for downstream analysis
    """
    
    def __init__(self, item_mapper: Optional[ItemMapper] = None,
                 validator: Optional[DataValidator] = None):
        """
        Initialize the data processor.
        
        Args:
            item_mapper: ItemMapper instance for construct mapping
            validator: DataValidator instance for quality checks
        """
        self.logger = logging.getLogger(__name__)
        self.item_mapper = item_mapper or ItemMapper()
        self.validator = validator or DataValidator(self.item_mapper)
        
        # Supported file formats
        self.supported_formats = ['.csv', '.tsv', '.txt']
        
        # Expected column names (flexible matching)
        self.expected_columns = {
            'measure': ['measure', 'rasch_measure', 'score', 'value'],
            'person_sequence': ['e1', 'person_seq', 'person_number'],
            'item_sequence': ['e2', 'item_seq', 'item_number'], 
            'person_id': ['persons', 'person_id', 'participant_id', 'user_id'],
            'item_id': ['assessment_items', 'item_id', 'question_id', 'item_name']
        }
        
        self.logger.info("PsychometricDataProcessor initialized")
    
    def process_file(self, filepath: Union[str, Path], 
                    encoding: Optional[str] = None,
                    delimiter: Optional[str] = None,
                    validate_data: bool = True) -> IngestionResult:
        """
        Process a psychometric assessment data file.
        
        Args:
            filepath: Path to the data file
            encoding: File encoding (auto-detected if None)
            delimiter: Column delimiter (auto-detected if None)
            validate_data: Whether to run data validation
            
        Returns:
            IngestionResult with processing details
        """
        filepath = Path(filepath)
        processing_log = []
        errors = []
        
        self.logger.info(f"Starting processing of file: {filepath}")
        processing_log.append(f"Processing file: {filepath.name}")
        
        # Validate file exists and format
        if not filepath.exists():
            error = f"File not found: {filepath}"
            errors.append(error)
            self.logger.error(error)
            return IngestionResult(
                success=False, data=None, validation_summary=None,
                file_info={}, processing_log=processing_log, errors=errors
            )
        
        if filepath.suffix.lower() not in self.supported_formats:
            error = f"Unsupported file format: {filepath.suffix}"
            errors.append(error)
            self.logger.error(error)
            return IngestionResult(
                success=False, data=None, validation_summary=None,
                file_info={}, processing_log=processing_log, errors=errors
            )
        
        # Get file info
        file_info = self._get_file_info(filepath)
        processing_log.append(f"File size: {file_info['size_mb']:.2f} MB")
        
        try:
            # Detect encoding if not provided
            if encoding is None:
                encoding = self._detect_encoding(filepath)
                processing_log.append(f"Detected encoding: {encoding}")
            
            # Detect delimiter if not provided
            if delimiter is None:
                delimiter = self._detect_delimiter(filepath, encoding)
                processing_log.append(f"Detected delimiter: '{delimiter}'")
            
            # Read the data
            data = self._read_data_file(filepath, encoding, delimiter)
            processing_log.append(f"Loaded {len(data)} rows, {len(data.columns)} columns")
            
            # Standardize column names
            data = self._standardize_columns(data)
            processing_log.append("Column names standardized")
            
            # Validate required columns are present
            missing_cols = self._check_required_columns(data)
            if missing_cols:
                error = f"Missing required columns: {missing_cols}"
                errors.append(error)
                self.logger.error(error)
                return IngestionResult(
                    success=False, data=None, validation_summary=None,
                    file_info=file_info, processing_log=processing_log, errors=errors
                )
            
            # Data type conversion and cleaning
            data = self._clean_and_convert_data(data)
            processing_log.append("Data types converted and cleaned")
            
            # Validate data if requested
            validation_summary = None
            if validate_data:
                validation_summary = self.validator.validate_dataset(data)
                processing_log.append(f"Validation: {validation_summary.valid_persons}/{validation_summary.total_persons} persons valid")
                
                if validation_summary.overall_errors:
                    errors.extend(validation_summary.overall_errors)
            
            # Success
            self.logger.info(f"Successfully processed {filepath.name}: {len(data)} records, {data['Persons'].nunique()} persons")
            
            return IngestionResult(
                success=True,
                data=data,
                validation_summary=validation_summary,
                file_info=file_info,
                processing_log=processing_log,
                errors=errors
            )
            
        except Exception as e:
            error = f"Error processing file: {str(e)}"
            errors.append(error)
            self.logger.error(error, exc_info=True)
            
            return IngestionResult(
                success=False, data=None, validation_summary=None,
                file_info=file_info, processing_log=processing_log, errors=errors
            )
    
    def _get_file_info(self, filepath: Path) -> Dict[str, any]:
        """Get basic file information."""
        stat = filepath.stat()
        return {
            'filename': filepath.name,
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified_time': stat.st_mtime,
            'extension': filepath.suffix.lower()
        }
    
    def _detect_encoding(self, filepath: Path) -> str:
        """Detect file encoding using chardet."""
        try:
            with open(filepath, 'rb') as f:
                # Read first 10KB for detection
                raw_data = f.read(10240)
            
            # Use chardet to detect encoding
            detected = chardet.detect(raw_data)
            encoding = detected['encoding']
            
            # Fallback to utf-8 if detection fails
            if encoding is None:
                encoding = 'utf-8'
            
            # Handle common encoding variations
            if encoding.lower() in ['ascii', 'us-ascii']:
                encoding = 'utf-8'
            
            return encoding
            
        except Exception as e:
            self.logger.warning(f"Could not detect encoding: {e}")
            return 'utf-8'

    def _detect_delimiter(self, filepath: Path, encoding: str) -> str:
        """Detect the delimiter used in the file."""
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                # Read first few lines to detect delimiter
                sample = f.read(1024)
                
            # Check for common delimiters
            delimiters = ['\t', ',', ';', '|']
            delimiter_counts = {}
            
            for delim in delimiters:
                delimiter_counts[delim] = sample.count(delim)
            
            # Return the most common delimiter
            best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
            
            # If tab is present, prefer it (common in psychometric data)
            if delimiter_counts['\t'] > 0:
                return '\t'
            
            return best_delimiter if delimiter_counts[best_delimiter] > 0 else ','
            
        except Exception as e:
            self.logger.warning(f"Could not detect delimiter, using tab: {e}")
            return '\t'  # Default to tab for psychometric data

    def _read_data_file(self, filepath: Path, encoding: str, delimiter: str) -> pd.DataFrame:
        """Read the data file with proper delimiter handling."""
        try:
            # Read the file with detected delimiter
            data = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)
            
            # If we still have issues with column separation, try common alternatives
            if len(data.columns) == 1 and '\t' in str(data.columns[0]):
                self.logger.info("Single column with tabs detected, trying tab delimiter")
                data = pd.read_csv(filepath, delimiter='\t', encoding=encoding)
                
            elif len(data.columns) == 1 and ',' in str(data.columns[0]):
                self.logger.info("Single column with commas detected, trying comma delimiter") 
                data = pd.read_csv(filepath, delimiter=',', encoding=encoding)
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error reading data file: {e}")
            raise

    def _standardize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to match expected format."""
        # Create a copy to avoid modifying original
        data = data.copy()
        
        # Create mapping from current columns to standard names
        column_mapping = {}
        
        for col in data.columns:
            col_lower = col.lower().strip()
            
            # Check against expected column patterns
            if any(expected in col_lower for expected in self.expected_columns['measure']):
                column_mapping[col] = 'Measure'
            elif any(expected in col_lower for expected in self.expected_columns['person_sequence']):
                column_mapping[col] = 'E1'
            elif any(expected in col_lower for expected in self.expected_columns['item_sequence']):
                column_mapping[col] = 'E2'
            elif any(expected in col_lower for expected in self.expected_columns['person_id']):
                column_mapping[col] = 'Persons'
            elif any(expected in col_lower for expected in self.expected_columns['item_id']):
                column_mapping[col] = 'Assessment_Items'
        
        # Apply the mapping
        data = data.rename(columns=column_mapping)
        
        # Log the column mapping
        self.logger.info(f"Column mapping applied: {column_mapping}")
        
        return data

    def _check_required_columns(self, data: pd.DataFrame) -> List[str]:
        """Check if required columns are present."""
        required_columns = ['Measure', 'Persons', 'Assessment_Items']
        missing_columns = []
        
        for col in required_columns:
            if col not in data.columns:
                missing_columns.append(col)
        
        return missing_columns

    def _clean_and_convert_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types."""
        data = data.copy()
        
        # Convert Measure to numeric if possible
        if 'Measure' in data.columns:
            data['Measure'] = pd.to_numeric(data['Measure'], errors='coerce')
        
        # Convert E1 and E2 to numeric if they exist
        for col in ['E1', 'E2']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Clean string columns
        string_cols = ['Persons', 'Assessment_Items']
        for col in string_cols:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip()
        
        # Remove rows with all NaN values
        data = data.dropna(how='all')
        
        # Additional validation for psychometric data
        data = self._validate_psychometric_data(data)
        
        return data
    
    def _validate_psychometric_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Additional validation specific to psychometric assessment data."""
        original_size = len(data)
        
        # Remove rows where person ID is missing
        if 'Persons' in data.columns:
            data = data.dropna(subset=['Persons'])
            self.logger.info(f"Removed {original_size - len(data)} rows with missing person IDs")
        
        # Remove rows where item ID is missing
        if 'Assessment_Items' in data.columns:
            data = data.dropna(subset=['Assessment_Items'])
        
        # Validate measure values are numeric and reasonable
        if 'Measure' in data.columns:
            # Remove obviously invalid measures
            initial_count = len(data)
            data = data[data['Measure'].notna()]
            data = data[data['Measure'].between(-10, 10)]  # Reasonable range for Rasch measures
            
            removed_count = initial_count - len(data)
            if removed_count > 0:
                self.logger.warning(f"Removed {removed_count} rows with invalid measures")
        
        return data
    
    def process_typeform_export(self, filepath: Union[str, Path], 
                               response_columns: List[str] = None,
                               participant_id_column: str = 'Response ID') -> IngestionResult:
        """
        Process a Typeform CSV export specifically.
        
        Args:
            filepath: Path to the Typeform CSV export
            response_columns: List of column names containing responses
            participant_id_column: Column name containing participant IDs
            
        Returns:
            IngestionResult with processed data
        """
        filepath = Path(filepath)
        processing_log = []
        errors = []
        
        self.logger.info(f"Processing Typeform export: {filepath}")
        processing_log.append(f"Processing Typeform export: {filepath.name}")
        
        try:
            # Read the Typeform CSV
            raw_data = pd.read_csv(filepath)
            processing_log.append(f"Loaded Typeform data: {len(raw_data)} responses, {len(raw_data.columns)} columns")
            
            # Transform to long format for psychometric analysis
            transformed_data = self._transform_typeform_to_long(
                raw_data, response_columns, participant_id_column
            )
            processing_log.append(f"Transformed to long format: {len(transformed_data)} records")
            
            # Apply standard processing
            final_data = self._standardize_columns(transformed_data)
            final_data = self._clean_and_convert_data(final_data)
            final_data = self._validate_psychometric_data(final_data)
            
            # Validate with the data validator
            validation_summary = self.validator.validate_dataset(final_data)
            processing_log.append(f"Validation complete: {validation_summary.valid_persons}/{validation_summary.total_persons} valid participants")
            
            return IngestionResult(
                success=True,
                data=final_data,
                validation_summary=validation_summary,
                file_info=self._get_file_info(filepath),
                processing_log=processing_log,
                errors=errors
            )
            
        except Exception as e:
            error = f"Error processing Typeform export: {str(e)}"
            errors.append(error)
            self.logger.error(error, exc_info=True)
            
            return IngestionResult(
                success=False, data=None, validation_summary=None,
                file_info=self._get_file_info(filepath), 
                processing_log=processing_log, errors=errors
            )
    
    def _transform_typeform_to_long(self, data: pd.DataFrame, 
                                   response_columns: List[str] = None,
                                   participant_id_column: str = 'Response ID') -> pd.DataFrame:
        """
        Transform Typeform wide format to long format for psychometric analysis.
        
        Args:
            data: Raw Typeform data in wide format
            response_columns: Columns containing item responses
            participant_id_column: Column containing participant IDs
            
        Returns:
            DataFrame in long format with columns: Persons, Assessment_Items, Measure
        """
        long_data = []
        
        # Auto-detect response columns if not provided
        if response_columns is None:
            # Look for columns that likely contain responses (numeric or Likert scale)
            response_columns = []
            for col in data.columns:
                if col != participant_id_column and data[col].dtype in ['int64', 'float64']:
                    response_columns.append(col)
                elif data[col].astype(str).str.match(r'^[1-7]$').any():  # Likert scale responses
                    response_columns.append(col)
        
        self.logger.info(f"Using {len(response_columns)} response columns for transformation")
        
        # Transform each row to multiple records
        for idx, row in data.iterrows():
            participant_id = row.get(participant_id_column, f"P_{idx:04d}")
            
            for item_col in response_columns:
                if pd.notna(row[item_col]):
                    # Convert response to numeric if needed
                    try:
                        measure = float(row[item_col])
                    except (ValueError, TypeError):
                        # Handle text responses (map to numeric if possible)
                        measure = self._map_text_response_to_numeric(row[item_col])
                        if measure is None:
                            continue
                    
                    long_data.append({
                        'Persons': str(participant_id),
                        'Assessment_Items': item_col,
                        'Measure': measure
                    })
        
        return pd.DataFrame(long_data)
    
    def _map_text_response_to_numeric(self, response) -> Optional[float]:
        """Map text responses to numeric values."""
        if pd.isna(response):
            return None
        
        response_str = str(response).lower().strip()
        
        # Victoria Project specific Likert scale mappings
        likert_mapping = {
            'never (0-10%)': 0,
            'seldom (11-35%)': 1,
            'sometimes (36-65%)': 2,
            'often (66-90%)': 3,
            'always (91-100%)': 4,
            'never': 0,
            'seldom': 1,
            'sometimes': 2,
            'often': 3,
            'always': 4,
            'strongly disagree': 0,
            'disagree': 1,
            'somewhat disagree': 1,
            'neutral': 2,
            'neither agree nor disagree': 2,
            'somewhat agree': 3,
            'agree': 3,
            'strongly agree': 4,
            'very low': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'very high': 4
        }
        
        return likert_mapping.get(response_str, None)
    
    def process_raw_survey_csv(self, filepath: Union[str, Path]) -> IngestionResult:
        """
        Process raw survey CSV with specific format for Victoria Project.
        
        Expected format:
        - Person IDs in "Please enter your prolific ID" column
        - 150+ assessment items as columns with Likert responses
        - Responses: "Never (0-10%)", "Seldom (11-35%)", "Sometimes (36-65%)", "Often (66-90%)", "Always (91-100%)"
        
        Args:
            filepath: Path to the raw survey CSV file
            
        Returns:
            IngestionResult with processed data in RaschPy format
        """
        filepath = Path(filepath)
        processing_log = []
        errors = []
        
        self.logger.info(f"Processing raw survey CSV: {filepath}")
        processing_log.append(f"Processing raw survey CSV: {filepath.name}")
        
        try:
            # Read the raw CSV
            raw_data = pd.read_csv(filepath)
            processing_log.append(f"Loaded raw survey data: {len(raw_data)} responses, {len(raw_data.columns)} columns")
            
            # Find the person ID column
            person_id_column = None
            for col in raw_data.columns:
                if 'prolific' in col.lower() or 'id' in col.lower():
                    person_id_column = col
                    break
            
            if person_id_column is None:
                # Use first column as person ID
                person_id_column = raw_data.columns[0]
                processing_log.append(f"Using first column as person ID: {person_id_column}")
            else:
                processing_log.append(f"Found person ID column: {person_id_column}")
            
            # Identify assessment item columns (exclude person ID and metadata)
            assessment_columns = []
            for col in raw_data.columns:
                if col != person_id_column and not any(meta in col.lower() for meta in ['timestamp', 'duration', 'consent', 'age', 'gender']):
                    assessment_columns.append(col)
            
            processing_log.append(f"Found {len(assessment_columns)} assessment item columns")
            
            # Transform to long format
            long_data = []
            
            for idx, row in raw_data.iterrows():
                person_id = str(row[person_id_column]).strip()
                
                # Skip if person ID is missing
                if pd.isna(person_id) or person_id == '' or person_id == 'nan':
                    continue
                
                for item_col in assessment_columns:
                    response = row[item_col]
                    
                    if pd.notna(response):
                        # Convert response to numeric
                        numeric_response = self._map_text_response_to_numeric(response)
                        
                        if numeric_response is not None:
                            long_data.append({
                                'Persons': person_id,
                                'Assessment_Items': item_col,
                                'Response': numeric_response
                            })
            
            # Create DataFrame
            transformed_data = pd.DataFrame(long_data)
            processing_log.append(f"Transformed to long format: {len(transformed_data)} response records")
            
            # Add sequence numbers for RaschPy format
            person_sequence = {person: idx + 1 for idx, person in enumerate(transformed_data['Persons'].unique())}
            item_sequence = {item: idx + 1 for idx, item in enumerate(transformed_data['Assessment_Items'].unique())}
            
            transformed_data['E1'] = transformed_data['Persons'].map(person_sequence)
            transformed_data['E2'] = transformed_data['Assessment_Items'].map(item_sequence)
            
            # For now, use raw response as measure (RaschPy will calculate proper measures)
            transformed_data['Measure'] = transformed_data['Response']
            
            # Select final columns in RaschPy format
            final_data = transformed_data[['Measure', 'E1', 'E2', 'Persons', 'Assessment_Items']].copy()
            
            # Validate the data
            validation_summary = self.validator.validate_dataset(final_data)
            processing_log.append(f"Validation complete: {validation_summary.valid_persons}/{validation_summary.total_persons} valid participants")
            
            # Success
            self.logger.info(f"Successfully processed raw survey CSV: {len(final_data)} records, {len(final_data['Persons'].unique())} persons, {len(final_data['Assessment_Items'].unique())} items")
            
            return IngestionResult(
                success=True,
                data=final_data,
                validation_summary=validation_summary,
                file_info=self._get_file_info(filepath),
                processing_log=processing_log,
                errors=errors
            )
            
        except Exception as e:
            error = f"Error processing raw survey CSV: {str(e)}"
            errors.append(error)
            self.logger.error(error, exc_info=True)
            
            return IngestionResult(
                success=False, data=None, validation_summary=None,
                file_info=self._get_file_info(filepath), 
                processing_log=processing_log, errors=errors
            )