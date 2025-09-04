"""
Data Preprocessing Module for Psychometric Assessment System

Handles data transformation, cleaning, and preparation for downstream analysis.
Converts raw assessment responses into analysis-ready formats.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
from dataclasses import dataclass
from pathlib import Path
import warnings
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer, KNNImputer
try:
    from .item_mapper import ItemMapper
    from .data_validator import DataValidator
except ImportError:
    try:
        from item_mapper import ItemMapper
        from data_validator import DataValidator
    except ImportError:
        print("Warning: Could not import ItemMapper and DataValidator")
        class ItemMapper:
            def __init__(self):
                self.constructs = {}
                self.item_construct_map = {}
                self.reverse_items = set()
            def get_all_constructs(self):
                return self.constructs
            def get_construct_for_item(self, item):
                return self.item_construct_map.get(item)
            def get_items_for_construct(self, construct):
                return [item for item, const in self.item_construct_map.items() if const == construct]
        class DataValidator:
            def __init__(self, item_mapper):
                self.item_mapper = item_mapper
            def validate_dataset(self, data):
                return type('ValidationResult', (), {'success': True, 'errors': []})()


@dataclass
class PreprocessingConfig:
    """Configuration for preprocessing operations."""
    handle_missing: str = 'knn'  # 'drop', 'mean', 'median', 'knn'
    outlier_method: str = 'iqr'  # 'iqr', 'zscore', 'isolation_forest', 'none'
    outlier_threshold: float = 3.0
    scaling_method: str = 'standard'  # 'standard', 'minmax', 'robust', 'none'
    create_construct_scores: bool = True
    min_items_per_construct: int = 3  # Minimum items required for construct score
    construct_aggregation: str = 'mean'  # 'mean', 'median', 'sum'
    remove_incomplete_persons: bool = False
    completion_threshold: float = 0.8  # Minimum completion rate to keep person


@dataclass
class PreprocessingResult:
    """Container for preprocessing results."""
    success: bool
    processed_data: Optional[pd.DataFrame]
    construct_scores: Optional[pd.DataFrame]
    person_level_data: Optional[pd.DataFrame]
    removed_outliers: List[str]
    imputed_values: Dict[str, int]
    scaling_info: Dict[str, Any]
    processing_log: List[str]
    errors: List[str]
    config_used: PreprocessingConfig


class PsychometricDataPreprocessor:
    """
    Preprocesses psychometric assessment data for analysis.
    
    Handles:
    - Missing value imputation
    - Outlier detection and removal
    - Data scaling and normalization
    - Construct score calculation
    - Person-level aggregation
    - Data format conversion
    """
    
    def __init__(self, item_mapper: Optional[ItemMapper] = None,
                 config: Optional[PreprocessingConfig] = None):
        """
        Initialize the data preprocessor.
        
        Args:
            item_mapper: ItemMapper instance for construct information
            config: PreprocessingConfig with processing parameters
        """
        self.logger = logging.getLogger(__name__)
        self.item_mapper = item_mapper or ItemMapper()
        self.config = config or PreprocessingConfig()
        
        # Store fitted transformers for consistency
        self.scalers = {}
        self.imputers = {}
        
        self.logger.info("PsychometricDataPreprocessor initialized")
    
    def preprocess_data(self, data: pd.DataFrame, 
                       config: Optional[PreprocessingConfig] = None) -> PreprocessingResult:
        """
        Main preprocessing pipeline for psychometric data.
        
        Args:
            data: Validated DataFrame from data ingestion
            config: Optional preprocessing configuration
            
        Returns:
            PreprocessingResult with processed data and metadata
        """
        config = config or self.config
        processing_log = []
        errors = []
        
        self.logger.info(f"Starting preprocessing of {len(data)} records")
        processing_log.append(f"Input data: {len(data)} records, {data['Persons'].nunique()} persons")
        
        try:
            # Step 1: Create wide format data (persons × items)
            wide_data = self._create_wide_format(data)
            processing_log.append(f"Created wide format: {wide_data.shape[0]} persons × {wide_data.shape[1]} items")
            
            # Step 2: Handle missing values
            if config.handle_missing != 'none':
                wide_data, imputation_info = self._handle_missing_values(wide_data, config.handle_missing)
                processing_log.append(f"Missing value handling: {sum(imputation_info.values())} values imputed")
            else:
                imputation_info = {}
            
            # Step 3: Filter persons by completion rate
            if config.remove_incomplete_persons:
                wide_data, removed_persons = self._filter_incomplete_persons(
                    wide_data, config.completion_threshold
                )
                processing_log.append(f"Removed {len(removed_persons)} incomplete persons")
            else:
                removed_persons = []
            
            # Step 4: Detect and handle outliers
            outliers_removed = []
            if config.outlier_method != 'none':
                wide_data, outliers_removed = self._handle_outliers(
                    wide_data, config.outlier_method, config.outlier_threshold
                )
                processing_log.append(f"Outlier detection: {len(outliers_removed)} outliers handled")
            
            # Step 5: Apply reverse scoring
            wide_data = self._apply_reverse_scoring(wide_data)
            processing_log.append("Applied reverse scoring to appropriate items")
            
            # Step 6: Scale/normalize data
            scaling_info = {}
            if config.scaling_method != 'none':
                wide_data, scaling_info = self._scale_data(wide_data, config.scaling_method)
                processing_log.append(f"Applied {config.scaling_method} scaling")
            
            # Step 7: Calculate construct scores
            construct_scores = None
            if config.create_construct_scores:
                construct_scores = self._calculate_construct_scores(
                    wide_data, config.construct_aggregation, config.min_items_per_construct
                )
                processing_log.append(f"Calculated construct scores: {construct_scores.shape[1]} constructs")
            
            # Step 8: Create person-level summary data
            person_level_data = self._create_person_level_data(wide_data, construct_scores)
            processing_log.append(f"Created person-level data: {person_level_data.shape[1]} features")
            
            # Convert back to long format for compatibility
            processed_long_data = self._convert_to_long_format(wide_data)
            
            self.logger.info(f"Preprocessing completed successfully: {len(processed_long_data)} records")
            
            return PreprocessingResult(
                success=True,
                processed_data=processed_long_data,
                construct_scores=construct_scores,
                person_level_data=person_level_data,
                removed_outliers=outliers_removed,
                imputed_values=imputation_info,
                scaling_info=scaling_info,
                processing_log=processing_log,
                errors=errors,
                config_used=config
            )
            
        except Exception as e:
            error = f"Preprocessing failed: {str(e)}"
            errors.append(error)
            self.logger.error(error, exc_info=True)
            
            return PreprocessingResult(
                success=False,
                processed_data=None,
                construct_scores=None,
                person_level_data=None,
                removed_outliers=[],
                imputed_values={},
                scaling_info={},
                processing_log=processing_log,
                errors=errors,
                config_used=config
            )
    
    def _create_wide_format(self, data: pd.DataFrame) -> pd.DataFrame:
        """Convert long format data to wide format (persons × items)."""
        # Pivot data to wide format
        wide_data = data.pivot(
            index='Persons',
            columns='Assessment_Items', 
            values='Measure'
        ).copy()
        
        # FIXED: Only add missing columns for items that actually exist in your mapping
        # AND only if we want to enforce complete coverage
        expected_items = self.item_mapper.get_all_items()
        current_items = set(wide_data.columns)
        expected_items_set = set(expected_items)
        
        # Only add missing columns if we have a significant portion of expected items
        # This prevents the issue where test data with few items gets padded to 147 columns
        coverage_ratio = len(current_items.intersection(expected_items_set)) / len(expected_items_set)
        
        if coverage_ratio > 0.5:  # Only pad if we have >50% of expected items
            missing_columns = expected_items_set - current_items
            for col in missing_columns:
                wide_data[col] = np.nan
            # Reorder columns to match expected item order
            wide_data = wide_data.reindex(columns=expected_items, fill_value=np.nan)
        
        return wide_data
    
    def _handle_missing_values(self, data: pd.DataFrame, method: str) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Handle missing values using specified method."""
        data = data.copy()
        imputation_info = {}
        
        # Count missing values before imputation
        missing_before = data.isnull().sum().sum()
        
        if method == 'drop':
            # Drop rows with any missing values
            data = data.dropna()
            imputation_info['dropped_rows'] = missing_before
            
        elif method == 'mean':
            # Impute with mean values
            imputer = SimpleImputer(strategy='mean')
            data_imputed = pd.DataFrame(
                imputer.fit_transform(data),
                index=data.index,
                columns=data.columns
            )
            imputation_info['mean_imputed'] = missing_before
            data = data_imputed
            self.imputers['mean'] = imputer
            
        elif method == 'median':
            # Impute with median values
            imputer = SimpleImputer(strategy='median')
            data_imputed = pd.DataFrame(
                imputer.fit_transform(data),
                index=data.index,
                columns=data.columns
            )
            imputation_info['median_imputed'] = missing_before
            data = data_imputed
            self.imputers['median'] = imputer
            
        elif method == 'knn':
            # KNN imputation
            imputer = KNNImputer(n_neighbors=5)
            data_imputed = pd.DataFrame(
                imputer.fit_transform(data),
                index=data.index,
                columns=data.columns
            )
            imputation_info['knn_imputed'] = missing_before
            data = data_imputed
            self.imputers['knn'] = imputer
        
        return data, imputation_info
    
    def _filter_incomplete_persons(self, data: pd.DataFrame, 
                                  threshold: float) -> Tuple[pd.DataFrame, List[str]]:
        """Remove persons with low completion rates."""
        completion_rates = data.notna().mean(axis=1)
        incomplete_persons = completion_rates[completion_rates < threshold].index.tolist()
        
        filtered_data = data[completion_rates >= threshold].copy()
        
        return filtered_data, incomplete_persons
    
    def _handle_outliers(self, data: pd.DataFrame, method: str, 
                        threshold: float) -> Tuple[pd.DataFrame, List[str]]:
        """Detect and handle outliers using specified method."""
        data = data.copy()
        outliers_removed = []
        
        if method == 'iqr':
            # IQR method for outlier detection
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Replace outliers with bounds (winsorizing)
            outlier_mask = (data < lower_bound) | (data > upper_bound)
            data = data.clip(lower=lower_bound, upper=upper_bound, axis=1)
            
            outliers_removed = outlier_mask.sum().sum()
            
        elif method == 'zscore':
            # Z-score method
            z_scores = np.abs((data - data.mean()) / data.std())
            outlier_mask = z_scores > threshold
            
            # Replace with median values
            medians = data.median()
            for col in data.columns:
                data.loc[outlier_mask[col], col] = medians[col]
            
            outliers_removed = outlier_mask.sum().sum()
            
        elif method == 'isolation_forest':
            # Isolation Forest method
            from sklearn.ensemble import IsolationForest
            
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            outlier_labels = iso_forest.fit_predict(data.fillna(data.median()))
            
            outlier_persons = data.index[outlier_labels == -1].tolist()
            data = data[outlier_labels != -1]
            outliers_removed = outlier_persons
        
        return data, outliers_removed
    
    def _apply_reverse_scoring(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply reverse scoring to appropriate items."""
        data = data.copy()
        
        # Get reverse-scored items that exist in the data
        reverse_items = [item for item in self.item_mapper.reverse_scored_items 
                        if item in data.columns]
        
        if reverse_items:
            # Calculate the theoretical range for reverse scoring
            # Assuming Rasch measures typically range from -4 to +4
            min_val = data[reverse_items].min().min()
            max_val = data[reverse_items].max().max()
            
            # Reverse score: new_value = max + min - old_value
            data[reverse_items] = (max_val + min_val) - data[reverse_items]
            
            self.logger.debug(f"Applied reverse scoring to {len(reverse_items)} items")
        
        return data
    
    def _scale_data(self, data: pd.DataFrame, method: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Scale data using specified method."""
        data = data.copy()
        scaling_info = {'method': method}
        
        if method == 'standard':
            # Z-score standardization
            scaler = StandardScaler()
            scaled_values = scaler.fit_transform(data)
            data = pd.DataFrame(scaled_values, index=data.index, columns=data.columns)
            self.scalers['standard'] = scaler
            scaling_info.update({
                'means': scaler.mean_.tolist(),
                'stds': scaler.scale_.tolist()
            })
            
        elif method == 'minmax':
            # Min-max scaling to [0, 1]
            scaler = MinMaxScaler()
            scaled_values = scaler.fit_transform(data)
            data = pd.DataFrame(scaled_values, index=data.index, columns=data.columns)
            self.scalers['minmax'] = scaler
            scaling_info.update({
                'mins': scaler.min_.tolist(),
                'scales': scaler.scale_.tolist()
            })
            
        elif method == 'robust':
            # Robust scaling using median and IQR
            from sklearn.preprocessing import RobustScaler
            scaler = RobustScaler()
            scaled_values = scaler.fit_transform(data)
            data = pd.DataFrame(scaled_values, index=data.index, columns=data.columns)
            self.scalers['robust'] = scaler
            scaling_info.update({
                'medians': scaler.center_.tolist(),
                'scales': scaler.scale_.tolist()
            })
        
        return data, scaling_info
    
    def _calculate_construct_scores(self, data: pd.DataFrame, 
                                   aggregation: str, 
                                   min_items: int) -> pd.DataFrame:
        """Calculate construct-level scores from item-level data."""
        construct_scores = pd.DataFrame(index=data.index)
        
        for construct_code in self.item_mapper.get_all_constructs().keys():
            construct_items = self.item_mapper.get_items_for_construct(construct_code)
            
            # Filter to items that exist in the data
            available_items = [item for item in construct_items if item in data.columns]
            
            if len(available_items) >= min_items:
                construct_data = data[available_items]
                
                if aggregation == 'mean':
                    construct_scores[construct_code] = construct_data.mean(axis=1)
                elif aggregation == 'median':
                    construct_scores[construct_code] = construct_data.median(axis=1)
                elif aggregation == 'sum':
                    construct_scores[construct_code] = construct_data.sum(axis=1)
                    
                # Add construct reliability measure (Cronbach's alpha approximation)
                if len(available_items) > 1:
                    construct_scores[f'{construct_code}_reliability'] = self._calculate_reliability(
                        construct_data
                    )
            else:
                self.logger.warning(f"Construct {construct_code} has insufficient items "
                                  f"({len(available_items)} < {min_items})")
        
        return construct_scores
    
    def _calculate_reliability(self, construct_data: pd.DataFrame) -> pd.Series:
        """Calculate reliability measure for construct scores."""
        # Simple internal consistency measure
        # Calculate inter-item correlations
        correlations = construct_data.corr().values
        
        # Extract upper triangle (excluding diagonal)
        upper_triangle = correlations[np.triu_indices_from(correlations, k=1)]
        
        # Return mean correlation as reliability proxy
        reliability = np.nanmean(upper_triangle) if len(upper_triangle) > 0 else np.nan
        
        return pd.Series([reliability] * len(construct_data), index=construct_data.index)
    
    def _create_person_level_data(self, item_data: pd.DataFrame, 
                                 construct_scores: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Create comprehensive person-level summary dataset."""
        person_data = pd.DataFrame(index=item_data.index)
        
        # Basic statistics
        person_data['total_items'] = item_data.notna().sum(axis=1)
        person_data['completion_rate'] = item_data.notna().mean(axis=1)
        person_data['mean_measure'] = item_data.mean(axis=1)
        person_data['std_measure'] = item_data.std(axis=1)
        person_data['min_measure'] = item_data.min(axis=1)
        person_data['max_measure'] = item_data.max(axis=1)
        person_data['range_measure'] = person_data['max_measure'] - person_data['min_measure']
        
        # Add construct scores if available
        if construct_scores is not None:
            person_data = pd.concat([person_data, construct_scores], axis=1)
        
        # Add construct-specific statistics
        for construct_code in self.item_mapper.get_all_constructs().keys():
            construct_items = self.item_mapper.get_items_for_construct(construct_code)
            available_items = [item for item in construct_items if item in item_data.columns]
            
            if available_items:
                construct_data = item_data[available_items]
                person_data[f'{construct_code}_items_completed'] = construct_data.notna().sum(axis=1)
                person_data[f'{construct_code}_completion_rate'] = construct_data.notna().mean(axis=1)
        
        return person_data
    
    def _convert_to_long_format(self, wide_data: pd.DataFrame) -> pd.DataFrame:
        """Convert wide format data back to long format."""
        # Reset index to make Persons a column
        wide_data_reset = wide_data.reset_index()
        
        # Melt to long format
        long_data = pd.melt(
            wide_data_reset,
            id_vars=['Persons'],
            var_name='Assessment_Items',
            value_name='Measure'
        )
        
        # Remove rows with NaN measures
        long_data = long_data.dropna(subset=['Measure'])
        
        # Add sequence numbers
        long_data = long_data.sort_values(['Persons', 'Assessment_Items'])
        long_data['E1'] = long_data.groupby('Persons').cumcount() + 1
        long_data['E2'] = long_data.groupby('Assessment_Items').cumcount() + 1
        
        # Reorder columns to match original format
        long_data = long_data[['Measure', 'E1', 'E2', 'Persons', 'Assessment_Items']]
        
        return long_data.reset_index(drop=True)
    
    def export_processed_data(self, result: PreprocessingResult, 
                             output_dir: Union[str, Path],
                             formats: List[str] = ['csv']):
        """
        Export processed data in multiple formats.
        
        Args:
            result: PreprocessingResult to export
            output_dir: Directory to save exported files
            formats: List of formats to export ('csv', 'parquet', 'excel')
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        datasets = {
            'processed_data': result.processed_data,
            'construct_scores': result.construct_scores,
            'person_level_data': result.person_level_data
        }
        
        for dataset_name, dataset in datasets.items():
            if dataset is not None:
                for format_type in formats:
                    filename = f"{dataset_name}.{format_type}"
                    filepath = output_dir / filename
                    
                    if format_type == 'csv':
                        dataset.to_csv(filepath, index=True)
                    elif format_type == 'parquet':
                        dataset.to_parquet(filepath, index=True)
                    elif format_type == 'excel':
                        dataset.to_excel(filepath, index=True)
        
        # Export processing log and metadata
        metadata = {
            'config': result.config_used.__dict__,
            'processing_log': result.processing_log,
            'removed_outliers': result.removed_outliers,
            'imputed_values': result.imputed_values,
            'scaling_info': result.scaling_info
        }
        
        import json
        with open(output_dir / 'preprocessing_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        self.logger.info(f"Processed data exported to {output_dir}")
    
    def create_analysis_ready_dataset(self, result: PreprocessingResult,
                                     analysis_type: str = 'comprehensive') -> pd.DataFrame:
        """
        Create analysis-ready dataset for specific analysis types.
        
        Args:
            result: PreprocessingResult with processed data
            analysis_type: Type of analysis ('item_level', 'construct_level', 'comprehensive')
            
        Returns:
            DataFrame optimized for the specified analysis
        """
        if analysis_type == 'item_level':
            return result.processed_data
        
        elif analysis_type == 'construct_level':
            if result.construct_scores is not None:
                return result.construct_scores
            else:
                raise ValueError("Construct scores not available. Enable create_construct_scores in config.")
        
        elif analysis_type == 'comprehensive':
            return result.person_level_data
        
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")


# Utility functions for easy access
def preprocess_assessment_data(data: pd.DataFrame, 
                              config: Optional[PreprocessingConfig] = None) -> PreprocessingResult:
    """
    Quick utility to preprocess assessment data.
    
    Args:
        data: Validated DataFrame from data ingestion
        config: Optional preprocessing configuration
        
    Returns:
        PreprocessingResult with processed data
    """
    preprocessor = PsychometricDataPreprocessor()
    return preprocessor.preprocess_data(data, config)


def create_custom_config(handle_missing: str = 'knn',
                        outlier_method: str = 'iqr',
                        scaling_method: str = 'standard',
                        create_constructs: bool = True) -> PreprocessingConfig:
    """
    Create custom preprocessing configuration.
    
    Args:
        handle_missing: Missing value strategy
        outlier_method: Outlier detection method
        scaling_method: Data scaling method
        create_constructs: Whether to calculate construct scores
        
    Returns:
        PreprocessingConfig with specified settings
    """
    return PreprocessingConfig(
        handle_missing=handle_missing,
        outlier_method=outlier_method,
        scaling_method=scaling_method,
        create_construct_scores=create_constructs
    )


if __name__ == "__main__":
    # Demo usage
    import sys
    try:
        from .data_ingestion import process_assessment_file
    except ImportError:
        from data_ingestion import process_assessment_file
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        
        # First ingest and validate the data
        ingestion_result = process_assessment_file(filepath)
        
        if ingestion_result.success:
            # Then preprocess
            config = PreprocessingConfig(
                handle_missing='knn',
                outlier_method='iqr',
                scaling_method='standard',
                create_construct_scores=True
            )
            
            preprocessing_result = preprocess_assessment_data(
                ingestion_result.data, config
            )
            
            if preprocessing_result.success:
                print("Preprocessing succeeded!")
                print(f"Processed {len(preprocessing_result.processed_data)} records")
                print(f"Created {preprocessing_result.construct_scores.shape[1]} construct scores")
                print(f"Person-level data: {preprocessing_result.person_level_data.shape}")
                
                # Export processed data
                preprocessor = PsychometricDataPreprocessor()
                preprocessor.export_processed_data(
                    preprocessing_result, 
                    'processed_output',
                    ['csv', 'parquet']
                )
            else:
                print("Preprocessing failed:")
                for error in preprocessing_result.errors:
                    print(f"  - {error}")
        else:
            print("Data ingestion failed. Cannot proceed with preprocessing.")
    else:
        print("Usage: python data_preprocessor.py <data_file_path>")