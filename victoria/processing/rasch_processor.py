"""
RaschPy Processor - Genuine Rasch Measurement using RaschPy RSM
Applies proper psychometric scaling using Rating Scale Model (RSM)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Try to import RaschPy - handle gracefully if not available
# Note: RaschPy must be manually installed (see INSTALL_RASCHPY.md)
# It cannot be installed via pip as it lacks setup.py/pyproject.toml
RASCHPY_AVAILABLE = False
RSM = None
RASCHPY_MODULE = None  # Store the module reference

def _try_import_raschpy():
    """Try to import RaschPy from various possible locations"""
    import sys
    import os
    import importlib.util
    
    # First, try direct import
    try:
        from RaschPy import RSM
        return True, RSM, "direct import"
    except ImportError:
        pass
    
    # Try alternative import path
    try:
        from raschpy import RSM
        return True, RSM, "alternative path (raschpy)"
    except ImportError:
        pass
    
    # Get project root (assuming rasch_processor.py is in victoria/processing/)
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    
    # RaschPy structure: D:\Victoria_Project\RaschPy\RaschPy\__init__.py
    # Try loading the module directly from file
    raschpy_init = os.path.join(project_root, 'RaschPy', 'RaschPy', '__init__.py')
    
    if os.path.exists(raschpy_init):
        try:
            spec = importlib.util.spec_from_file_location("RaschPy", raschpy_init)
            if spec and spec.loader:
                raschpy_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(raschpy_module)
                if hasattr(raschpy_module, 'RSM'):
                    # Return module, RSM class, and source path
                    return True, raschpy_module.RSM, (raschpy_init, raschpy_module)
        except Exception as e:
            logger.debug(f"Failed to load RaschPy from file: {e}")
    
    # Fallback: try adding to path
    raschpy_parent = os.path.join(project_root, 'RaschPy')
    raschpy_module_path = os.path.join(raschpy_parent, 'RaschPy')
    
    possible_paths = [
        raschpy_parent,  # D:\Victoria_Project\RaschPy (parent directory)
        raschpy_module_path,  # D:\Victoria_Project\RaschPy\RaschPy (nested)
    ]
    
    # Try adding paths and importing
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and abs_path not in sys.path:
            sys.path.insert(0, abs_path)
            try:
                # Try direct import
                from RaschPy import RSM
                return True, RSM, abs_path
            except ImportError:
                # Remove path if import failed
                if abs_path in sys.path:
                    sys.path.remove(abs_path)
                continue
    
    return False, None, None

# Attempt import at module load time
RASCHPY_AVAILABLE, RSM, import_source = _try_import_raschpy()

# Extract module reference if it's a tuple
if isinstance(import_source, tuple):
    import_source_path, RASCHPY_MODULE = import_source
    import_source = import_source_path
else:
    RASCHPY_MODULE = None

if RASCHPY_AVAILABLE:
    logger.info(f"RaschPy library imported successfully from {import_source}")
else:
    logger.warning("RaschPy library not available.")
    logger.warning("For installation instructions, see: INSTALL_RASCHPY.md")
    logger.warning("Falling back to simplified Rasch implementation")


class RaschPyProcessor:
    """
    Processes response data using genuine RaschPy RSM (Rating Scale Model)
    Implements proper psychometric measurement with item calibration and person ability estimation
    """
    
    def __init__(self, max_score: int = 4):
        """
        Initialize RaschPy processor
        
        Args:
            max_score: Maximum score for RSM (default 4 for 0-4 scale)
        """
        self.logger = logging.getLogger(__name__)
        self.max_score = max_score
        self.item_difficulties = {}
        self.person_abilities = {}
        self.fit_statistics = {}
        self.rasch_model = None
        self.raschpy_available = RASCHPY_AVAILABLE
        
        if not self.raschpy_available:
            self.logger.warning("RaschPy not available - using fallback implementation")
    
    def prepare_data_for_rasch(
        self, 
        df: pd.DataFrame, 
        assessment_columns: List[str]
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Prepare DataFrame for RaschPy analysis
        RaschPy RSM expects: persons as rows, items as columns (NOT transposed!)
        
        Args:
            df: DataFrame with persons as rows, items as columns
            assessment_columns: List of column names containing assessment responses
            
        Returns:
            Tuple of:
            - DataFrame with persons as rows, items as columns (ready for RaschPy)
            - List of person IDs
        """
        # Extract only assessment columns
        assessment_data = df[assessment_columns].copy()
        
        # Create person IDs based on row indices
        person_ids = [f"person_{i}" for i in range(len(assessment_data))]
        assessment_data.index = person_ids
        
        # Ensure all values are integers (0-4)
        assessment_data = assessment_data.astype(float).round().astype(int)
        
        # Replace any NaN with 0 (or handle missing data appropriately)
        assessment_data = assessment_data.fillna(0)
        
        # Clip values to valid range (0-4)
        assessment_data = assessment_data.clip(0, 4)
        
        self.logger.info(f"Prepared data for Rasch analysis: {len(assessment_data)} persons × {len(assessment_data.columns)} items")
        
        return assessment_data, person_ids
    
    def run_rsm_analysis(
        self, 
        data_df: pd.DataFrame,
        item_names: List[str] = None,
        person_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run RaschPy RSM analysis on prepared data
        
        Args:
            data_df: DataFrame with persons as rows, items as columns (integer scores 0-4)
            item_names: Optional list of item names (uses index if not provided)
            
        Returns:
            Dictionary containing:
            - item_difficulties: Dict mapping item names to difficulty estimates
            - person_abilities: Dict mapping person IDs to ability estimates (logit scale)
            - fit_statistics: Dict with fit statistics
        """
        self.logger.info("Starting RaschPy RSM analysis...")
        
        if not self.raschpy_available:
            return self._fallback_rasch_analysis(data_df, item_names)
        
        try:
            # Initialize RSM model
            # RaschPy RSM expects: RSM(dataframe, max_score) where dataframe has persons as rows, items as columns
            self.logger.debug(f"Initializing RSM with {len(data_df)} persons, {len(data_df.columns)} items, max_score={self.max_score}")
            self.logger.debug(f"DataFrame shape: {data_df.shape}, index: {list(data_df.index[:5])}, columns: {list(data_df.columns[:5])}")
            
            # NOTE: Having fewer rows (persons) than columns (items) is normal in this project
            # because we often run a single-person report against many items.
            
            # RaschPy typically requires multiple persons for proper calibration
            # Single person data may cause issues
            if len(data_df) == 1:
                self.logger.warning("Only 1 person in data. RaschPy calibration may fail or produce unreliable results.")
            
            self.rasch_model = RSM(data_df, max_score=self.max_score)
            
            # Calibrate items (estimate item difficulties and thresholds)
            self.logger.debug("Calling calibrate()...")
            try:
                self.rasch_model.calibrate()
                self.logger.debug("Calibration completed")
            except Exception as calib_error:
                import traceback
                self.logger.error(f"Error during calibrate(): {calib_error}")
                self.logger.error(f"Error type: {type(calib_error).__name__}")
                # Log traceback at ERROR level so it shows up in filtered logs.
                self.logger.error(f"Calibrate traceback:\n{traceback.format_exc()}")
                raise
            
            # Measure persons (estimate person abilities)
            # RaschPy RSM has person_abils() method that estimates person abilities
            # It sets self.person_abilities as a pandas Series
            if hasattr(self.rasch_model, 'person_abils'):
                try:
                    self.rasch_model.person_abils()
                except Exception as e:
                    import traceback
                    self.logger.error(f"Error calling person_abils(): {e}")
                    self.logger.error(f"person_abils traceback:\n{traceback.format_exc()}")
            elif hasattr(self.rasch_model, 'measure'):
                # Fallback to measure() if it exists
                try:
                    self.rasch_model.measure()
                except Exception as e:
                    self.logger.warning(f"Error calling measure(): {e}")
            
            # Extract item difficulties (stored in self.diffs as pandas Series)
            item_diffs = None
            try:
                self.logger.debug("Accessing diffs attribute...")
                # Check if diffs exists and what type it is
                if not hasattr(self.rasch_model, 'diffs'):
                    self.logger.warning("diffs attribute does not exist on rasch_model")
                    item_diffs = None
                else:
                    item_diffs = getattr(self.rasch_model, 'diffs', None)
                    self.logger.debug(f"diffs retrieved, type: {type(item_diffs)}")
                    
                    if item_diffs is None:
                        self.logger.warning("diffs attribute is None")
                    elif callable(item_diffs):
                        self.logger.warning("diffs is a method, not an attribute - cannot use")
                        item_diffs = None
                    elif isinstance(item_diffs, pd.Series):
                        self.logger.debug(f"diffs is a Series with {len(item_diffs)} items, index: {list(item_diffs.index[:5])}")
                    else:
                        self.logger.debug(f"diffs is {type(item_diffs)}, value sample: {str(item_diffs)[:100]}")
            except Exception as e:
                self.logger.error(f"Error accessing diffs: {e}", exc_info=True)
                import traceback
                self.logger.debug(f"Full traceback: {traceback.format_exc()}")
                item_diffs = None
            
            if item_diffs is not None:
                if isinstance(item_diffs, pd.Series):
                    item_diffs = item_diffs.to_dict()
                elif isinstance(item_diffs, dict):
                    pass  # Already a dict
                else:
                    # Try to convert
                    try:
                        item_diffs = {str(k): float(v) for k, v in item_diffs.items()}
                    except Exception:
                        item_diffs = {}
            else:
                item_diffs = {}
            
            # Extract person abilities (stored in self.person_abilities as pandas Series after person_abils())
            # Check if person_abilities exists and is an attribute (not a method)
            person_abils = None
            if hasattr(self.rasch_model, 'person_abilities'):
                person_abils_attr = getattr(self.rasch_model, 'person_abilities')
                # Check if it's actually an attribute (Series) and not a method
                if isinstance(person_abils_attr, pd.Series):
                    person_abils = person_abils_attr
                elif callable(person_abils_attr):
                    # It's a method, call it
                    person_abils = person_abils_attr()
            
            # If still None, try calling person_abils() again
            if person_abils is None and hasattr(self.rasch_model, 'person_abils'):
                try:
                    self.rasch_model.person_abils()
                    person_abils = getattr(self.rasch_model, 'person_abilities', None)
                except Exception as e:
                    self.logger.warning(f"Could not call person_abils(): {e}")
            
            # Convert person abilities to dict if it's a Series
            if isinstance(person_abils, pd.Series):
                person_abils = person_abils.to_dict()
            elif person_abils is None or not isinstance(person_abils, dict):
                # Fallback: create empty dict (will use fallback method)
                person_abils = {}
                self.logger.warning("Could not extract person abilities from RaschPy model")
            
            # Extract fit statistics if available
            fit_stats = {}
            if hasattr(self.rasch_model, 'fit_statistics'):
                fit_statistics_attr = getattr(self.rasch_model, 'fit_statistics')
                # Only use if it's actually a dict/attribute, not a method
                if not callable(fit_statistics_attr) and isinstance(fit_statistics_attr, dict):
                    fit_stats = fit_statistics_attr.copy()
            elif hasattr(self.rasch_model, 'fit_stats'):
                fit_stats_attr = getattr(self.rasch_model, 'fit_stats')
                # Only use if it's actually a dict/attribute, not a method
                if not callable(fit_stats_attr) and isinstance(fit_stats_attr, dict):
                    fit_stats = fit_stats_attr.copy()
            
            # Extract thresholds if available
            if hasattr(self.rasch_model, 'thresholds'):
                thresholds_attr = getattr(self.rasch_model, 'thresholds')
                # Check if thresholds is an attribute (array/Series) and not a method
                if not callable(thresholds_attr):
                    try:
                        if hasattr(thresholds_attr, 'tolist'):
                            fit_stats['thresholds'] = thresholds_attr.tolist()
                        else:
                            fit_stats['thresholds'] = list(thresholds_attr)
                    except Exception as e:
                        self.logger.debug(f"Could not extract thresholds: {e}")
            
            # Convert to dictionaries with proper keys
            item_names_list = item_names if item_names else list(data_df.columns)
            person_names_list = person_ids if person_ids else list(data_df.index)
            
            # Handle different return formats for item difficulties
            # Use Series index directly to match item names
            self.item_difficulties = {}
            try:
                if isinstance(item_diffs, pd.Series):
                    self.logger.debug(f"Processing item_diffs as Series with {len(item_diffs)} items")
                    for item_name in item_names_list:
                        try:
                            if item_name in item_diffs.index:
                                self.item_difficulties[item_name] = float(item_diffs.loc[item_name])
                            elif len(item_diffs) > 0:
                                # Try to match by position if index doesn't match
                                idx = item_names_list.index(item_name) if item_name in item_names_list else 0
                                if idx < len(item_diffs):
                                    self.item_difficulties[item_name] = float(item_diffs.iloc[idx])
                        except (IndexError, KeyError, TypeError) as e:
                            self.logger.debug(f"Could not map item {item_name}: {e}")
                            continue
                    # If no matches, try positional mapping
                    if not self.item_difficulties and len(item_diffs) == len(item_names_list):
                        try:
                            self.item_difficulties = {item_names_list[i]: float(item_diffs.iloc[i]) 
                                                     for i in range(len(item_names_list))}
                        except Exception as e:
                            self.logger.warning(f"Positional mapping failed: {e}")
                elif isinstance(item_diffs, dict):
                    self.item_difficulties = {str(k): float(v) for k, v in item_diffs.items()}
                elif isinstance(item_diffs, (list, np.ndarray)):
                    self.item_difficulties = {item_names_list[i]: float(item_diffs[i]) 
                                             for i in range(min(len(item_names_list), len(item_diffs)))}
                else:
                    self.logger.warning(f"Could not extract item difficulties in expected format. Type: {type(item_diffs)}")
            except Exception as e:
                self.logger.error(f"Error processing item difficulties: {e}", exc_info=True)
                self.item_difficulties = {}
            
            # Handle person abilities
            # Use Series index directly to match person IDs
            self.person_abilities = {}
            try:
                if isinstance(person_abils, pd.Series):
                    self.logger.debug(f"Processing person_abils as Series with {len(person_abils)} persons")
                    # Map using Series index (which should match person IDs from dataframe index)
                    for person_id in person_names_list:
                        try:
                            if person_id in person_abils.index:
                                self.person_abilities[person_id] = float(person_abils.loc[person_id])
                            elif len(person_abils) > 0:
                                # Fallback: use first value if index doesn't match
                                self.person_abilities[person_id] = float(person_abils.iloc[0])
                        except (IndexError, KeyError, TypeError) as e:
                            self.logger.debug(f"Could not map person {person_id}: {e}")
                            continue
                    # If no matches, try positional mapping
                    if not self.person_abilities and len(person_abils) == len(person_names_list):
                        try:
                            self.person_abilities = {person_names_list[i]: float(person_abils.iloc[i]) 
                                                    for i in range(len(person_names_list))}
                        except Exception as e:
                            self.logger.warning(f"Positional mapping failed: {e}")
                elif isinstance(person_abils, dict):
                    self.person_abilities = {str(k): float(v) for k, v in person_abils.items()}
                elif isinstance(person_abils, (list, np.ndarray)):
                    self.person_abilities = {person_names_list[i]: float(person_abils[i]) 
                                            for i in range(min(len(person_names_list), len(person_abils)))}
                else:
                    self.logger.warning(f"Could not extract person abilities in expected format. Type: {type(person_abils)}")
            except Exception as e:
                self.logger.error(f"Error processing person abilities: {e}", exc_info=True)
                self.person_abilities = {}
            
            self.fit_statistics = fit_stats if isinstance(fit_stats, dict) else {}
            
            self.logger.info(f"RaschPy RSM analysis completed:")
            self.logger.info(f"  - Items analyzed: {len(self.item_difficulties)}")
            self.logger.info(f"  - Persons analyzed: {len(self.person_abilities)}")
            if self.item_difficulties:
                diff_range = (min(self.item_difficulties.values()), max(self.item_difficulties.values()))
                self.logger.info(f"  - Item difficulty range: {diff_range[0]:.3f} to {diff_range[1]:.3f}")
            if self.person_abilities:
                abil_range = (min(self.person_abilities.values()), max(self.person_abilities.values()))
                self.logger.info(f"  - Person ability range: {abil_range[0]:.3f} to {abil_range[1]:.3f}")
            
            return {
                'item_difficulties': self.item_difficulties,
                'person_abilities': self.person_abilities,
                'fit_statistics': self.fit_statistics,
                'model': self.rasch_model
            }
            
        except Exception as e:
            import traceback
            self.logger.error(f"Error running RaschPy RSM analysis: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            # Log full traceback at ERROR level so it shows up in filtered logs
            self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
            self.logger.error("Falling back to simplified implementation")
            return self._fallback_rasch_analysis(data_df, item_names)
    
    def _fallback_rasch_analysis(
        self, 
        data_df: pd.DataFrame,
        item_names: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback Rasch analysis when RaschPy is not available
        Uses simplified estimation methods
        
        Args:
            data_df: DataFrame with items as rows, persons as columns
            item_names: Optional list of item names
            
        Returns:
            Dictionary with estimated item difficulties and person abilities
        """
        self.logger.info("Using fallback Rasch analysis (RaschPy not available)")
        
        # In this project, `data_df` is persons (rows) × items (columns)
        person_names_list = list(data_df.index)
        item_names_list = item_names if item_names else list(data_df.columns)
        
        # Estimate item difficulties using mean response across persons (simplified)
        # Items with higher mean scores are "easier" (lower difficulty).
        item_difficulties = {}
        for item_name in item_names_list:
            if item_name not in data_df.columns:
                continue
            item_scores = data_df[item_name].values
            mean_score = np.nanmean(item_scores)
            # Convert to logit scale: easier items (higher mean) → lower difficulty
            if mean_score > 0 and mean_score < self.max_score:
                prob = mean_score / self.max_score
                if prob >= 0.99:
                    prob = 0.99
                elif prob <= 0.01:
                    prob = 0.01
                difficulty = -np.log(prob / (1 - prob))  # Negative because easier = lower difficulty
            else:
                difficulty = 0.0
            item_difficulties[item_name] = float(difficulty)
        
        # Estimate person abilities using mean response across items (simplified)
        # Persons with higher mean scores have higher ability.
        person_abilities = {}
        for person_name in person_names_list:
            if person_name not in data_df.index:
                continue
            person_scores = data_df.loc[person_name].values
            mean_score = np.nanmean(person_scores)
            if mean_score > 0 and mean_score < self.max_score:
                prob = mean_score / self.max_score
                if prob >= 0.99:
                    prob = 0.99
                elif prob <= 0.01:
                    prob = 0.01
                ability = np.log(prob / (1 - prob))
            else:
                ability = 0.0
            person_abilities[person_name] = float(ability)
        
        self.item_difficulties = item_difficulties
        self.person_abilities = person_abilities
        self.fit_statistics = {}
        
        self.logger.info(f"Fallback analysis completed:")
        self.logger.info(f"  - Items: {len(item_difficulties)}")
        self.logger.info(f"  - Persons: {len(person_abilities)}")
        
        return {
            'item_difficulties': item_difficulties,
            'person_abilities': person_abilities,
            'fit_statistics': {},
            'model': None
        }
    
    def convert_logit_to_0_1_scale(self, logit_value: float) -> float:
        """
        Convert logit scale value to 0-1 scale for compatibility
        
        Args:
            logit_value: Value on logit scale
            
        Returns:
            Value on 0-1 scale
        """
        # Use logistic function: p = exp(logit) / (1 + exp(logit))
        # Then scale to 0-1 range
        try:
            exp_logit = np.exp(logit_value)
            prob = exp_logit / (1 + exp_logit)
            return float(np.clip(prob, 0.0, 1.0))
        except (OverflowError, ValueError):
            # Handle extreme values
            if logit_value > 10:
                return 1.0
            elif logit_value < -10:
                return 0.0
            else:
                return 0.5
    
    def get_item_difficulties(self) -> Dict[str, float]:
        """Get calibrated item difficulties"""
        return self.item_difficulties.copy()
    
    def get_person_abilities(self) -> Dict[str, float]:
        """Get person ability estimates (logit scale)"""
        return self.person_abilities.copy()
    
    def get_person_abilities_0_1(self) -> Dict[str, float]:
        """Get person ability estimates converted to 0-1 scale"""
        return {
            person_id: self.convert_logit_to_0_1_scale(ability)
            for person_id, ability in self.person_abilities.items()
        }
    
    def get_fit_statistics(self) -> Dict[str, Any]:
        """Get fit statistics from Rasch analysis"""
        return self.fit_statistics.copy()
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of Rasch analysis"""
        return {
            'items_analyzed': len(self.item_difficulties),
            'persons_analyzed': len(self.person_abilities),
            'item_difficulty_range': (
                min(self.item_difficulties.values()) if self.item_difficulties else 0,
                max(self.item_difficulties.values()) if self.item_difficulties else 0
            ),
            'person_ability_range': (
                min(self.person_abilities.values()) if self.person_abilities else 0,
                max(self.person_abilities.values()) if self.person_abilities else 0
            ),
            'fit_statistics': self.fit_statistics,
            'raschpy_available': self.raschpy_available
        }
