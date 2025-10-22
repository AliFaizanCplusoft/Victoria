#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed Trait Scorer
Calculates trait scores using the direct question-trait mapping approach
"""

import pandas as pd
import logging
from typing import Dict, List, Any
from ..mapping.question_trait_mapper import QuestionTraitMapper

logger = logging.getLogger(__name__)

class FixedTraitScorer:
    """Calculates trait scores using fixed mapping approach"""
    
    def __init__(self):
        self.mapper = QuestionTraitMapper()
        self.question_mapping = self.mapper.get_question_mapping()
        self.likert_mapping = self.mapper.get_likert_mapping()
        self.trait_names = self.mapper.get_trait_names()
        
        logger.info(f"Initialized FixedTraitScorer with {len(self.trait_names)} traits")
        logger.info(f"Trait names: {', '.join(self.trait_names)}")
    
    def calculate_trait_scores(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Calculate trait scores for all persons in the dataframe
        
        Args:
            df: DataFrame with Likert scale responses
            
        Returns:
            Dictionary of person profiles with trait scores
        """
        logger.info(f"Calculating trait scores for {len(df)} persons")
        
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
        Calculate trait scores for a single person
        
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

