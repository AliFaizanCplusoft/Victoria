#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Question-Trait Mapping Module
Handles the mapping between Likert scale questions and entrepreneurial traits
"""

import pandas as pd
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class QuestionTraitMapper:
    """Maps Likert scale questions to entrepreneurial traits"""
    
    def __init__(self):
        self.question_trait_mapping = self._create_direct_mapping()
        self.likert_mapping = self._create_likert_mapping()
    
    def _create_direct_mapping(self) -> Dict[str, List[str]]:
        """Create direct mapping from question text to traits"""
        return {
            # Innovation & Orientation (IO)
            'I enjoy new challenges': ['IO'],
            'I come up with good ideas': ['IO'], 
            'I am driven by my passion to innovate': ['IO'],
            'I communicate my ideas': ['IO'],
            'I am adventurous': ['IO'],
            'I follow my intuition': ['IO'],
            'I go beyond my comfort zone': ['IO'],
            'I am creative': ['IO'],
            
            # Drive & Ambition (DA)
            'I pursue perfection': ['DA'],
            'I am determined to reach my goals': ['DA'],
            'I focus deeply on one goal at a time': ['DA'],
            'I am driven by long-term success': ['DA'],
            'I am confident in my ability to assemble highly productive teams': ['DA'],
            'I know how to develop strong team performance': ['DA'],
            'I am dependable': ['DA'],
            'I am resourceful': ['DA'],
            
            # Adaptability (AD)
            'I work well when things aren\'t clearly defined': ['AD'],
            'I am comfortable making decisions in uncertain environments': ['AD'],
            'I see unexpected changes as a chance to improve, not a setback': ['AD'],
            'I adapt my stances': ['AD'],
            'I can adapt to different team dynamics': ['AD'],
            'I am adaptive person': ['AD'],
            'I can adapt my message to audience': ['AD'],
            'I adjust my approach in negotiations without losing sight of what matters most': ['AD'],
            
            # Risk Taking (RT)
            'I make decisions that involve risk': ['RT'],
            'I act with intention, even when the outcome is unclear': ['RT'],
            'I make decisions with missing information': ['RT'],
            'I am quick to act, appreciating on-the-spot problem-solving': ['RT'],
            'Calculated risk-taking is important': ['RT'],
            
            # Decision Making (DM)
            'I struggle making decisions': ['DM'],
            'I seek informed input from others': ['DM'],
            'I make decisions as soon as an issue arises': ['DM'],
            'I break problems into steps to solve the problem': ['DM'],
            'I run through possible scenarios in advance of an issue': ['DM'],
            'I examine multiple perspectives before making a decision': ['DM'],
            'I consider assumptions that drive my decisions': ['DM'],
            'I have an existing framework for making decisions': ['DM'],
            'I am focused when working independently, using deep analysis to guide my decisions': ['DM'],
            
            # Critical Thinking (CT)
            'There is always more to learn': ['CT'],
            'I need to learn more to move forward': ['CT'],
            'I take time to fully understand complex issues before acting': ['CT'],
            'I run through multiple scenarios when considering a problem': ['CT'],
            'I think before speaking': ['CT'],
            'I consider the consequences of my actions': ['CT'],
            
            # Problem Solving (PS)
            'I break problems into steps to solve the problem': ['PS'],
            'I run through possible scenarios in advance of an issue': ['PS'],
            'I examine multiple perspectives before making a decision': ['PS'],
            'I am resourceful': ['PS'],
            'I am focused when working independently, using deep analysis to guide my decisions': ['PS'],
            
            # Accountability (A)
            'I complete tasks I am not passionate about': ['A'],
            'I procrastinate': ['A'],
            'I am comfortable owning the responsibility for outcomes': ['A'],
            'I am committed to following through on every promise': ['A'],
            'I acknowledge my role in successes and failures': ['A'],
            'I am proactive in communicating any potential issues': ['A'],
            'I can say no when something is unrealistic': ['A'],
            'I meet deadlines': ['A'],
            'I learn from my mistakes': ['A'],
            'I own my role in outcomes, even when they fall short': ['A'],
            
            # Emotional Intelligence (EI)
            'I can discern emotional clues': ['EI'],
            'I can discern emotional triggers in conflicts': ['EI'],
            'I self-reflect to improve emotional awareness': ['EI'],
            'I am comfortable being vulnerable': ['EI'],
            'I am an open communicator': ['EI'],
            'I am comfortable delivering sensitive feedback': ['EI'],
            'I listen before speaking': ['EI'],
            'I remain composed when navigating disagreements': ['EI'],
            
            # Conflict Management (C)
            'I am comfortable engaging in constructive conflict': ['C'],
            'I can differentiate between constructive and destructive conflict': ['C'],
            'I address destructive conflicts directly': ['C'],
            'Conflict leads to better outcomes': ['C'],
            'I want to avoid conflict': ['C'],
            'I can separate the person from the issue': ['C'],
            'I am good at empathizing with others': ['C'],
            'I can adapt communication based on the needs of others': ['C'],
            
            # Team Building (TB)
            'I am confident in my ability to assemble highly productive teams': ['TB'],
            'I know how to develop strong team performance': ['TB'],
            'I trust individuals with their responsibilities': ['TB'],
            'I provide excellent guidance to teams that I lead': ['TB'],
            'I love to see my team get positive recognition': ['TB'],
            'I take credit for the accomplishments of my team': ['TB'],
            'When constructive conflict arises in my team, I am comfortable with it': ['TB'],
            'I can identify good talent': ['TB'],
            'I believe teams develop better solutions than individuals': ['TB'],
            'I create safe team environments': ['TB'],
            
            # Servant Leadership (SL)
            'I contribute without needing my name attached': ['SL'],
            'I want others to know what I did': ['SL'],
            'I focus on the needs of my team': ['SL'],
            'I want my legacy to elevate others': ['SL'],
            'I am a good listener': ['SL'],
            'I speak up at meetings': ['SL'],
            'I value input from everyone equally': ['SL'],
            'I want the whole team to succeed': ['SL'],
            'Trust is essential for innovation': ['SL'],
            
            # Failure Resilience (F)
            'I am discouraged by failure': ['F'],
            'Failure teaches me': ['F'],
            'I admit my mistakes even when it might affect how others see me': ['F'],
            'I am comfortable with failure': ['F'],
            'When something goes wrong, it is my fault': ['F'],
            'I am resistant to change after experiencing a setback': ['F'],
            'I accept responsibility for errors': ['F'],
            'Failure makes me want to stop trying': ['F'],
            'Some failures are worse than other failures': ['F'],
            'Some failures are better than other failures': ['F'],
            'I update my perspective even when it means letting go of familiar strategies': ['F'],
            
            # Resilience & Grit (RG)
            'I give up when something is challenging': ['RG'],
            'I am determined to reach my goals': ['RG'],
            'I work through difficult situations rather than avoid them': ['RG'],
            'I stay committed, even if results take longer than expected': ['RG'],
            'If the path I\'m on isn\'t working, I\'m quick to test a new one': ['RG'],
            'Even when priorities shift, I follow through on what I promised': ['RG'],
            'I keep my promises': ['RG'],
            'I handle frustration well': ['RG'],
            
            # Relationship Building (RB)
            'I value relationships': ['RB'],
            'I am an open communicator': ['RB'],
            'I am comfortable being vulnerable': ['RB'],
            'I nurture connections': ['RB'],
            'I use people as a means to an end': ['RB'],
            'I listen actively': ['RB'],
            'I am easily distracted': ['RB'],
            'I am open to feedback': ['RB'],
            'I move past small talk': ['RB'],
            'I build rapport with anyone': ['RB'],
            'I maintain relationships': ['RB'],
            'Relationships are transactional': ['RB'],
            
            # Negotiation (N)
            'I adjust my approach in negotiations without losing sight of what matters most': ['N'],
            'I can see someone else\'s perspective': ['N'],
            'I compromise': ['N'],
            'I am collaborative': ['N'],
            
            # Introverted vs Extroverted (IN)
            'Social situations drain my energy': ['IN'],
            'I am energized by meeting new people': ['IN'],
            'I am inclined to speak up and pitch ideas in group settings or large events': ['IN'],
            'I am driven by social engagement': ['IN'],
            'I jump into conversations': ['IN'],
            'I actively participate': ['IN'],
            'I am comfortable sharing ideas in smaller, more personal settings': ['IN'],
            'I am observant': ['IN'],
            'I am an active listener': ['IN'],
            'I reflect': ['IN']
        }
    
    def _create_likert_mapping(self) -> Dict[str, float]:
        """Create mapping from Likert responses to numeric values"""
        return {
            'Seldom (11-35%)': 0.2,
            'Sometimes (36-65%)': 0.5, 
            'Often (66-90%)': 0.8,
            'Always (91-100%)': 1.0
        }
    
    def get_question_mapping(self) -> Dict[str, List[str]]:
        """Get the question-trait mapping"""
        return self.question_trait_mapping
    
    def get_likert_mapping(self) -> Dict[str, float]:
        """Get the Likert scale mapping"""
        return self.likert_mapping
    
    def map_likert_to_numeric(self, likert_value) -> float:
        """Convert Likert scale responses to numeric values"""
        if pd.isna(likert_value):
            return 0.5  # Neutral value for missing data
        
        likert_value = str(likert_value).strip()
        return self.likert_mapping.get(likert_value, 0.5)  # Default to neutral if not found
    
    def get_trait_names(self) -> List[str]:
        """Get list of all trait names"""
        all_traits = set()
        for traits in self.question_trait_mapping.values():
            all_traits.update(traits)
        return sorted(list(all_traits))
    
    def get_questions_for_trait(self, trait: str) -> List[str]:
        """Get all questions that measure a specific trait"""
        questions = []
        for question, traits in self.question_trait_mapping.items():
            if trait in traits:
                questions.append(question)
        return questions
    
    def validate_mapping(self) -> Dict[str, any]:
        """Validate the mapping and return statistics"""
        stats = {
            'total_questions': len(self.question_trait_mapping),
            'total_traits': len(self.get_trait_names()),
            'trait_distribution': {},
            'questions_per_trait': {}
        }
        
        # Count questions per trait
        for trait in self.get_trait_names():
            questions = self.get_questions_for_trait(trait)
            stats['questions_per_trait'][trait] = len(questions)
            stats['trait_distribution'][trait] = len(questions)
        
        return stats

