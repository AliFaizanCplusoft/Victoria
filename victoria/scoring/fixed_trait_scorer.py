#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed Trait Scorer
Calculates trait scores using Rasch measurement principles
Uses genuine Rasch measures instead of simple arithmetic mean
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional
from ..mapping.question_trait_mapper import QuestionTraitMapper

logger = logging.getLogger(__name__)


class FixedTraitScorer:
    """
    Calculates trait scores using Rasch measurement
    Aggregates item-level Rasch measures to trait-level scores
    """
    
    def __init__(self):
        self.mapper = QuestionTraitMapper()
        self.question_mapping = self.mapper.get_question_mapping()
        self.likert_mapping = self.mapper.get_likert_mapping()
        self.trait_names = self.mapper.get_trait_names()
        
        # Rasch analysis results (set by set_rasch_results)
        self.rasch_item_difficulties = {}
        self.rasch_person_abilities = {}
        self.use_rasch = False
        
        logger.info(f"Initialized FixedTraitScorer with {len(self.trait_names)} traits")
        logger.info(f"Trait names: {', '.join(self.trait_names)}")
    
    def set_rasch_results(
        self, 
        item_difficulties: Dict[str, float],
        person_abilities: Dict[str, float]
    ):
        """
        Set Rasch analysis results for use in trait scoring
        
        Args:
            item_difficulties: Dictionary mapping item names to difficulty estimates
            person_abilities: Dictionary mapping person IDs to ability estimates (logit scale)
        """
        self.rasch_item_difficulties = item_difficulties
        self.rasch_person_abilities = person_abilities
        self.use_rasch = True
        logger.info(f"Rasch results set: {len(item_difficulties)} items, {len(person_abilities)} persons")
    
    def calculate_trait_scores(
        self, 
        df: pd.DataFrame,
        rasch_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate trait scores for all persons in the dataframe
        
        Args:
            df: DataFrame with Likert scale responses
            rasch_results: Optional Rasch analysis results dictionary
            
        Returns:
            Dictionary of person profiles with trait scores
        """
        logger.info(f"Calculating trait scores for {len(df)} persons")
        
        # Set Rasch results if provided
        if rasch_results:
            item_diffs = rasch_results.get('item_difficulties', {})
            person_abils = rasch_results.get('person_abilities', {})
            if item_diffs and person_abils:
                self.set_rasch_results(item_diffs, person_abils)
        
        profiles = {}
        
        # Process each person (row)
        for idx, row in df.iterrows():
            person_id = f"person_{idx}"
            person_scores = self._calculate_person_traits(row, person_id)
            profiles[person_id] = person_scores
            
            logger.debug(f"Calculated scores for {person_id}: {len(person_scores)} traits")
        
        # Log summary statistics
        self._log_scoring_summary(profiles)
        
        return profiles
    
    def _calculate_person_traits(self, person_data: pd.Series, person_id: str) -> Dict[str, float]:
        """
        Calculate trait scores for a single person using Rasch measures
        
        Args:
            person_data: Person's response data
            person_id: Person identifier
            
        Returns:
            Dictionary of trait scores (0-1 scale)
        """
        trait_scores = {}
        
        if self.use_rasch and person_id in self.rasch_person_abilities:
            # Use Rasch measures: aggregate item-level abilities to trait-level
            trait_scores = self._calculate_traits_from_rasch(person_data, person_id)
        else:
            # Fallback to arithmetic mean (legacy method)
            trait_scores = self._calculate_traits_from_mean(person_data, person_id)
        
        return trait_scores
    
    def _calculate_traits_from_rasch(
        self, 
        person_data: pd.Series, 
        person_id: str
    ) -> Dict[str, float]:
        """
        Calculate trait scores using Rasch measures (Option B: Item-level Rasch, Trait Aggregation)
        
        For each trait:
        1. Get all items/questions belonging to that trait
        2. Calculate item-specific person ability estimates from actual responses
        3. Average the abilities (or use weighted average based on item difficulties)
        4. Convert logit scale to 0-1 scale
        
        Args:
            person_data: Person's response data
            person_id: Person identifier
            
        Returns:
            Dictionary of trait scores (0-1 scale)
        """
        trait_scores = {}
        overall_person_ability_logit = self.rasch_person_abilities.get(person_id, 0.0)
        
        for trait in self.trait_names:
            # Find all questions that measure this trait
            trait_questions = self.mapper.get_questions_for_trait(trait)
            trait_item_scores = []
            trait_item_weights = []
            
            for question in trait_questions:
                # Get item difficulty for this question
                item_difficulty = self.rasch_item_difficulties.get(question)
                
                # Get person's actual response to this item
                if question in person_data.index:
                    response_value = person_data[question]
                    
                    # Convert response to numeric if needed
                    if isinstance(response_value, str):
                        response_numeric = self.mapper.map_likert_to_numeric(response_value)
                    elif pd.isna(response_value):
                        continue  # Skip missing responses
                    else:
                        response_numeric = float(response_value)
                    
                    # Calculate item-specific person ability estimate
                    # Using Rasch model: P(X=1) = exp(ability - difficulty) / (1 + exp(ability - difficulty))
                    # For polytomous (0-4 scale), we estimate ability from response
                    # Response value (0-1) represents probability of endorsement
                    # Convert to logit: logit = log(p / (1-p))
                    # Then: ability = logit + difficulty
                    
                    if item_difficulty is not None:
                        # Convert response (0-1) to logit scale
                        # Clamp to avoid log(0) or log(inf)
                        p = np.clip(response_numeric, 0.01, 0.99)
                        response_logit = np.log(p / (1 - p))
                        
                        # Estimate person ability for this item: ability = response_logit + difficulty
                        # This gives us item-specific ability estimate
                        item_specific_ability = response_logit + item_difficulty
                        
                        trait_item_scores.append(item_specific_ability)
                        
                        # Weight by item difficulty (more difficult items weighted more)
                        # Items with higher absolute difficulty get more weight
                        weight = abs(item_difficulty) + 1.0  # Add 1 to avoid zero weights
                        trait_item_weights.append(weight)
                    else:
                        # Fallback: use overall person ability if item difficulty not available
                        trait_item_scores.append(overall_person_ability_logit)
                        trait_item_weights.append(1.0)
            
            if trait_item_scores:
                # Weighted average of item-specific abilities
                if trait_item_weights and len(trait_item_weights) == len(trait_item_scores):
                    weights_array = np.array(trait_item_weights)
                    abilities_array = np.array(trait_item_scores)
                    weighted_ability = np.average(abilities_array, weights=weights_array)
                else:
                    weighted_ability = np.mean(trait_item_scores)
                
                # Convert logit to 0-1 scale
                trait_score = self._convert_logit_to_0_1(weighted_ability)
                trait_scores[trait] = trait_score
            else:
                # No items found for this trait - use fallback to arithmetic mean
                logger.warning(f"No Rasch measures found for trait {trait} for person {person_id}, using fallback")
                trait_scores[trait] = self._calculate_trait_fallback_mean(person_data, trait)
        
        return trait_scores
    
    def _calculate_trait_fallback_mean(self, person_data: pd.Series, trait: str) -> float:
        """
        Fallback method: calculate trait score using arithmetic mean
        Used when Rasch measures are not available for a trait
        """
        trait_questions = self.mapper.get_questions_for_trait(trait)
        trait_values = []
        
        for question in trait_questions:
            if question in person_data.index:
                value = self.mapper.map_likert_to_numeric(person_data[question])
                if not pd.isna(value):
                    trait_values.append(value)
        
        if trait_values:
            return sum(trait_values) / len(trait_values)
        else:
            return 0.5  # Default neutral score
    
    def _calculate_traits_from_mean(
        self, 
        person_data: pd.Series, 
        person_id: str
    ) -> Dict[str, float]:
        """
        Calculate trait scores using arithmetic mean (legacy fallback method)
        
        Args:
            person_data: Person's response data
            person_id: Person identifier
            
        Returns:
            Dictionary of trait scores
        """
        trait_scores = {}
        
        for trait in self.trait_names:
            # Find all questions that measure this trait
            trait_questions = self.mapper.get_questions_for_trait(trait)
            trait_values = []
            
            for question in trait_questions:
                if question in person_data.index:
                    value = self.mapper.map_likert_to_numeric(person_data[question])
                    trait_values.append(value)
            
            if trait_values:
                # Calculate average score for this trait
                avg_score = sum(trait_values) / len(trait_values)
                trait_scores[trait] = avg_score
            else:
                trait_scores[trait] = 0.5  # Default neutral score
                logger.warning(f"No measures found for trait {trait} for person {person_id}")
        
        return trait_scores
    
    def _convert_logit_to_0_1(self, logit_value: float) -> float:
        """
        Convert logit scale value to 0-1 scale for compatibility
        
        Args:
            logit_value: Value on logit scale
            
        Returns:
            Value on 0-1 scale
        """
        try:
            # Use logistic function: p = exp(logit) / (1 + exp(logit))
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
    
    def _log_scoring_summary(self, profiles: Dict[str, Dict[str, float]]):
        """Log summary statistics of the scoring process"""
        if not profiles:
            logger.warning("No profiles generated")
            return
        
        # Calculate statistics
        all_scores = []
        for profile in profiles.values():
            all_scores.extend(profile.values())
        
        if all_scores:
            min_score = min(all_scores)
            max_score = max(all_scores)
            avg_score = sum(all_scores) / len(all_scores)
            std_dev = pd.Series(all_scores).std()
            
            logger.info(f"Trait scoring completed:")
            logger.info(f"  - Persons processed: {len(profiles)}")
            logger.info(f"  - Traits per person: {len(self.trait_names)}")
            logger.info(f"  - Total scores calculated: {len(all_scores)}")
            logger.info(f"  - Score range: {min_score:.3f} to {max_score:.3f}")
            logger.info(f"  - Average score: {avg_score:.3f}")
            logger.info(f"  - Standard deviation: {std_dev:.3f}")
            
            # Check if we have meaningful variation
            if std_dev > 0.01:
                logger.info("SUCCESS: Trait scores show meaningful variation!")
            else:
                logger.warning("WARNING: Trait scores show little variation")
    
    def get_trait_names(self) -> List[str]:
        """Get list of trait names"""
        return self.trait_names
    
    def get_mapping_stats(self) -> Dict[str, Any]:
        """Get mapping statistics"""
        return self.mapper.validate_mapping()

