"""
Enhanced Trait Scorer for Individual Analysis
Integrates with Vertria's Entrepreneurial Archetypes
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

from victoria.core.models import TraitScore, PersonTraitProfile, ArchetypeScore
from victoria.core.enums import ArchetypeType, TraitType, ScoreLevel
from victoria.config.settings import config, archetype_config, trait_config

class TraitScorer:
    """
    Enhanced trait scorer that integrates with Vertria's archetype framework
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define trait mappings based on the assessment structure
        self.trait_mappings = {
            'Risk Taking': ['RT'],
            'Innovation': ['IO'], 
            'Leadership': ['E(', 'RB'],  # E( seems to be leadership-related
            'Resilience': ['RG', 'F'],  # RG = Resilience/Grit, F = Failure handling
            'Accountability': ['A'],     # A = Accountability
            'Decision Making': ['DM'],   # DM = Decision Making
            'Adaptability': ['AD'],      # AD = Adaptability
            'Continuous Learning': ['CT'], # CT = Continuous Learning/Thinking
            'Passion/Drive': ['DA'],     # DA = Drive/Ambition
            'Problem Solving': ['PS'],   # PS = Problem Solving
            'Emotional Intelligence': ['EI'] # EI = Emotional Intelligence
        }
        
        # Reverse scored items (lower raw score = higher trait)
        # Using question text instead of codes
        self.reverse_items = {
            'I pursue perfection', 'I procrastinate', 'I struggle making decisions', 
            'I need to learn more to move forward', 'I am discouraged by failure',
            'I give up when something is challenging', 'I get annoyed if I don\'t come up with an idea',
            'I follow traditions', 'I view obstacles as blockers', 
            'I am resistant to change after experiencing a setback'
        }
    
    def load_trait_mapping(self, traits_file_path: str) -> Dict[str, List[str]]:
        """Load trait mappings from the assessment file"""
        try:
            df = pd.read_csv(traits_file_path, header=None)
            
            # Parse the CSV structure: 
            # Column 0: item_code, Column 1: description, 
            # Column 2-3: trait codes, Column 5: actual question text
            trait_map = {}
            for _, row in df.iterrows():
                if len(row) >= 6:
                    # Use the actual question text from column 5
                    question_text = row[5] if pd.notna(row[5]) else row[1]
                    
                    # Extract trait codes from columns 2 and 3
                    trait_codes = []
                    if pd.notna(row[2]) and str(row[2]).strip():
                        trait_codes.append(str(row[2]).strip())
                    if len(row) > 3 and pd.notna(row[3]) and str(row[3]).strip():
                        trait_codes.append(str(row[3]).strip())
                    
                    if trait_codes and pd.notna(question_text):
                        trait_map[str(question_text).strip()] = trait_codes
            
            self.logger.info(f"Loaded {len(trait_map)} item-trait mappings")
            return trait_map
            
        except Exception as e:
            self.logger.error(f"Error loading trait mappings: {e}")
            return {}
    
    def calculate_trait_scores(self, processed_data_path: str, 
                              traits_file_path: str) -> Dict[str, PersonTraitProfile]:
        """Calculate trait scores for all individuals with archetype analysis"""
        try:
            # Load processed data
            df = pd.read_csv(processed_data_path, sep='\t')
            
            # Load trait mappings
            trait_map = self.load_trait_mapping(traits_file_path)
            
            profiles = {}
            person_columns = [col for col in df.columns if col != 'Item']
            
            for person_id in person_columns:
                try:
                    profile = self._calculate_individual_profile(df, person_id, trait_map)
                    if profile:
                        # Calculate archetype scores
                        profile = self._calculate_archetype_scores(profile)
                        profiles[person_id] = profile
                        
                except Exception as e:
                    self.logger.error(f"Error processing {person_id}: {e}")
                    continue
            
            self.logger.info(f"Successfully processed {len(profiles)} individual profiles")
            return profiles
            
        except Exception as e:
            self.logger.error(f"Error calculating trait scores: {e}")
            return {}
    
    def _calculate_individual_profile(self, df: pd.DataFrame, person_id: str, 
                                    trait_map: Dict[str, str]) -> Optional[PersonTraitProfile]:
        """Calculate trait profile for an individual"""
        try:
            person_data = df.set_index('Item')[person_id]
            
            # Calculate trait scores
            trait_scores = []
            total_items = 0
            valid_responses = 0
            
            for trait_name in trait_config.CORE_TRAITS:
                trait_codes = self.trait_mappings.get(trait_name, [])
                
                # Find items for this trait
                trait_items = []
                for question_text, item_traits in trait_map.items():
                    if any(trait_code in item_traits for trait_code in trait_codes):
                        if question_text in person_data.index:
                            trait_items.append(question_text)
                
                if trait_items:
                    # Calculate trait score
                    trait_score = self._calculate_trait_score(person_data, trait_items, trait_name)
                    if trait_score:
                        trait_scores.append(trait_score)
                        valid_responses += trait_score.items_count
                
                total_items += len(trait_items)
            
            if not trait_scores:
                return None
            
            # Calculate overall metrics
            overall_score = np.mean([ts.score for ts in trait_scores])
            completion_rate = (valid_responses / total_items) if total_items > 0 else 0
            
            return PersonTraitProfile(
                person_id=person_id,
                traits=trait_scores,
                overall_score=overall_score,
                completion_rate=completion_rate
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating profile for {person_id}: {e}")
            return None
    
    def _calculate_trait_score(self, person_data: pd.Series, trait_items: List[str], 
                             trait_name: str) -> Optional[TraitScore]:
        """Calculate score for a specific trait"""
        try:
            scores = []
            for item in trait_items:
                if item in person_data.index and pd.notna(person_data[item]):
                    score = float(person_data[item])
                    
                    # Apply reverse scoring if needed
                    if item in self.reverse_items:
                        score = -score  # Reverse the score
                    
                    scores.append(score)
            
            if not scores:
                return None
            
            # Calculate trait metrics
            trait_score = np.mean(scores)
            
            # Calculate percentile (simplified - would need population data for accurate percentiles)
            # For now, using z-score transformation
            percentile = self._score_to_percentile(trait_score)
            
            return TraitScore(
                trait_name=trait_name,
                score=trait_score,
                percentile=percentile,
                items_count=len(scores),
                description=f"Score based on {len(scores)} assessment items",
                confidence=min(1.0, len(scores) / 10)  # Confidence based on number of items
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating trait score for {trait_name}: {e}")
            return None
    
    def _score_to_percentile(self, score: float) -> float:
        """Convert trait score to percentile (simplified)"""
        # This is a simplified conversion - in production you'd use population norms
        # Assuming scores are roughly normally distributed around 0 with std dev of 1
        try:
            from scipy.stats import norm
            percentile = norm.cdf(score) * 100
            return max(1, min(99, percentile))  # Keep within 1-99 range
        except ImportError:
            # Fallback if scipy not available
            return max(1, min(99, 50 + score * 20))  # Simple linear transformation
        except:
            # Other errors - use fallback
            return max(1, min(99, 50 + score * 20))
    
    def _calculate_archetype_scores(self, profile: PersonTraitProfile) -> PersonTraitProfile:
        """Calculate archetype matches for the profile"""
        trait_dict = profile.trait_dict
        archetype_scores = []
        
        for archetype_key, archetype_info in archetype_config.ARCHETYPES.items():
            archetype_type = ArchetypeType(archetype_key)
            core_traits = archetype_info['core_traits']
            
            # Calculate archetype score based on core traits
            trait_scores = []
            matching_traits = []
            
            for trait_name in core_traits:
                if trait_name in trait_dict:
                    trait_score = trait_dict[trait_name]
                    trait_scores.append(trait_score.score)
                    matching_traits.append(trait_name)
            
            if trait_scores:
                archetype_score = np.mean(trait_scores)
                
                # Calculate confidence based on trait coverage and scores
                coverage = len(matching_traits) / len(core_traits)
                score_consistency = 1 - (np.std(trait_scores) / (np.mean(np.abs(trait_scores)) + 0.1))
                confidence = coverage * score_consistency
                
                archetype_scores.append(ArchetypeScore(
                    archetype=archetype_type,
                    score=archetype_score,
                    confidence=confidence,
                    matching_traits=matching_traits,
                    description=archetype_info['description'],
                    characteristics=archetype_info['characteristics']
                ))
        
        # Sort by score and assign primary/secondary
        archetype_scores.sort(key=lambda x: x.score, reverse=True)
        
        if archetype_scores:
            profile.primary_archetype = archetype_scores[0]
            profile.secondary_archetypes = archetype_scores[1:3]  # Top 2 secondary matches
            
            # Generate recommendations based on archetype
            profile.recommendations = self._generate_archetype_recommendations(profile.primary_archetype)
            profile.growth_areas = self._identify_growth_areas(profile)
        
        return profile
    
    def _generate_archetype_recommendations(self, archetype: ArchetypeScore) -> List[str]:
        """Generate personalized recommendations based on primary archetype"""
        recommendations_map = {
            ArchetypeType.STRATEGIC_INNOVATION: [
                "Focus on developing structured innovation processes",
                "Consider roles in strategic planning and R&D",
                "Build skills in market analysis and trend forecasting"
            ],
            ArchetypeType.RESILIENT_LEADERSHIP: [
                "Develop conflict resolution and mediation skills", 
                "Consider leadership roles in challenging environments",
                "Focus on team building and crisis management training"
            ],
            ArchetypeType.COLLABORATIVE_RESPONSIBILITY: [
                "Explore servant leadership methodologies",
                "Consider roles in team development and mentoring",
                "Focus on building trust and accountability systems"
            ],
            ArchetypeType.AMBITIOUS_DRIVE: [
                "Set challenging long-term goals with clear milestones",
                "Consider entrepreneurial ventures or leadership roles",
                "Focus on persistence and goal achievement strategies"
            ],
            ArchetypeType.ADAPTIVE_INTELLIGENCE: [
                "Develop analytical and problem-solving frameworks",
                "Consider roles in consulting or strategic analysis", 
                "Focus on emotional intelligence and customer empathy"
            ]
        }
        
        return recommendations_map.get(archetype.archetype, [
            "Continue developing your unique strengths",
            "Seek opportunities that align with your natural talents",
            "Consider leadership development programs"
        ])
    
    def _identify_growth_areas(self, profile: PersonTraitProfile) -> List[str]:
        """Identify areas for development based on lower-scoring traits"""
        growth_areas = []
        
        # Find traits in the lower percentiles
        low_traits = [trait for trait in profile.traits if trait.percentile < 30]
        
        for trait in low_traits:
            if trait.trait_name == "Leadership":
                growth_areas.append("Develop leadership and team management skills")
            elif trait.trait_name == "Innovation": 
                growth_areas.append("Cultivate creative thinking and innovation practices")
            elif trait.trait_name == "Risk Taking":
                growth_areas.append("Build comfort with calculated risk-taking")
            elif trait.trait_name == "Emotional Intelligence":
                growth_areas.append("Enhance emotional awareness and interpersonal skills")
            # Add more specific recommendations as needed
        
        return growth_areas[:3]  # Limit to top 3 growth areas