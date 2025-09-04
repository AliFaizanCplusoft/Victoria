"""
Trait Scorer for Individual Analysis
Extracts and calculates trait scores from processed Rasch data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

# Import configuration
from config import config

@dataclass
class TraitScore:
    """Individual trait score information"""
    trait_name: str
    score: float
    percentile: float
    items_count: int
    description: str

@dataclass
class PersonTraitProfile:
    """Complete trait profile for an individual"""
    person_id: str
    traits: List[TraitScore]
    overall_score: float
    completion_rate: float
    
    def get_trait_dict(self) -> Dict[str, float]:
        """Get trait scores as dictionary"""
        return {trait.trait_name: trait.score for trait in self.traits}

class TraitScorer:
    """
    Extracts trait scores from processed Rasch data
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
        self.reverse_items = {
            'PursuePerfection', 'Procrastinate', 'StruggleDecs', 'KnowEnuf',
            'DiscourageByFailure', 'GiveUpChallenging', 'AnnoyedIfNoIdea',
            'FollowTraditions', 'ObstaclesAsBlocks', 'Resistant2ChangeAfterFail'
        }
    
    def load_trait_mapping(self, traits_file_path: str) -> Dict[str, str]:
        """Load trait mappings from the assessment file"""
        try:
            df = pd.read_csv(traits_file_path, header=None)
            
            # Parse the CSV structure: item_code, description, trait1, trait2, etc.
            trait_map = {}
            for _, row in df.iterrows():
                if len(row) >= 3:
                    item_code = row[0]
                    # Extract trait codes from columns 2 and 3
                    trait_codes = []
                    if pd.notna(row[2]) and row[2].strip():
                        trait_codes.append(row[2].strip())
                    if len(row) > 3 and pd.notna(row[3]) and row[3].strip():
                        trait_codes.append(row[3].strip())
                    
                    if trait_codes:
                        trait_map[item_code] = trait_codes
            
            self.logger.info(f"Loaded {len(trait_map)} item-trait mappings")
            return trait_map
            
        except Exception as e:
            self.logger.error(f"Error loading trait mappings: {e}")
            return {}
    
    def calculate_trait_scores(self, processed_data_path: str, 
                              traits_file_path: str) -> Dict[str, PersonTraitProfile]:
        """Calculate trait scores for all individuals"""
        try:
            # Load processed data
            df = pd.read_csv(processed_data_path, sep='\t')
            
            # Load trait mappings
            item_trait_map = self.load_trait_mapping(traits_file_path)
            
            # Group by person
            person_profiles = {}
            
            for person_id in df['Persons'].unique():
                person_data = df[df['Persons'] == person_id]
                
                # Calculate trait scores for this person
                trait_scores = self._calculate_person_traits(person_data, item_trait_map)
                
                # Calculate overall metrics
                overall_score = np.mean([ts.score for ts in trait_scores]) if trait_scores else 0.0
                completion_rate = len(person_data) / len(df['Assessment_Items'].unique())
                
                profile = PersonTraitProfile(
                    person_id=person_id,
                    traits=trait_scores,
                    overall_score=overall_score,
                    completion_rate=completion_rate
                )
                
                person_profiles[person_id] = profile
            
            self.logger.info(f"Calculated trait scores for {len(person_profiles)} individuals")
            return person_profiles
            
        except Exception as e:
            self.logger.error(f"Error calculating trait scores: {e}")
            return {}
    
    def _calculate_person_traits(self, person_data: pd.DataFrame, 
                                item_trait_map: Dict[str, List[str]]) -> List[TraitScore]:
        """Calculate trait scores for a single person"""
        trait_measures = {}
        
        # Group measures by trait
        for _, row in person_data.iterrows():
            item_code = row['Assessment_Items']
            measure = row['Measure']
            
            if item_code in item_trait_map:
                trait_codes = item_trait_map[item_code]
                
                # Handle reverse scoring
                if item_code in self.reverse_items:
                    # For reverse items, invert the measure
                    measure = -measure
                
                for trait_code in trait_codes:
                    if trait_code not in trait_measures:
                        trait_measures[trait_code] = []
                    trait_measures[trait_code].append(measure)
        
        # Calculate trait scores
        trait_scores = []
        for trait_name, trait_codes in self.trait_mappings.items():
            measures = []
            for code in trait_codes:
                if code in trait_measures:
                    measures.extend(trait_measures[code])
            
            if measures:
                # Calculate mean measure for this trait
                mean_measure = np.mean(measures)
                
                # Convert to 0-1 scale (normalize based on typical Rasch range)
                # Typical Rasch measures range from -3 to +3
                normalized_score = (mean_measure + 3) / 6
                normalized_score = max(0, min(1, normalized_score))  # Clamp to 0-1
                
                # Calculate percentile (simplified - could use population norms)
                percentile = normalized_score * 100
                
                trait_score = TraitScore(
                    trait_name=trait_name,
                    score=normalized_score,
                    percentile=percentile,
                    items_count=len(measures),
                    description=f"Based on {len(measures)} assessment items"
                )
                
                trait_scores.append(trait_score)
        
        return trait_scores
    
    def get_person_profile(self, person_id: str, 
                          person_profiles: Dict[str, PersonTraitProfile]) -> Optional[PersonTraitProfile]:
        """Get trait profile for a specific person"""
        return person_profiles.get(person_id)
    
    def create_scoring_dataframe(self, person_profiles: Dict[str, PersonTraitProfile]) -> pd.DataFrame:
        """Create a pandas DataFrame with all trait scores for Streamlit"""
        data = []
        
        for person_id, profile in person_profiles.items():
            row = {
                'person_id': person_id,
                'overall_score': profile.overall_score,
                'completion_rate': profile.completion_rate,
                'overall_percentile': profile.overall_score * 100  # Simple percentile
            }
            
            # Add trait scores
            for trait in profile.traits:
                row[trait.trait_name] = trait.score
            
            data.append(row)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.set_index('person_id')
        
        return df

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scorer = TraitScorer()
    
    # Calculate trait scores
    profiles = scorer.calculate_trait_scores(
        processed_data_path=config.get_file_path("test_output_corrected.csv"),
        traits_file_path=config.traits_file_path
    )
    
    # Create DataFrame for Streamlit
    df = scorer.create_scoring_dataframe(profiles)
    print(f"Created trait scores for {len(df)} individuals")
    print(df.head())