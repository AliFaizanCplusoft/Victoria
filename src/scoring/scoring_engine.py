"""
Scoring Engine for Psychometric Assessment System

Calculates individual and construct-level scores from processed assessment data.
Implements various scoring algorithms and generates assessment scores.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
from dataclasses import dataclass
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Try multiple import strategies to handle different project structures
try:
    from ..data.item_mapper import ItemMapper
    from ..data.data_ingestion import process_assessment_file, PsychometricDataProcessor
except ImportError:
    try:
        from data.item_mapper import ItemMapper
        from data.data_ingestion import process_assessment_file, PsychometricDataProcessor
    except ImportError:
        try:
            from data.item_mapper import ItemMapper
            from data.data_ingestion import process_assessment_file, PsychometricDataProcessor
        except ImportError:
            print("Warning: Could not import ItemMapper. Using fallback.")
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
                def is_reverse_scored(self, item):
                    return item in self.reverse_items
                def get_all_items(self):
                    return list(self.item_construct_map.keys())
            def process_assessment_file(filepath):
                print(f"Warning: Using fallback data processing for {filepath}")
                return type('Result', (), {
                    'success': False,
                    'errors': ['ItemMapper and data_ingestion modules not available']
                })()
            class PsychometricDataProcessor:
                def __init__(self, item_mapper=None, validator=None):
                    self.item_mapper = item_mapper or ItemMapper()
                def process_file(self, filepath):
                    print(f"Warning: Using fallback processing for {filepath}")
                    return type('Result', (), {
                        'success': False,
                        'errors': ['Full data processing not available']
                    })()

@dataclass
class ConstructScore:
    construct_id: str
    construct_name: str
    score: float
    percentile: Optional[float] = None

@dataclass
class PersonScore:
    person_id: str
    overall_score: float
    overall_percentile: Optional[float]
    construct_scores: List[ConstructScore]
    item_scores: Dict[str, float]
    completion_rate: float
    reliability_scores: Dict[str, float]
    percentile_ranks: Dict[str, float]
    raw_responses: Dict[str, float]

@dataclass
class ScoringResult:
    success: bool
    person_scores: List[PersonScore]
    group_statistics: Dict[str, Dict]
    construct_reliabilities: Dict[str, float]
    scoring_metadata: Dict[str, any]
    errors: List[str]
    warnings: List[str]

class PsychometricScoringEngine:

    def __init__(self, item_mapper: Optional[ItemMapper] = None,
                 norm_data: Optional[Dict] = None,
                 use_rasch_scoring: bool = True):
        self.logger = logging.getLogger(__name__)
        self.item_mapper = item_mapper or ItemMapper()
        self.norm_data = norm_data or self._load_default_norms()
        self.min_items_per_construct = 3
        self.min_completion_rate = 0.8
        self.scoring_methods = ['raw', 'standardized', 'percentile', 'sten', 'rasch']
        self._use_rasch_scoring = use_rasch_scoring
        self.logger.info(f"PsychometricScoringEngine initialized (Rasch scoring: {use_rasch_scoring})")

    def _load_default_norms(self) -> dict:
        return {}

    def _calculate_construct_reliabilities(self, wide_data):
        reliabilities = {}
        for construct_code in self.item_mapper.get_all_constructs():
            items = self.item_mapper.get_items_for_construct(construct_code)
            available_items = [item for item in items if item in wide_data.columns]
            if len(available_items) >= 2:
                construct_data = wide_data[available_items].dropna()
                if not construct_data.empty:
                    alpha = self._cronbach_alpha(construct_data)
                    reliabilities[construct_code] = alpha
        return reliabilities

    def _calculate_group_statistics(self, person_scores):
        if not person_scores:
            return {}
        overall_scores = [ps.overall_score for ps in person_scores]
        group_stats = {
            'overall': {
                'mean': np.mean(overall_scores),
                'std': np.std(overall_scores),
                'min': np.min(overall_scores),
                'max': np.max(overall_scores),
                'median': np.median(overall_scores),
                'count': len(overall_scores)
            }
        }

        # Convert list of ConstructScore to dict
        constructs = set()
        person_construct_maps = []
        for ps in person_scores:
            # Convert list to dict for each person
            construct_dict = {cs.construct_id: cs.score for cs in ps.construct_scores}
            person_construct_maps.append(construct_dict)
            constructs.update(construct_dict.keys())

        for construct in constructs:
            values = []
            for construct_map in person_construct_maps:
                if construct in construct_map:
                    values.append(construct_map[construct])
            if values:
                group_stats[construct] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'median': np.median(values),
                    'count': len(values)
                }

        return group_stats

    def _cronbach_alpha(self, data):
        if data.empty or data.shape[1] < 2:
            return 0.0
        k = data.shape[1]
        item_variances = data.var(axis=0, ddof=1)
        total_score = data.sum(axis=1)
        total_variance = total_score.var(ddof=1)
        if total_variance == 0:
            return 0.0
        alpha = (k / (k - 1)) * (1 - (item_variances.sum() / total_variance))
        return max(0.0, min(1.0, alpha))

    def score_assessment_data(self, data: pd.DataFrame,
                              scoring_method: str = 'standardized',
                              calculate_percentiles: bool = True) -> ScoringResult:
        self.logger.info(f"Starting scoring with method: {scoring_method}")
        errors = []
        warnings = []
        person_scores = []
        try:
            if not self._validate_scoring_data(data):
                errors.append("Invalid data format for scoring")
                return ScoringResult(
                    success=False, person_scores=[], group_statistics={},
                    construct_reliabilities={}, scoring_metadata={},
                    errors=errors, warnings=warnings
                )
            wide_data = self._prepare_scoring_data(data)
            self.logger.info(f"Prepared data: {wide_data.shape[0]} persons × {wide_data.shape[1]} items")
            for person_id in wide_data.index:
                person_data = wide_data.loc[person_id]
                try:
                    person_score = self._calculate_person_scores(
                        person_id, person_data, scoring_method, calculate_percentiles
                    )
                    person_scores.append(person_score)
                except Exception as e:
                    warning = f"Could not score person {person_id}: {str(e)}"
                    warnings.append(warning)
                    self.logger.warning(warning)
            group_stats = self._calculate_group_statistics(person_scores)
            construct_reliabilities = self._calculate_construct_reliabilities(wide_data)
            scoring_metadata = {
                'scoring_method': scoring_method,
                'total_persons': len(person_scores),
                'total_constructs': len(self.item_mapper.get_all_constructs()),
                'completion_threshold': self.min_completion_rate,
                'norm_data_available': self.norm_data is not None
            }
            self.logger.info(f"Scoring completed: {len(person_scores)} persons scored")
            return ScoringResult(
                success=True,
                person_scores=person_scores,
                group_statistics=group_stats,
                construct_reliabilities=construct_reliabilities,
                scoring_metadata=scoring_metadata,
                errors=errors,
                warnings=warnings
            )
        except Exception as e:
            error = f"Scoring failed: {str(e)}"
            errors.append(error)
            self.logger.error(error, exc_info=True)
            return ScoringResult(
                success=False, person_scores=[], group_statistics={},
                construct_reliabilities={}, scoring_metadata={},
                errors=errors, warnings=warnings
            )

    def _validate_scoring_data(self, data: pd.DataFrame) -> bool:
        required_columns = ['Measure', 'Persons', 'Assessment_Items']
        for col in required_columns:
            if col not in data.columns:
                self.logger.error(f"Missing required column: {col}")
                return False
        return len(data) > 0

    def _prepare_scoring_data(self, data: pd.DataFrame) -> pd.DataFrame:
        duplicates = data.duplicated(subset=['Persons', 'Assessment_Items'], keep=False)
        if duplicates.any():
            self.logger.warning(f"Found {duplicates.sum()} duplicate person-item combinations")
            data_clean = data.drop_duplicates(subset=['Persons', 'Assessment_Items'], keep='last')
            self.logger.info(f"Removed duplicates: {len(data)} -> {len(data_clean)} records")
        else:
            data_clean = data
        try:
            wide_data = data_clean.pivot(
                index='Persons',
                columns='Assessment_Items',
                values='Measure'
            )
        except ValueError as e:
            self.logger.warning(f"Pivot failed, using pivot_table: {e}")
            wide_data = data_clean.pivot_table(
                index='Persons',
                columns='Assessment_Items',
                values='Measure',
                aggfunc='mean'
            )
        mapped_items = [item for item in wide_data.columns
                        if self.item_mapper.get_construct_for_item(item) is not None]
        if mapped_items:
            wide_data = wide_data[mapped_items]
        else:
            self.logger.warning("No mapped items found in the data")
        reverse_items = [item for item in wide_data.columns
                         if self.item_mapper.is_reverse_scored(item)]
        if reverse_items:
            min_val = wide_data[reverse_items].min().min()
            max_val = wide_data[reverse_items].max().max()
            wide_data[reverse_items] = (max_val + min_val) - wide_data[reverse_items]
            self.logger.info(f"Applied reverse scoring to {len(reverse_items)} items")
        return wide_data

    def _rasch_score(self, values, construct_code):
        """
        Calculate Rasch-style measure from raw responses.
        
        This implements a simplified Rasch model transformation:
        - Converts raw scores to logit scale
        - Adjusts for item difficulty if available
        - Returns standardized measure
        """
        if not values:
            return 0.0
        
        # Convert to numpy array for easier handling
        responses = np.array(values)
        
        # Calculate raw score (sum of responses)
        raw_score = np.sum(responses)
        max_possible = len(responses) * np.max(responses)
        
        # Avoid perfect scores for logit calculation
        if raw_score == 0:
            raw_score = 0.5
        elif raw_score == max_possible:
            raw_score = max_possible - 0.5
        
        # Calculate proportion correct
        proportion = raw_score / max_possible
        
        # Convert to logit (Rasch measure)
        logit = np.log(proportion / (1 - proportion))
        
        # Apply item difficulty adjustments if available
        if self.norm_data and construct_code in self.norm_data:
            item_difficulties = self.norm_data[construct_code].get('item_difficulties', [])
            if item_difficulties and len(item_difficulties) == len(responses):
                # Adjust for item difficulty
                difficulty_adjustment = np.mean(item_difficulties)
                logit = logit - difficulty_adjustment
        
        return logit

    def _standardize_score(self, values, construct_code):
        """Convert raw values to standardized T-scores (mean=50, sd=10)."""
        if not values:
            return 50.0
        
        # Use Rasch scoring if this is measurement data
        if hasattr(self, '_use_rasch_scoring') and self._use_rasch_scoring:
            rasch_measure = self._rasch_score(values, construct_code)
            # Convert Rasch logit to T-score scale
            t_score = 50 + (rasch_measure * 10)
            return max(10, min(90, t_score))  # Constrain to reasonable range
        
        # Standard z-score transformation
        mean_score = np.mean(values)
        if self.norm_data and construct_code in self.norm_data:
            norm_mean = self.norm_data[construct_code].get('mean', mean_score)
            norm_std = self.norm_data[construct_code].get('std', 1.0)
        else:
            norm_mean = mean_score
            norm_std = 1.0
        z_score = (mean_score - norm_mean) / norm_std if norm_std > 0 else 0.0
        t_score = 50 + (z_score * 10)
        return t_score

    def _calculate_alpha_reliability(self, scores):
        scores = np.array(scores)
        if scores.ndim == 1:
            return 1.0
        k = scores.shape[1]
        if k <= 1:
            return 1.0
        item_variances = scores.var(axis=0, ddof=1)
        total_score = scores.sum(axis=1)
        total_variance = total_score.var(ddof=1)
        if total_variance == 0:
            return 1.0
        alpha = (k / (k - 1)) * (1 - (item_variances.sum() / total_variance))
        return round(alpha, 4)

    def _calculate_person_scores(self, person_id: str, person_data: pd.Series,
                                 scoring_method: str, calculate_percentiles: bool) -> PersonScore:
        raw_responses = person_data.dropna().to_dict()
        total_possible_items = len(self.item_mapper.get_all_items())
        if total_possible_items == 0:
            total_possible_items = len(person_data)
        completed_items = len(raw_responses)
        completion_rate = completed_items / total_possible_items if total_possible_items > 0 else 0
        construct_scores_raw = {}
        reliability_scores = {}
        for construct_code, _ in self.item_mapper.get_all_constructs().items():
            construct_items = self.item_mapper.get_items_for_construct(construct_code)
            available_items = [item for item in construct_items
                               if item in raw_responses and not pd.isna(raw_responses[item])]
            if len(available_items) >= self.min_items_per_construct:
                construct_values = [raw_responses[item] for item in available_items]
                if scoring_method == 'raw':
                    construct_score = np.mean(construct_values)
                elif scoring_method == 'standardized':
                    construct_score = self._standardize_score(construct_values, construct_code)
                elif scoring_method == 'percentile':
                    construct_score = self._percentile_score(construct_values, construct_code)
                else:
                    construct_score = np.mean(construct_values)
                construct_scores_raw[construct_code] = construct_score
                if len(available_items) > 2:
                    reliability_scores[construct_code] = self._calculate_alpha_reliability(
                        construct_values
                    )
        percentile_ranks = {}
        if calculate_percentiles and self.norm_data:
            percentile_ranks = self._calculate_percentile_ranks(construct_scores_raw)
        construct_scores = []
        for code, score in construct_scores_raw.items():
            construct_scores.append(
                ConstructScore(
                    construct_id=code,
                    construct_name=self.item_mapper.get_construct_name(code),
                    score=score,
                    percentile=percentile_ranks.get(code)
                )
            )
        if construct_scores:
            overall_score = np.mean([c.score for c in construct_scores])
        else:
            overall_score = np.mean(list(raw_responses.values())) if raw_responses else 0.0
        overall_percentile = None
        if calculate_percentiles and overall_score and self.norm_data:
            overall_percentile = 50.0
        return PersonScore(
            person_id=person_id,
            overall_score=overall_score,
            overall_percentile=overall_percentile,
            construct_scores=construct_scores,
            item_scores=raw_responses,
            completion_rate=completion_rate,
            reliability_scores=reliability_scores,
            percentile_ranks=percentile_ranks,
            raw_responses=raw_responses
        )

    def _percentile_score(self, values, construct_code):
        """Calculate percentile score based on values and norm data."""
        if not values:
            return 50.0
        
        mean_score = np.mean(values)
        
        # If we have norm data for this construct, use it
        if self.norm_data and construct_code in self.norm_data:
            norm_data = self.norm_data[construct_code]
            if 'values' in norm_data:
                # Calculate percentile based on norm data
                norm_values = norm_data['values']
                percentile = (np.sum(norm_values <= mean_score) / len(norm_values)) * 100
                return max(1, min(99, percentile))
        
        # Fallback: assume normal distribution with mean=50, std=10
        # Convert to z-score and then percentile
        z_score = (mean_score - 50) / 10
        # Approximate percentile using z-score (simplified)
        percentile = 50 + (z_score * 20)  # Map z-score to percentile range
        return max(1, min(99, percentile))

    def _calculate_percentile_ranks(self, construct_scores_raw: Dict[str, float]) -> Dict[str, float]:
        """Calculate percentile ranks for each construct score."""
        percentile_ranks = {}
        
        for construct_code, score in construct_scores_raw.items():
            # Use the same logic as _percentile_score but for individual constructs
            if self.norm_data and construct_code in self.norm_data:
                norm_data = self.norm_data[construct_code]
                if 'values' in norm_data:
                    norm_values = norm_data['values']
                    percentile = (np.sum(norm_values <= score) / len(norm_values)) * 100
                    percentile_ranks[construct_code] = max(1, min(99, percentile))
                else:
                    percentile_ranks[construct_code] = 50.0
            else:
                # Fallback calculation using z-score approximation
                z_score = (score - 50) / 10
                percentile = 50 + (z_score * 20)
                percentile_ranks[construct_code] = max(1, min(99, percentile))
        
        return percentile_ranks

    def calculate_individual_scores(self, person_id: str, transformed_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate individual scores from Rasch-transformed data.
        
        Args:
            person_id: Person identifier
            transformed_data: Rasch-transformed data
            
        Returns:
            Dictionary with individual scoring results
        """
        try:
            # Filter data for this person
            person_data = transformed_data[transformed_data['Persons'] == person_id]
            
            if person_data.empty:
                self.logger.warning(f"No data found for person {person_id}")
                return {}
            
            # Calculate construct scores using Rasch measures
            construct_scores = {}
            
            # Group by construct (need to map items to constructs)
            for construct_code, construct_name in self.item_mapper.get_all_constructs().items():
                construct_items = self.item_mapper.get_items_for_construct(construct_code)
                
                # Find person's responses for this construct
                construct_measures = []
                for _, row in person_data.iterrows():
                    if row['Assessment_Items'] in construct_items:
                        construct_measures.append(row['Measure'])
                
                if construct_measures:
                    # Calculate construct score from Rasch measures
                    construct_score = np.mean(construct_measures)
                    
                    # Calculate percentile (simplified - could use norm data)
                    percentile = self._calculate_rasch_percentile(construct_score)
                    
                    construct_scores[construct_code] = {
                        'score': construct_score,
                        'percentile': percentile,
                        'construct_name': construct_name
                    }
            
            # Calculate overall score
            if construct_scores:
                overall_score = np.mean([cs['score'] for cs in construct_scores.values()])
                overall_percentile = self._calculate_rasch_percentile(overall_score)
            else:
                overall_score = 0.0
                overall_percentile = 50.0
            
            return {
                'overall_score': overall_score,
                'overall_percentile': overall_percentile,
                'construct_scores': construct_scores
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating individual scores: {e}")
            return {}

    def _calculate_rasch_percentile(self, rasch_measure: float) -> float:
        """
        Convert Rasch measure to percentile rank.
        
        Args:
            rasch_measure: Rasch logit measure
            
        Returns:
            Percentile rank (0-100)
        """
        # Simple conversion from logit to percentile
        # This is a simplified approach - more sophisticated norm data could be used
        
        # Assume typical Rasch measures range from -3 to +3 logits
        # Convert to 0-100 percentile scale
        normalized = (rasch_measure + 3) / 6  # Normalize to 0-1 range
        percentile = normalized * 100
        
        # Constrain to reasonable percentile range
        return max(1, min(99, percentile))
