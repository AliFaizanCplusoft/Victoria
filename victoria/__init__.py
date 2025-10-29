"""
Victoria Package
Professional psychometric assessment system
"""

from .services import AssessmentService
from .scoring import UnifiedTraitScorer
from .factories import DependencyFactory

__version__ = "2.0.0"
__all__ = [
    'AssessmentService',
    'UnifiedTraitScorer', 
    'DependencyFactory'
]