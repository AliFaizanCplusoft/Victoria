"""
Trait Scorer - Step 4-5: Question-to-Trait Mapping and Trait Score Calculation
Calculates 17 trait scores from Rasch measures
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TraitScorer:
    """
    Calculates trait scores from Rasch measures using question-trait mapping
    """
    
    def __init__(self):
        """Initialize trait scorer with 17 traits"""
        self.trait_names = [
            'IN', 'DM', 'RB', 'N', 'CT', 'PS', 'A',
            'EI', 'C', 'TB', 'SL', 'AD', 'F', 'RG', 'IO', 'DA', 'RT'
        ]
        
        self.trait_descriptions = {
            'IN': 'Introverted vs Extroverted',
            'DM': 'Decision Making',
            'RB': 'Relationship Building', 
            'N': 'Negotiation',
            'CT': 'Critical Thinking',
            'PS': 'Problem Solving',
            'A': 'Accountability',
            'EI': 'Emotional Intelligence',
            'C': 'Conflict Management',
            'TB': 'Team Building',
            'SL': 'Servant Leadership',
            'AD': 'Adaptability',
            'F': 'Approach to Failure',
            'RG': 'Resilience and Grit',
            'IO': 'Innovation Orientation',
            'DA': 'Drive and Ambition',
            'RT': 'Risk Taking'
        }
        
        # Question to trait mapping (simplified for core functionality)
        self.question_trait_mapping = self._load_question_mapping()
    
    def calculate_trait_scores(self, rasch_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate trait scores for all persons
        
        Args:
            rasch_data: Dictionary containing Rasch measures for each person
            
        Returns:
            Dictionary containing trait scores for each person
        """
        trait_profiles = {}
        
        for person_id, person_measures in rasch_data.items():
            trait_scores = {}
            
            for trait in self.trait_names:
                # Find questions that map to this trait
                trait_measures = []
                
                for question, measure in person_measures.items():
                    if self._question_maps_to_trait(question, trait):
                        trait_measures.append(measure)
                
                if trait_measures:
                    # Calculate mean measure for this trait
                    mean_measure = np.mean(trait_measures)
                    
                    # Normalize to 0-1 scale
                    # Rasch measures typically range -3 to +3
                    normalized_score = (mean_measure + 3) / 6
                    normalized_score = max(0, min(1, normalized_score))  # Clamp to 0-1
                    
                    trait_scores[trait] = normalized_score
                else:
                    # Default score if no questions map to this trait
                    trait_scores[trait] = 0.5
            
            trait_profiles[person_id] = {
                'trait_scores': trait_scores,
                'person_id': person_id
            }
        
        return trait_profiles
    
    def _load_question_mapping(self) -> Dict[str, List[str]]:
        """Load question to trait mapping"""
        # Simplified mapping - in production, this would load from CSV
        mapping = {}
        
        # Sample mappings (would be loaded from question_trait_mapping.csv)
        sample_mappings = {
            'I enjoy new challenges': ['RT', 'DA'],
            'I come up with good ideas': ['IO', 'CT'],
            'I pursue perfection': ['PS', 'CT'],
            'I work well when things aren\'t clearly defined': ['AD', 'RT'],
            'I make decisions that involve risk': ['RT', 'DM'],
            'I am adventurous': ['RT', 'DA'],
            'I am comfortable making decisions in uncertain environments': ['DM', 'AD'],
            'I am driven by my passion to innovate': ['IO', 'DA'],
            'I communicate my ideas': ['IO', 'SL'],
            'I follow my intuition': ['DM', 'RT'],
            'I am determined to reach my goals': ['RG', 'DA'],
            'I focus deeply on one goal at a time': ['PS', 'CT'],
            'I seek informed input from others': ['SL', 'TB'],
            'I go beyond my comfort zone': ['RT', 'AD'],
            'I work through difficult situations rather than avoid them': ['RG', 'PS'],
            'I act with intention, even when the outcome is unclear': ['DM', 'RT'],
            'I ask questions': ['CT', 'N'],
            'I see unexpected changes as a chance to improve, not a setback': ['AD', 'F'],
            'I stay committed, even if results take longer than expected': ['RG', 'PS'],
            'If the path I\'m on isn\'t working, I\'m quick to test a new one': ['AD', 'IO'],
            'Even when priorities shift, I follow through on what I promised': ['A', 'RG'],
            'I keep my promises': ['A', 'SL'],
            'I handle frustration well': ['EI', 'RG'],
            'Failure teaches me': ['F', 'CT'],
            'I admit my mistakes even when it might affect how others see me': ['A', 'EI'],
            'I am comfortable with failure': ['F', 'RT'],
            'I accept responsibility for errors': ['A', 'SL'],
            'I update my perspective even when it means letting go of familiar strategies': ['AD', 'IO'],
            'I adapt my stances': ['AD', 'N'],
            'I welcome feedback': ['EI', 'SL'],
            'I contribute without needing my name attached': ['SL', 'TB'],
            'I focus on the needs of my team': ['SL', 'TB'],
            'I want my legacy to elevate others': ['SL', 'TB'],
            'I am a good listener': ['EI', 'SL'],
            'I speak up at meetings': ['IO', 'SL'],
            'I value input from everyone equally': ['SL', 'TB'],
            'I am driven by long-term success': ['DA', 'RG'],
            'I want the whole team to succeed': ['TB', 'SL'],
            'Trust is essential for innovation': ['TB', 'IO'],
            'I own my role in outcomes, even when they fall short': ['A', 'SL'],
            'I am confident in my ability to assemble highly productive teams': ['TB', 'SL'],
            'I know how to develop strong team performance': ['TB', 'SL'],
            'I trust individuals with their responsibilities': ['TB', 'SL'],
            'I provide excellent guidance to teams that I lead': ['SL', 'TB'],
            'I love to see my team get positive recognition': ['SL', 'TB'],
            'I take credit for the accomplishments of my team': ['SL', 'TB'],
            'When constructive conflict arises in my team, I am comfortable with it': ['C', 'TB'],
            'I value relationships': ['RB', 'TB'],
            'I can adapt to different team dynamics': ['AD', 'TB'],
            'I can identify good talent': ['TB', 'CT'],
            'I am an open communicator': ['SL', 'IO'],
            'I am comfortable being vulnerable': ['EI', 'SL'],
            'I believe teams develop better solutions than individuals': ['TB', 'IO'],
            'I create safe team environments': ['TB', 'SL'],
            'I am dependable': ['A', 'RG'],
            'Calculated risk-taking is important': ['RT', 'DM'],
            'I am comfortable engaging in constructive conflict': ['C', 'TB'],
            'I can differentiate between constructive and destructive conflict': ['C', 'CT'],
            'I address destructive conflicts directly': ['C', 'SL'],
            'Conflict leads to better outcomes': ['C', 'TB'],
            'I want to avoid conflict': ['C', 'EI'],
            'I can separate the person from the issue': ['C', 'EI'],
            'I am good at empathizing with others': ['EI', 'SL'],
            'I can adapt communication based on the needs of others': ['EI', 'SL'],
            'I am comfortable delivering sensitive feedback': ['EI', 'SL'],
            'I listen before speaking': ['EI', 'SL'],
            'I remain composed when navigating disagreements': ['EI', 'C'],
            'I can discern emotional clues': ['EI', 'CT'],
            'I can discern emotional triggers in conflicts': ['EI', 'C'],
            'I self-reflect to improve emotional awareness': ['EI', 'CT'],
            'I am comfortable owning the responsibility for outcomes': ['A', 'SL'],
            'I am committed to following through on every promise': ['A', 'RG'],
            'I acknowledge my role in successes and failures': ['A', 'EI'],
            'I am proactive in communicating any potential issues': ['A', 'SL'],
            'I can say no when something is unrealistic': ['A', 'DM'],
            'I meet deadlines': ['A', 'RG'],
            'I learn from my mistakes': ['F', 'CT'],
            'I feel comfortable receiving feedback from my colleagues': ['EI', 'SL'],
            'I believe I have the best solution to a problem': ['PS', 'CT'],
            'I act without thinking': ['RT', 'DM'],
            'I take time to fully understand complex issues before acting': ['CT', 'DM'],
            'I make decisions as soon as an issue arises': ['DM', 'RT'],
            'I break problems into steps to solve the problem': ['PS', 'CT'],
            'I run through possible scenarios in advance of an issue': ['CT', 'PS'],
            'I examine multiple perspectives before making a decision': ['CT', 'DM'],
            'I consider assumptions that drive my decisions': ['CT', 'DM'],
            'I am self-aware': ['EI', 'CT'],
            'I articulate my biases': ['EI', 'CT'],
            'I ask questions': ['CT', 'N'],
            'I put myself in uncomfortable situations': ['RT', 'AD'],
            'I am creative': ['IO', 'CT'],
            'I prepare before meeting someone for the first time': ['RB', 'SL'],
            'I run through multiple scenarios when considering a problem': ['CT', 'PS'],
            'I adjust my approach in negotiations without losing sight of what matters most': ['N', 'AD'],
            'I can adapt my message to audience': ['SL', 'IO'],
            'I can see someone else\'s perspective': ['EI', 'N'],
            'I compromise': ['N', 'SL'],
            'I am collaborative': ['TB', 'SL'],
            'I am adaptive person': ['AD', 'RT'],
            'I am composed': ['EI', 'RG'],
            'I am open to diverse perspectives': ['AD', 'EI'],
            'I think before speaking': ['CT', 'EI'],
            'I am influenced': ['N', 'EI'],
            'I nurture connections': ['RB', 'TB'],
            'I use people as a means to an end': ['RB', 'TB'],
            'I listen actively': ['EI', 'SL'],
            'I am easily distracted': ['CT', 'PS'],
            'I am open to feedback': ['EI', 'SL'],
            'I move past small talk': ['RB', 'IO'],
            'I build rapport with anyone': ['RB', 'SL'],
            'I maintain relationships': ['RB', 'TB'],
            'Relationships are transactional': ['RB', 'TB'],
            'I make decisions with missing information': ['DM', 'RT'],
            'I make choices intentionally': ['DM', 'CT'],
            'My decisions are objective': ['DM', 'CT'],
            'I consider my biases': ['CT', 'EI'],
            'I am quick to act, appreciating on-the-spot problem-solving': ['PS', 'RT'],
            'I am resourceful': ['PS', 'IO'],
            'I consider the consequences of my actions': ['CT', 'DM'],
            'I have an existing framework for making decisions': ['DM', 'CT'],
            'I am focused when working independently, using deep analysis to guide my decisions': ['CT', 'PS'],
            'I am comfortable sharing ideas in smaller, more personal settings': ['IO', 'SL'],
            'I am observant': ['CT', 'EI'],
            'I am an active listener': ['EI', 'SL'],
            'I reflect': ['CT', 'EI'],
            'Social situations drain my energy': ['IN', 'EI'],
            'I am energized by meeting new people': ['IN', 'RB'],
            'I am inclined to speak up and pitch ideas in group settings or large events': ['IN', 'IO'],
            'I am driven by social engagement': ['IN', 'RB'],
            'I jump into conversations': ['IN', 'IO'],
            'I actively participate': ['IN', 'TB']
        }
        
        return sample_mappings
    
    def _question_maps_to_trait(self, question: str, trait: str) -> bool:
        """Check if a question maps to a specific trait"""
        if question in self.question_trait_mapping:
            return trait in self.question_trait_mapping[question]
        return False
