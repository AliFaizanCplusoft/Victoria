"""
Core enumerations for Victoria Project
"""
from enum import Enum, auto

class ArchetypeType(Enum):
    """Vertria's 5 Entrepreneurial Archetypes"""
    STRATEGIC_INNOVATION = "strategic_innovation"
    RESILIENT_LEADERSHIP = "resilient_leadership" 
    COLLABORATIVE_RESPONSIBILITY = "collaborative_responsibility"
    AMBITIOUS_DRIVE = "ambitious_drive"
    ADAPTIVE_INTELLIGENCE = "adaptive_intelligence"

class TraitType(Enum):
    """The 11 core psychometric traits"""
    RISK_TAKING = "Risk Taking"
    INNOVATION = "Innovation"
    LEADERSHIP = "Leadership"
    RESILIENCE = "Resilience"
    ACCOUNTABILITY = "Accountability"
    DECISION_MAKING = "Decision Making"
    ADAPTABILITY = "Adaptability"
    CONTINUOUS_LEARNING = "Continuous Learning"
    PASSION_DRIVE = "Passion/Drive"
    PROBLEM_SOLVING = "Problem Solving"
    EMOTIONAL_INTELLIGENCE = "Emotional Intelligence"

class ReportFormat(Enum):
    """Available report formats"""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"

class ScoreLevel(Enum):
    """Score level categories"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"