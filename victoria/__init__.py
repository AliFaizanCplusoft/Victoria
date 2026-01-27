"""
Victoria Package
Professional psychometric assessment system
"""

# Core modules
from .core import DataProcessor, ArchetypeDetector, VisualizationEngine, ReportGenerator

# Scoring modules
from .scoring.fixed_trait_scorer import FixedTraitScorer

__version__ = "2.0.0"
__all__ = [
    'DataProcessor',
    'ArchetypeDetector',
    'VisualizationEngine',
    'ReportGenerator',
    'FixedTraitScorer'
]