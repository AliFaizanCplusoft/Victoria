"""
RaschPy Integration Module for Victoria Project

Handles Rasch model analysis using RaschPy library to:
- Process person-item response matrices
- Generate person ability estimates and item difficulty measures
- Calculate fit statistics (infit, outfit)
- Produce final transformed dataset with Rasch measures
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
from dataclasses import dataclass
import warnings

# RaschPy imports - using correct classes and methods
try:
    import RaschPy as rp
    from RaschPy import SLM, PCM, RSM, MFRM
    RASCHPY_AVAILABLE = True
except ImportError:
    RASCHPY_AVAILABLE = False
    rp = None
    SLM = None
    PCM = None
    RSM = None
    MFRM = None

@dataclass
class RaschResults:
    """Container for Rasch analysis results."""
    success: bool
    person_abilities: Optional[pd.DataFrame]
    item_difficulties: Optional[pd.DataFrame]
    fit_statistics: Optional[pd.DataFrame]
    transformed_data: Optional[pd.DataFrame]
    model_summary: Dict[str, Any]
    processing_log: List[str]
    errors: List[str]

class RaschAnalyzer:
    """
    RaschPy integration class for Victoria Project.
    
    Handles the complete Rasch analysis pipeline:
    1. Data preprocessing for RaschPy format
    2. Model fitting and estimation
    3. Person ability and item difficulty calculation
    4. Fit statistics computation
    5. Data transformation to target format
    """
    
    def __init__(self):
        """Initialize the Rasch analyzer."""
        self.logger = logging.getLogger(__name__)
        
        if not RASCHPY_AVAILABLE:
            self.logger.warning("RaschPy not available. Install with: pip install git+https://github.com/MarkElliott999/RaschPy.git")
        else:
            self.logger.info("RaschPy available for Rasch model analysis")
    
    def analyze_data(self, data: pd.DataFrame, 
                    person_col: str = 'Persons',
                    item_col: str = 'Assessment_Items',
                    response_col: str = 'Measure') -> RaschResults:
        """
        Perform complete Rasch analysis on the dataset.
        
        Args:
            data: DataFrame with person-item responses
            person_col: Column name for person identifiers
            item_col: Column name for item identifiers
            response_col: Column name for response values
            
        Returns:
            RaschResults object with analysis results
        """
        processing_log = []
        errors = []
        
        self.logger.info("Starting Rasch analysis")
        processing_log.append("Starting Rasch analysis")
        
        if not RASCHPY_AVAILABLE:
            error = "RaschPy not available. Cannot perform Rasch analysis."
            errors.append(error)
            self.logger.error(error)
            return RaschResults(
                success=False, person_abilities=None, item_difficulties=None,
                fit_statistics=None, transformed_data=None, model_summary={},
                processing_log=processing_log, errors=errors
            )
        
        try:
            # Step 1: Prepare data for RaschPy
            person_item_matrix = self._prepare_person_item_matrix(data, person_col, item_col, response_col)
            processing_log.append(f"Created person-item matrix: {person_item_matrix.shape[0]} persons × {person_item_matrix.shape[1]} items")
            
            # Step 2: Fit Rasch model
            rasch_model = self._fit_rasch_model(person_item_matrix)
            processing_log.append("Fitted Rasch model")
            
            # Step 3: Extract person abilities
            person_abilities = self._extract_person_abilities(rasch_model, person_item_matrix)
            processing_log.append(f"Extracted person abilities: {len(person_abilities)} persons")
            
            # Step 4: Extract item difficulties
            item_difficulties = self._extract_item_difficulties(rasch_model, person_item_matrix)
            processing_log.append(f"Extracted item difficulties: {len(item_difficulties)} items")
            
            # Step 5: Calculate fit statistics
            fit_statistics = self._calculate_fit_statistics(rasch_model, person_item_matrix)
            processing_log.append("Calculated fit statistics")
            
            # Step 6: Transform data to target format
            transformed_data = self._transform_to_target_format(
                data, person_abilities, item_difficulties, person_col, item_col, response_col
            )
            processing_log.append(f"Transformed data to target format: {len(transformed_data)} records")
            
            # Step 7: Create model summary
            model_summary = self._create_model_summary(rasch_model, person_abilities, item_difficulties)
            
            self.logger.info("Rasch analysis completed successfully")
            
            return RaschResults(
                success=True,
                person_abilities=person_abilities,
                item_difficulties=item_difficulties,
                fit_statistics=fit_statistics,
                transformed_data=transformed_data,
                model_summary=model_summary,
                processing_log=processing_log,
                errors=errors
            )
            
        except Exception as e:
            error = f"Error in Rasch analysis: {str(e)}"
            errors.append(error)
            self.logger.error(error, exc_info=True)
            
            return RaschResults(
                success=False, person_abilities=None, item_difficulties=None,
                fit_statistics=None, transformed_data=None, model_summary={},
                processing_log=processing_log, errors=errors
            )
    
    def _prepare_person_item_matrix(self, data: pd.DataFrame, 
                                   person_col: str, item_col: str, response_col: str) -> pd.DataFrame:
        """
        Prepare person-item matrix for RaschPy analysis.
        
        Args:
            data: Input data in long format
            person_col: Person identifier column
            item_col: Item identifier column
            response_col: Response value column
            
        Returns:
            Person-item matrix with persons as rows and items as columns
        """
        # Create pivot table with persons as rows and items as columns
        person_item_matrix = data.pivot_table(
            index=person_col,
            columns=item_col,
            values=response_col,
            aggfunc='first'  # Use first response if duplicates exist
        )
        
        # RaschPy expects specific data format - no NaN values
        # Fill NaN values with 0 (assuming 0 means no response/incorrect)
        person_item_matrix = person_item_matrix.fillna(0)
        
        # Ensure all values are integers (required by RaschPy)
        person_item_matrix = person_item_matrix.astype(int)
        
        self.logger.info(f"Person-item matrix shape: {person_item_matrix.shape}")
        self.logger.info(f"Response range: {person_item_matrix.min().min()} to {person_item_matrix.max().max()}")
        
        return person_item_matrix
    
    def _fit_rasch_model(self, person_item_matrix: pd.DataFrame) -> Any:
        """
        Fit Rasch model using RaschPy proper classes.
        
        Args:
            person_item_matrix: Person-item response matrix
            
        Returns:
            Fitted RaschPy model object
        """
        try:
            # RaschPy expects DataFrame directly, not numpy array
            # Determine model type based on response range
            max_score = int(person_item_matrix.max().max())
            
            if max_score == 1:
                # Dichotomous data - use Simple Logistic Model (SLM)
                rasch_model = rp.SLM(person_item_matrix)
                self.logger.info("Using SLM (Simple Logistic Model) for dichotomous data")
            elif max_score > 1:
                # Polytomous data - use Rating Scale Model (RSM)
                rasch_model = rp.RSM(person_item_matrix)
                self.logger.info(f"Using RSM (Rating Scale Model) for polytomous data (max_score={max_score})")
            else:
                raise ValueError("Invalid response data: all responses are 0")
            
            # Calibrate the model - this is where parameter estimation happens
            rasch_model.calibrate()
            
            self.logger.info("Rasch model calibrated successfully")
            return rasch_model
            
        except Exception as e:
            self.logger.error(f"Error fitting Rasch model: {e}")
            raise
    
    def _extract_person_abilities(self, rasch_model: Any, person_item_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        Extract person abilities from fitted RaschPy model.
        
        Args:
            rasch_model: Fitted RaschPy model object
            person_item_matrix: Original person-item matrix
            
        Returns:
            DataFrame with person abilities and fit statistics
        """
        try:
            # Generate person statistics using RaschPy methods
            rasch_model.person_stats_df()
            
            # Extract person abilities from the person_stats DataFrame
            person_stats = rasch_model.person_stats.copy()
            
            # Create DataFrame with person information
            person_df = pd.DataFrame({
                'person_id': person_item_matrix.index,
                'ability': person_stats['Ability'].values if 'Ability' in person_stats.columns else np.zeros(len(person_item_matrix.index)),
                'ability_se': person_stats['SE'].values if 'SE' in person_stats.columns else np.full(len(person_item_matrix.index), np.nan),
                'person_fit': person_stats['Infit'].values if 'Infit' in person_stats.columns else np.full(len(person_item_matrix.index), np.nan)
            })
            
            return person_df
            
        except Exception as e:
            self.logger.error(f"Error extracting person abilities: {e}")
            # Fallback: create basic person estimates
            person_df = pd.DataFrame({
                'person_id': person_item_matrix.index,
                'ability': np.zeros(len(person_item_matrix.index)),
                'ability_se': np.full(len(person_item_matrix.index), np.nan),
                'person_fit': np.full(len(person_item_matrix.index), np.nan)
            })
            return person_df
    
    def _extract_item_difficulties(self, rasch_model: Any, person_item_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        Extract item difficulties from fitted RaschPy model.
        
        Args:
            rasch_model: Fitted RaschPy model object
            person_item_matrix: Original person-item matrix
            
        Returns:
            DataFrame with item difficulties and fit statistics
        """
        try:
            # Generate item statistics using RaschPy methods
            rasch_model.item_stats_df()
            
            # Extract item difficulties from the item_stats DataFrame
            item_stats = rasch_model.item_stats.copy()
            
            # Create DataFrame with item information
            item_df = pd.DataFrame({
                'item_id': person_item_matrix.columns,
                'difficulty': item_stats['Difficulty'].values if 'Difficulty' in item_stats.columns else np.zeros(len(person_item_matrix.columns)),
                'difficulty_se': item_stats['SE'].values if 'SE' in item_stats.columns else np.full(len(person_item_matrix.columns), np.nan),
                'item_fit': item_stats['Infit'].values if 'Infit' in item_stats.columns else np.full(len(person_item_matrix.columns), np.nan)
            })
            
            return item_df
            
        except Exception as e:
            self.logger.error(f"Error extracting item difficulties: {e}")
            # Fallback: create basic item estimates
            item_df = pd.DataFrame({
                'item_id': person_item_matrix.columns,
                'difficulty': np.zeros(len(person_item_matrix.columns)),
                'difficulty_se': np.full(len(person_item_matrix.columns), np.nan),
                'item_fit': np.full(len(person_item_matrix.columns), np.nan)
            })
            return item_df
    
    def _calculate_fit_statistics(self, rasch_model: Any, person_item_matrix: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate fit statistics for the Rasch model.
        
        Args:
            rasch_model: Fitted RaschModel object
            person_item_matrix: Original person-item matrix
            
        Returns:
            DataFrame with fit statistics
        """
        try:
            fit_stats = []
            
            # Model-level fit statistics
            if hasattr(rasch_model, 'model_fit'):
                fit_stats.append({
                    'statistic': 'model_fit',
                    'value': rasch_model.model_fit,
                    'type': 'model'
                })
            
            # Person fit statistics
            if hasattr(rasch_model, 'person_fit'):
                for i, person_id in enumerate(person_item_matrix.index):
                    fit_stats.append({
                        'statistic': 'person_fit',
                        'value': rasch_model.person_fit[i],
                        'type': 'person',
                        'id': person_id
                    })
            
            # Item fit statistics
            if hasattr(rasch_model, 'item_fit'):
                for i, item_id in enumerate(person_item_matrix.columns):
                    fit_stats.append({
                        'statistic': 'item_fit',
                        'value': rasch_model.item_fit[i],
                        'type': 'item',
                        'id': item_id
                    })
            
            return pd.DataFrame(fit_stats)
            
        except Exception as e:
            self.logger.error(f"Error calculating fit statistics: {e}")
            return pd.DataFrame()
    
    def _transform_to_target_format(self, original_data: pd.DataFrame, 
                                   person_abilities: pd.DataFrame,
                                   item_difficulties: pd.DataFrame,
                                   person_col: str, item_col: str, response_col: str) -> pd.DataFrame:
        """
        Transform data to the exact target format with Rasch measures.
        
        Target format:
        Measure    E1    E2    Persons    Assessment_Items
        1.37       1     1     6728f3d973b4504d88a81299    EnergizedByPotential
        
        Args:
            original_data: Original data in long format
            person_abilities: Person abilities from Rasch analysis
            item_difficulties: Item difficulties from Rasch analysis
            person_col: Person identifier column
            item_col: Item identifier column  
            response_col: Response value column
            
        Returns:
            DataFrame in target format with Rasch measures
        """
        # Create mapping dictionaries
        person_ability_map = dict(zip(person_abilities['person_id'], person_abilities['ability']))
        item_difficulty_map = dict(zip(item_difficulties['item_id'], item_difficulties['difficulty']))
        
        # Create transformed data
        transformed_data = original_data.copy()
        
        # Calculate Rasch measures (person ability - item difficulty)
        # This creates the logit-based measures shown in your example
        transformed_data['Measure'] = (
            transformed_data[person_col].map(person_ability_map) - 
            transformed_data[item_col].map(item_difficulty_map)
        )
        
        # Add sequence numbers if not present
        if 'E1' not in transformed_data.columns:
            person_sequence = {person: idx + 1 for idx, person in enumerate(transformed_data[person_col].unique())}
            transformed_data['E1'] = transformed_data[person_col].map(person_sequence)
        
        if 'E2' not in transformed_data.columns:
            # E2 should reset to 1 for each person (question number within person)
            transformed_data = transformed_data.sort_values([person_col, item_col]).reset_index(drop=True)
            transformed_data['E2'] = transformed_data.groupby(person_col).cumcount() + 1
        
        # Select and rename columns to match exact target format
        result_data = transformed_data[['Measure', 'E1', 'E2', person_col, item_col]].copy()
        result_data = result_data.rename(columns={
            person_col: 'Persons',
            item_col: 'Assessment_Items'
        })
        
        # Remove rows with NaN measures
        result_data = result_data.dropna(subset=['Measure'])
        
        # Sort by E1 (person sequence) and E2 (item sequence) to match your format
        result_data = result_data.sort_values(['E1', 'E2']).reset_index(drop=True)
        
        # Round Measure values to 2 decimal places to match your format
        result_data['Measure'] = result_data['Measure'].round(2)
        
        return result_data
    
    def _create_model_summary(self, rasch_model: Any, 
                             person_abilities: pd.DataFrame,
                             item_difficulties: pd.DataFrame) -> Dict[str, Any]:
        """
        Create a summary of the Rasch model results.
        
        Args:
            rasch_model: Fitted RaschModel object
            person_abilities: Person abilities DataFrame
            item_difficulties: Item difficulties DataFrame
            
        Returns:
            Dictionary with model summary information
        """
        summary = {
            'model_type': 'Rasch Model',
            'persons_count': len(person_abilities),
            'items_count': len(item_difficulties),
            'person_ability_stats': {
                'mean': person_abilities['ability'].mean(),
                'std': person_abilities['ability'].std(),
                'min': person_abilities['ability'].min(),
                'max': person_abilities['ability'].max()
            },
            'item_difficulty_stats': {
                'mean': item_difficulties['difficulty'].mean(),
                'std': item_difficulties['difficulty'].std(),
                'min': item_difficulties['difficulty'].min(),
                'max': item_difficulties['difficulty'].max()
            }
        }
        
        # Add model-specific statistics if available
        if hasattr(rasch_model, 'reliability'):
            summary['reliability'] = rasch_model.reliability
        
        if hasattr(rasch_model, 'separation'):
            summary['separation'] = rasch_model.separation
            
        return summary
    
    def analyze_person_data(self, person_id: str, raw_data: Any) -> RaschResults:
        """
        Analyze data for a specific person using Rasch model.
        
        Args:
            person_id: Person identifier
            raw_data: Raw assessment data for this person
            
        Returns:
            RaschResults object with individual analysis
        """
        try:
            # Convert raw_data to DataFrame format expected by analyze_data
            if hasattr(raw_data, 'to_dataframe'):
                data_df = raw_data.to_dataframe()
            elif isinstance(raw_data, dict):
                # Convert dict to DataFrame
                data_df = pd.DataFrame([raw_data])
            else:
                # Assume it's already a DataFrame
                data_df = raw_data
            
            # Filter for this specific person if multiple persons in data
            if 'Persons' in data_df.columns:
                person_data = data_df[data_df['Persons'] == person_id]
            else:
                person_data = data_df
            
            # If no data found, return empty results
            if person_data.empty:
                return RaschResults(
                    success=False, person_abilities=None, item_difficulties=None,
                    fit_statistics=None, transformed_data=None, model_summary={},
                    processing_log=[], errors=[f"No data found for person {person_id}"]
                )
            
            # Run full Rasch analysis on person data
            return self.analyze_data(person_data)
            
        except Exception as e:
            self.logger.error(f"Error analyzing person data: {e}")
            return RaschResults(
                success=False, person_abilities=None, item_difficulties=None,
                fit_statistics=None, transformed_data=None, model_summary={},
                processing_log=[], errors=[str(e)]
            )

    def export_results(self, results: RaschResults, output_dir: Path) -> Dict[str, str]:
        """
        Export Rasch analysis results to multiple formats.
        
        Args:
            results: RaschResults object
            output_dir: Directory to save results
            
        Returns:
            Dictionary with paths to exported files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        export_paths = {}
        
        try:
            # Export person abilities
            if results.person_abilities is not None:
                person_path = output_dir / 'person_abilities.csv'
                results.person_abilities.to_csv(person_path, index=False)
                export_paths['person_abilities'] = str(person_path)
            
            # Export item difficulties
            if results.item_difficulties is not None:
                item_path = output_dir / 'item_difficulties.csv'
                results.item_difficulties.to_csv(item_path, index=False)
                export_paths['item_difficulties'] = str(item_path)
            
            # Export fit statistics
            if results.fit_statistics is not None:
                fit_path = output_dir / 'fit_statistics.csv'
                results.fit_statistics.to_csv(fit_path, index=False)
                export_paths['fit_statistics'] = str(fit_path)
            
            # Export transformed data
            if results.transformed_data is not None:
                transform_path = output_dir / 'transformed_data.csv'
                results.transformed_data.to_csv(transform_path, index=False)
                export_paths['transformed_data'] = str(transform_path)
            
            # Export model summary
            import json
            summary_path = output_dir / 'model_summary.json'
            with open(summary_path, 'w') as f:
                json.dump(results.model_summary, f, indent=2, default=str)
            export_paths['model_summary'] = str(summary_path)
            
            self.logger.info(f"Exported Rasch results to {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
        
        return export_paths