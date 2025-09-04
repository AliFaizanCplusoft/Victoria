"""
Core domain models for Victoria Project
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
from .enums import ArchetypeType, TraitType, ScoreLevel

@dataclass
class TraitScore:
    """Individual trait score information"""
    trait_name: str
    score: float
    percentile: float
    items_count: int
    description: str
    level: Optional[ScoreLevel] = None
    confidence: Optional[float] = None
    
    def __post_init__(self):
        """Calculate score level based on percentile"""
        if self.level is None:
            if self.percentile >= 90:
                self.level = ScoreLevel.VERY_HIGH
            elif self.percentile >= 70:
                self.level = ScoreLevel.HIGH
            elif self.percentile >= 30:
                self.level = ScoreLevel.MODERATE
            else:
                self.level = ScoreLevel.LOW

@dataclass
class ArchetypeScore:
    """Archetype match information"""
    archetype: ArchetypeType
    score: float
    confidence: float
    matching_traits: List[str]
    description: str
    characteristics: List[str]

@dataclass
class PersonTraitProfile:
    """Complete trait profile for an individual"""
    person_id: str
    traits: List[TraitScore]
    overall_score: float
    completion_rate: float
    primary_archetype: Optional[ArchetypeScore] = None
    secondary_archetypes: List[ArchetypeScore] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    growth_areas: List[str] = field(default_factory=list)
    
    @property
    def trait_dict(self) -> Dict[str, TraitScore]:
        """Get traits as a dictionary"""
        return {trait.trait_name: trait for trait in self.traits}
    
    def get_trait_score(self, trait_name: str) -> Optional[TraitScore]:
        """Get score for a specific trait"""
        return self.trait_dict.get(trait_name)

@dataclass
class TraitCluster:
    """Information about a trait cluster"""
    cluster_id: int
    traits: List[str]
    cluster_name: str
    description: str
    centroid: np.ndarray
    size: int
    archetype_mapping: Optional[ArchetypeType] = None
    
    def __post_init__(self):
        """Convert numpy array to list for serialization if needed"""
        if isinstance(self.centroid, np.ndarray):
            self.centroid = self.centroid.tolist()

@dataclass
class ClusteringResult:
    """Result of trait clustering analysis"""
    clusters: List[TraitCluster]
    silhouette_score: float
    explained_variance: float
    method_used: str
    n_clusters: int
    archetype_mappings: Dict[int, ArchetypeType] = field(default_factory=dict)

@dataclass
class ReportData:
    """Data structure for report generation"""
    profile: PersonTraitProfile
    clusters: Optional[ClusteringResult] = None
    visualizations: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def report_title(self) -> str:
        """Generate report title"""
        if self.profile.primary_archetype:
            return f"Psychometric Profile - {self.profile.primary_archetype.archetype.value.replace('_', ' ').title()}"
        return f"Psychometric Profile - {self.profile.person_id}"