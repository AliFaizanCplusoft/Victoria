"""
Validation utilities for file uploads and data processing
"""

import os
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from fastapi import UploadFile
import pandas as pd

from .exceptions import FileValidationError, DataValidationError, ResourceLimitError


class FileValidator:
    """Validator for uploaded files."""
    
    # Supported file types
    SUPPORTED_EXTENSIONS = {'.csv', '.txt'}
    SUPPORTED_MIME_TYPES = {
        'text/csv',
        'text/plain',
        'application/csv',
        'text/comma-separated-values'
    }
    
    # File size limits
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_TOTAL_SIZE = 200 * 1024 * 1024  # 200MB for batch uploads
    MAX_FILES_PER_BATCH = 50
    
    def __init__(self):
        """Initialize file validator."""
        pass
    
    def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate a single uploaded file.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Dictionary with validation results and metadata
            
        Raises:
            FileValidationError: If validation fails
        """
        if not file.filename:
            raise FileValidationError("File must have a filename")
        
        # Check file extension
        file_path = Path(file.filename)
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file type: {file_path.suffix}. "
                f"Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )
        
        # Check file size
        if file.size and file.size > self.MAX_FILE_SIZE:
            raise ResourceLimitError(
                f"File size ({file.size} bytes) exceeds maximum limit "
                f"({self.MAX_FILE_SIZE} bytes)"
            )
        
        # Check MIME type
        if file.content_type and file.content_type not in self.SUPPORTED_MIME_TYPES:
            raise FileValidationError(
                f"Unsupported MIME type: {file.content_type}. "
                f"Supported types: {', '.join(self.SUPPORTED_MIME_TYPES)}"
            )
        
        return {
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
            "extension": file_path.suffix.lower(),
            "is_valid": True
        }
    
    def validate_batch_files(self, files: List[UploadFile]) -> Dict[str, Any]:
        """
        Validate a batch of uploaded files.
        
        Args:
            files: List of uploaded file objects
            
        Returns:
            Dictionary with validation results and metadata
            
        Raises:
            FileValidationError: If validation fails
            ResourceLimitError: If resource limits are exceeded
        """
        if len(files) > self.MAX_FILES_PER_BATCH:
            raise ResourceLimitError(
                f"Too many files in batch ({len(files)}). "
                f"Maximum allowed: {self.MAX_FILES_PER_BATCH}"
            )
        
        total_size = 0
        file_metadata = []
        
        for file in files:
            metadata = self.validate_file(file)
            file_metadata.append(metadata)
            total_size += file.size or 0
        
        if total_size > self.MAX_TOTAL_SIZE:
            raise ResourceLimitError(
                f"Total file size ({total_size} bytes) exceeds maximum limit "
                f"({self.MAX_TOTAL_SIZE} bytes)"
            )
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "files": file_metadata,
            "is_valid": True
        }
    
    def validate_file_content(self, file_path: str) -> Dict[str, Any]:
        """
        Validate the content of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with content validation results
            
        Raises:
            FileValidationError: If content validation fails
        """
        if not os.path.exists(file_path):
            raise FileValidationError(f"File not found: {file_path}")
        
        try:
            # Try to read as CSV
            df = pd.read_csv(file_path, nrows=10)  # Read first 10 rows for validation
            
            if df.empty:
                raise DataValidationError("File is empty or contains no valid data")
            
            return {
                "file_path": file_path,
                "rows_sample": len(df),
                "columns": list(df.columns),
                "column_count": len(df.columns),
                "has_header": True,
                "is_valid": True
            }
            
        except pd.errors.EmptyDataError:
            raise DataValidationError("File is empty")
        except pd.errors.ParserError as e:
            raise DataValidationError(f"File parsing error: {str(e)}")
        except Exception as e:
            raise FileValidationError(f"Error reading file: {str(e)}")


class DataValidator:
    """Validator for psychometric data."""
    
    # Minimum requirements for psychometric data
    MIN_ROWS = 1
    MIN_COLUMNS = 5
    MIN_COMPLETION_RATE = 0.5
    
    def __init__(self):
        """Initialize data validator."""
        pass
    
    def validate_psychometric_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate psychometric assessment data.
        
        Args:
            df: DataFrame containing assessment data
            
        Returns:
            Dictionary with validation results
            
        Raises:
            DataValidationError: If validation fails
        """
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "summary": {}
        }
        
        # Check minimum rows
        if len(df) < self.MIN_ROWS:
            validation_results["errors"].append(
                f"Insufficient data: {len(df)} rows (minimum: {self.MIN_ROWS})"
            )
            validation_results["is_valid"] = False
        
        # Check minimum columns
        if len(df.columns) < self.MIN_COLUMNS:
            validation_results["errors"].append(
                f"Insufficient columns: {len(df.columns)} (minimum: {self.MIN_COLUMNS})"
            )
            validation_results["is_valid"] = False
        
        # Check for missing data
        missing_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if missing_percentage > 50:
            validation_results["warnings"].append(
                f"High percentage of missing data: {missing_percentage:.1f}%"
            )
        
        # Check data types
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) < 3:
            validation_results["warnings"].append(
                f"Few numeric columns detected: {len(numeric_columns)}"
            )
        
        # Summary statistics
        validation_results["summary"] = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": len(numeric_columns),
            "missing_percentage": missing_percentage,
            "column_names": list(df.columns)
        }
        
        return validation_results
    
    def validate_completion_rate(self, df: pd.DataFrame) -> float:
        """
        Calculate and validate completion rate.
        
        Args:
            df: DataFrame containing assessment data
            
        Returns:
            Completion rate (0-1)
            
        Raises:
            DataValidationError: If completion rate is too low
        """
        total_cells = len(df) * len(df.columns)
        completed_cells = total_cells - df.isnull().sum().sum()
        completion_rate = completed_cells / total_cells if total_cells > 0 else 0
        
        if completion_rate < self.MIN_COMPLETION_RATE:
            raise DataValidationError(
                f"Completion rate too low: {completion_rate:.2%} "
                f"(minimum: {self.MIN_COMPLETION_RATE:.2%})"
            )
        
        return completion_rate
    
    def validate_assessment_format(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that data follows expected assessment format.
        
        Args:
            df: DataFrame containing assessment data
            
        Returns:
            Dictionary with format validation results
        """
        format_results = {
            "is_valid": True,
            "format_type": "unknown",
            "issues": []
        }
        
        # Check for common assessment formats
        columns_lower = [col.lower() for col in df.columns]
        
        # Check for Typeform format
        if any('typeform' in col for col in columns_lower):
            format_results["format_type"] = "typeform"
        
        # Check for standard CSV format
        elif any(col.startswith('q') for col in columns_lower):
            format_results["format_type"] = "standard_csv"
        
        # Check for participant ID column
        id_columns = ['id', 'participant_id', 'user_id', 'respondent_id']
        if not any(col in columns_lower for col in id_columns):
            format_results["issues"].append("No participant ID column found")
        
        # Check for response columns
        response_columns = [col for col in columns_lower if any(
            keyword in col for keyword in ['q', 'question', 'response', 'answer']
        )]
        
        if len(response_columns) < 5:
            format_results["issues"].append(
                f"Few response columns detected: {len(response_columns)}"
            )
        
        if format_results["issues"]:
            format_results["is_valid"] = False
        
        return format_results


def validate_assessment_id(assessment_id: str) -> bool:
    """
    Validate assessment ID format.
    
    Args:
        assessment_id: Assessment ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not assessment_id:
        return False
    
    # Check length (should be reasonable)
    if len(assessment_id) < 8 or len(assessment_id) > 100:
        return False
    
    # Check for valid characters (alphanumeric, hyphens, underscores)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', assessment_id):
        return False
    
    return True


def validate_file_path(file_path: str) -> bool:
    """
    Validate file path security.
    
    Args:
        file_path: File path to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not file_path:
        return False
    
    # Check for path traversal attempts
    if '..' in file_path or file_path.startswith('/'):
        return False
    
    # Check for valid characters
    import re
    if not re.match(r'^[a-zA-Z0-9._/-]+$', file_path):
        return False
    
    return True