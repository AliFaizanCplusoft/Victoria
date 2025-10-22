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
            "Emotional Intelligence": "EI"
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
    
    def get_archetype_correlation_data(self) -> Dict[str, List[float]]:
        """Get correlation data for heatmap visualization"""
        return {
            'Adaptive Intelligence': [0.35, 0.32, 0.94, 0.36, 0.28, 0.88, 0.32, 0.83, 0.84, 0.34, 0.33, 0.34],
            'Ambitious Drive': [0.85, 0.32, 0.32, 0.32, 0.15, 0.72, 0.33, 0.33, 0.32, 0.32, 0.32, 0.32],
            'Collaborative Responsibility': [0.35, 0.82, 0.32, 0.39, 0.26, 0.26, 0.33, 0.32, 0.84, 0.33, 0.84, 0.45],
            'Resilient Leadership': [0.85, 0.82, 0.32, 0.38, 0.28, 0.38, 0.32, 0.83, 0.32, 0.84, 0.83, 0.34],
            'Strategic Innovation': [0.35, 0.32, 0.32, 0.88, 0.45, 0.85, 0.33, 0.84, 0.34, 0.83, 0.34, 0.28]
        }
