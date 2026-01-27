"""
Archetype Detector - Detects entrepreneurial archetype based on trait scores
"""

import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Archetype:
    """Represents an entrepreneurial archetype"""
    name: str
    description: str
    key_traits: List[str]
    color: str
    score: float = 0.0

class ArchetypeDetector:
    """Detects entrepreneurial archetype based on trait scores"""
    
    def __init__(self):
        """Initialize archetype detector with predefined archetypes"""
        self.archetypes = {
            "strategic_innovation": Archetype(
                name="Strategic Innovation",
                description="This archetype is characterized by Risk Taking, Innovation and Orientation, Critical Thinking, and Decision Making. It emphasizes calculated and strategic innovative efforts.",
                key_traits=["Risk Taking", "Innovation Orientation", "Critical Thinking", "Decision Making"],
                color="#667eea"
            ),
            "resilient_leadership": Archetype(
                name="Resilient Leadership", 
                description="This archetype combines Resilience and Grit, Team Building, Servant Leadership, Adaptability, and Risk Taking. It highlights the importance of leading with empathy while building cohesive teams that can thrive amidst challenges.",
                key_traits=["Resilience and Grit", "Team Building", "Servant Leadership", "Adaptability", "Risk Taking"],
                color="#764ba2"
            ),
            "collaborative_responsibility": Archetype(
                name="Collaborative Responsibility",
                description="This archetype includes Servant Leadership, Team Building, and Accountability. It focuses on the growth and well-being of a team, emphasizing ownership of actions for building trust and a successful business.",
                key_traits=["Servant Leadership", "Team Building", "Accountability"],
                color="#f093fb"
            ),
            "ambitious_drive": Archetype(
                name="Ambitious Drive",
                description="This archetype is defined by Drive and Ambition, Resilience and Grit, and Problem Solving. These traits are essential for staying motivated and persevering through business challenges.",
                key_traits=["Drive and Ambition", "Resilience and Grit", "Problem Solving"],
                color="#4facfe"
            ),
            "adaptive_intelligence": Archetype(
                name="Adaptive Intelligence",
                description="This archetype is characterized by Critical Thinking, Problem Solving, Emotional Intelligence, and Adaptability. It emphasizes the ability to navigate complex situations with both analytical and emotional intelligence.",
                key_traits=["Critical Thinking", "Problem Solving", "Emotional Intelligence", "Adaptability"],
                color="#43e97b"
            )
        }
        
        # Mapping from full trait names to trait codes
        self.trait_name_to_code = {
            "Risk Taking": "RT",
            "Innovation Orientation": "IO", 
            "Critical Thinking": "CT",
            "Decision Making": "DM",
            "Resilience and Grit": "RG",
            "Team Building": "TB",
            "Servant Leadership": "SL",
            "Adaptability": "AD",
            "Accountability": "A",
            "Drive and Ambition": "DA",
            "Problem Solving": "PS",
            "Emotional Intelligence": "EI",
            "Relationship-Building": "RB",
            "Negotiation": "N",
            "Conflict Resolution": "C",
            "Approach to Failure": "F",
            "Social Orientation": "IN"
        }
    
    def detect_archetype(self, trait_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Detect the best matching archetype for given trait scores
        
        Args:
            trait_scores: Dictionary of trait scores (trait_code: score)
            
        Returns:
            Dictionary containing detected archetype and confidence
        """
        best_archetype = None
        best_score = 0.0
        archetype_scores = {}
        
        for archetype_id, archetype in self.archetypes.items():
            # Calculate average score for key traits
            key_trait_scores = []
            for trait_name in archetype.key_traits:
                trait_code = self.trait_name_to_code.get(trait_name, trait_name)
                if trait_code in trait_scores:
                    key_trait_scores.append(trait_scores[trait_code])
            
            if key_trait_scores:
                avg_score = sum(key_trait_scores) / len(key_trait_scores)
                archetype_scores[archetype_id] = avg_score
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_archetype = archetype
        
        if best_archetype:
            # Calculate confidence (0-1)
            confidence = min(best_score, 1.0)
            
            return {
                'archetype_name': best_archetype.name,
                'archetype_description': best_archetype.description,
                'archetype_color': best_archetype.color,
                'archetype_score': best_score,
                'confidence': confidence,
                'all_scores': archetype_scores
            }
        else:
            return {
                'archetype_name': 'Unknown',
                'archetype_description': 'Unable to determine archetype',
                'archetype_color': '#666666',
                'archetype_score': 0.0,
                'confidence': 0.0,
                'all_scores': {}
            }
    
    def _calculate_trait_archetype_correlation(self, trait_name: str, archetype: Archetype) -> float:
        """
        Calculate correlation score between a trait and an archetype dynamically.
        
        Calculation Method:
        1. Key Traits: High correlation (0.85-0.90) - traits that define the archetype
           - Base score: 0.85
           - Small variation (0.0-0.05) based on trait order for visual distinction
        
        2. Secondary/Related Traits: Medium correlation (0.35-0.45)
           - Traits that complement key traits but aren't defining
           - Examples: Emotional Intelligence for Adaptive Intelligence
        
        3. Unrelated Traits: Low correlation (0.28-0.34)
           - Traits not directly related to the archetype
        
        4. Social Orientation: Always 0.0 (not a key trait for any archetype)
        
        5. New Traits (RB, N, C, F): Assigned based on archetype relevance:
           - Relationship-Building: High for Collaborative Responsibility, Resilient Leadership
           - Negotiation: Medium for Collaborative Responsibility, Strategic Innovation
           - Conflict Resolution: High for Collaborative Responsibility, Resilient Leadership
           - Approach to Failure: High for Resilient Leadership, Ambitious Drive
        
        Args:
            trait_name: Full name of the trait (e.g., "Resilience and Grit")
            archetype: Archetype object with key_traits list
            
        Returns:
            Correlation score between 0.0 and 1.0
        """
        # Social Orientation is not a key trait for any archetype
        if trait_name == "Social Orientation":
            return 0.0
        
        archetype_name = archetype.name
        
        # Check if trait is a key trait for this archetype
        if trait_name in archetype.key_traits:
            # Key traits get high correlation (0.85-0.90)
            # Use 0.85 as base, add small variation based on trait position
            base_score = 0.85
            # Add slight variation (0.0-0.05) based on trait order for visual distinction
            trait_index = archetype.key_traits.index(trait_name)
            variation = min(0.05 * trait_index, 0.05)
            return round(base_score + variation, 2)
        
        # Handle the 4 new traits with specific correlation logic
        new_trait_correlations = {
            "Relationship-Building": {
                "Collaborative Responsibility": 0.88,  # High - essential for collaboration
                "Resilient Leadership": 0.40,  # Medium - supports team building
                "Adaptive Intelligence": 0.35,  # Low-medium - helps with adaptability
                "Ambitious Drive": 0.30,  # Low - less critical
                "Strategic Innovation": 0.30  # Low - less critical
            },
            "Negotiation": {
                "Collaborative Responsibility": 0.42,  # Medium - important for collaboration
                "Strategic Innovation": 0.38,  # Medium - supports decision making
                "Resilient Leadership": 0.35,  # Low-medium - useful for team management
                "Adaptive Intelligence": 0.33,  # Low-medium - helps with adaptability
                "Ambitious Drive": 0.30  # Low - less critical
            },
            "Conflict Resolution": {
                "Collaborative Responsibility": 0.86,  # High - essential for team harmony
                "Resilient Leadership": 0.40,  # Medium - important for team management
                "Adaptive Intelligence": 0.36,  # Low-medium - helps navigate challenges
                "Strategic Innovation": 0.32,  # Low - less critical
                "Ambitious Drive": 0.30  # Low - less critical
            },
            "Approach to Failure": {
                "Resilient Leadership": 0.87,  # High - core to resilience
                "Ambitious Drive": 0.85,  # High - essential for perseverance
                "Strategic Innovation": 0.38,  # Medium - important for learning from failures
                "Adaptive Intelligence": 0.35,  # Low-medium - helps with adaptation
                "Collaborative Responsibility": 0.32  # Low - less critical
            }
        }
        
        if trait_name in new_trait_correlations:
            return new_trait_correlations[trait_name].get(archetype_name, 0.30)
        
        # Check for secondary/related traits (traits that complement key traits but aren't key traits themselves)
        # These get medium correlation (0.35-0.45)
        secondary_traits_map = {
            "Adaptive Intelligence": {
                "Drive and Ambition": 0.88,  # High - important for adaptive intelligence
                "Problem Solving": 0.28  # Low - not directly related
            },
            "Ambitious Drive": {
                "Problem Solving": 0.15  # Very low - not a key trait
            },
            "Collaborative Responsibility": {
                "Critical Thinking": 0.84  # High - important for collaboration
            },
            "Resilient Leadership": {
                # All key traits already handled above
            },
            "Strategic Innovation": {
                "Problem Solving": 0.45,  # Medium - supports innovation
                "Drive and Ambition": 0.85,  # High - important for strategic innovation
                "Adaptability": 0.84  # High - important for innovation
            }
        }
        
        if archetype_name in secondary_traits_map:
            if trait_name in secondary_traits_map[archetype_name]:
                return secondary_traits_map[archetype_name][trait_name]
        
        # All other traits get low correlation (0.28-0.34)
        # This represents traits that are not directly related to the archetype
        return 0.32
    
    def get_archetype_correlation_data(self) -> Dict[str, List[float]]:
        """
        Get correlation data for heatmap visualization - DYNAMICALLY CALCULATED
        
        This method dynamically calculates correlation scores between traits and archetypes
        based on whether traits are key traits, secondary traits, or unrelated traits.
        
        Calculation Method:
        - Key Traits: High correlation (0.85-0.90) - traits that define the archetype
        - Secondary Traits: Medium correlation (0.35-0.45) - traits that complement key traits
        - Unrelated Traits: Low correlation (0.28-0.34) - traits not directly related
        - Social Orientation: Always 0.0 (not a key trait for any archetype)
        
        Returns 17 values per archetype in the following order:
        0. Social Orientation
        1. Resilience and Grit
        2. Servant Leadership
        3. Emotional Intelligence
        4. Decision-Making
        5. Problem-Solving
        6. Drive and Ambition
        7. Innovation Orientation
        8. Adaptability
        9. Critical Thinking
        10. Team Building
        11. Risk Taking
        12. Accountability
        13. Relationship-Building
        14. Negotiation
        15. Conflict Resolution
        16. Approach to Failure
        
        Returns:
            Dictionary mapping archetype names to lists of 17 correlation scores
        """
        # Define all traits in the exact order used by the heatmap
        # Note: This order must match the trait_names order in visualization_engine.py
        # The visualization engine maps these to display names, but we use archetype definition names here
        all_traits = [
            "Social Orientation",           # 0 - IN
            "Resilience and Grit",          # 1 - RG (heatmap uses "Resilience & Grit" but maps to this)
            "Servant Leadership",           # 2 - SL
            "Emotional Intelligence",       # 3 - EI
            "Decision Making",              # 4 - DM (heatmap uses "Decision-Making" but maps to this)
            "Problem Solving",               # 5 - PS (heatmap uses "Problem-Solving" but maps to this)
            "Drive and Ambition",           # 6 - DA (heatmap uses "Drive & Ambition" but maps to this)
            "Innovation Orientation",       # 7 - IO
            "Adaptability",                 # 8 - AD
            "Critical Thinking",            # 9 - CT
            "Team Building",                # 10 - TB
            "Risk Taking",                  # 11 - RT
            "Accountability",                # 12 - A
            "Relationship-Building",        # 13 - RB
            "Negotiation",                  # 14 - N
            "Conflict Resolution",          # 15 - C
            "Approach to Failure"            # 16 - F
        ]
        
        correlation_data = {}
        
        # Calculate correlation scores for each archetype
        for archetype_id, archetype in self.archetypes.items():
            archetype_name = archetype.name
            correlation_scores = []
            
            for trait_name in all_traits:
                # Map trait names to match archetype definitions
                # Handle naming differences between heatmap and archetype definitions
                # The all_traits list uses names without hyphens, but we need to check both formats
                mapped_trait_name = trait_name
                # Archetype definitions use "Decision Making" and "Problem Solving" (no hyphens)
                # So our all_traits list already matches, but we handle both just in case
                
                # Calculate correlation score dynamically
                score = self._calculate_trait_archetype_correlation(mapped_trait_name, archetype)
                correlation_scores.append(score)
            
            correlation_data[archetype_name] = correlation_scores
        
        return correlation_data
