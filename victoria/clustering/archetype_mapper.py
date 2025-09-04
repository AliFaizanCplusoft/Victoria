"""
Vertria Archetype Mapper
Maps individual profiles and clusters to entrepreneurial archetypes
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

from victoria.core.models import PersonTraitProfile, ArchetypeScore, TraitCluster
from victoria.core.enums import ArchetypeType
from victoria.config.settings import archetype_config, trait_config

class ArchetypeMapper:
    """
    Maps individual profiles and clusters to Vertria's entrepreneurial archetypes
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def map_individual_to_archetype(self, profile: PersonTraitProfile) -> PersonTraitProfile:
        """Map an individual profile to archetypes"""
        archetype_scores = self._calculate_archetype_scores(profile)
        
        # Sort by score and confidence
        archetype_scores.sort(key=lambda x: x.score * x.confidence, reverse=True)
        
        if archetype_scores:
            profile.primary_archetype = archetype_scores[0]
            profile.secondary_archetypes = archetype_scores[1:3]
        
        return profile
    
    def _calculate_archetype_scores(self, profile: PersonTraitProfile) -> List[ArchetypeScore]:
        """Calculate archetype match scores for a profile"""
        archetype_scores = []
        trait_dict = profile.trait_dict
        
        for archetype_key, archetype_info in archetype_config.ARCHETYPES.items():
            archetype_type = ArchetypeType(archetype_key)
            
            # Calculate archetype score
            score, confidence, matching_traits = self._calculate_single_archetype_score(
                trait_dict, archetype_info['core_traits']
            )
            
            if score > 0:  # Only include if there's some match
                archetype_scores.append(ArchetypeScore(
                    archetype=archetype_type,
                    score=score,
                    confidence=confidence,
                    matching_traits=matching_traits,
                    description=archetype_info['description'],
                    characteristics=archetype_info['characteristics']
                ))
        
        return archetype_scores
    
    def _calculate_single_archetype_score(self, trait_dict: Dict[str, any], 
                                        core_traits: List[str]) -> Tuple[float, float, List[str]]:
        """Calculate score for a single archetype"""
        trait_scores = []
        matching_traits = []
        
        for trait_name in core_traits:
            if trait_name in trait_dict:
                trait_score = trait_dict[trait_name]
                # Use normalized score (0-1 scale based on percentile)
                normalized_score = trait_score.percentile / 100.0
                trait_scores.append(normalized_score)
                matching_traits.append(trait_name)
        
        if not trait_scores:
            return 0.0, 0.0, []
        
        # Calculate archetype score as weighted average
        archetype_score = np.mean(trait_scores)
        
        # Calculate confidence based on:
        # 1. Coverage: how many core traits we have data for
        # 2. Consistency: how consistent the trait scores are
        # 3. Strength: how strong the overall scores are
        
        coverage = len(matching_traits) / len(core_traits)
        consistency = 1.0 - (np.std(trait_scores) if len(trait_scores) > 1 else 0.0)
        strength = archetype_score
        
        confidence = coverage * consistency * (0.5 + 0.5 * strength)
        
        return archetype_score, confidence, matching_traits
    
    def map_cluster_to_archetype(self, cluster: TraitCluster) -> Optional[ArchetypeType]:
        """Map a trait cluster to the best matching archetype"""
        best_match = None
        best_score = 0.0
        
        for archetype_key, archetype_info in archetype_config.ARCHETYPES.items():
            archetype_type = ArchetypeType(archetype_key)
            core_traits = archetype_info['core_traits']
            
            # Calculate match score
            match_score = self._calculate_cluster_archetype_match(cluster, core_traits)
            
            if match_score > best_score:
                best_score = match_score
                best_match = archetype_type
        
        # Only return match if score is above threshold
        return best_match if best_score > 0.3 else None
    
    def _calculate_cluster_archetype_match(self, cluster: TraitCluster, 
                                         core_traits: List[str]) -> float:
        """Calculate how well a cluster matches an archetype"""
        # Calculate trait overlap
        cluster_traits_set = set(cluster.traits)
        core_traits_set = set(core_traits)
        
        overlap = cluster_traits_set & core_traits_set
        overlap_ratio = len(overlap) / len(core_traits_set)
        
        # Calculate centroid alignment for overlapping traits
        centroid_scores = []
        for trait in overlap:
            if trait in trait_config.CORE_TRAITS:
                trait_index = trait_config.CORE_TRAITS.index(trait)
                if trait_index < len(cluster.centroid):
                    centroid_scores.append(cluster.centroid[trait_index])
        
        # Calculate strength of matching traits
        strength = np.mean(centroid_scores) if centroid_scores else 0.0
        
        # Combined score: overlap ratio weighted by trait strength
        match_score = overlap_ratio * (0.5 + 0.5 * max(0, strength))
        
        return match_score
    
    def generate_archetype_insights(self, archetype_score: ArchetypeScore, 
                                  profile: PersonTraitProfile) -> Dict[str, any]:
        """Generate detailed insights for an archetype match"""
        insights = {
            'archetype': archetype_score.archetype.value,
            'match_strength': archetype_score.score,
            'confidence': archetype_score.confidence,
            'key_strengths': [],
            'development_areas': [],
            'recommendations': [],
            'career_alignment': []
        }
        
        # Analyze key strengths
        for trait_name in archetype_score.matching_traits:
            trait_score = profile.get_trait_score(trait_name)
            if trait_score and trait_score.percentile > 70:
                insights['key_strengths'].append({
                    'trait': trait_name,
                    'percentile': trait_score.percentile,
                    'level': trait_score.level.value
                })
        
        # Identify development areas (core archetype traits that are lower)
        archetype_info = archetype_config.ARCHETYPES[archetype_score.archetype.value]
        for trait_name in archetype_info['core_traits']:
            trait_score = profile.get_trait_score(trait_name)
            if trait_score and trait_score.percentile < 40:
                insights['development_areas'].append({
                    'trait': trait_name,
                    'percentile': trait_score.percentile,
                    'improvement_potential': 100 - trait_score.percentile
                })
        
        # Generate recommendations
        insights['recommendations'] = self._generate_archetype_recommendations(
            archetype_score.archetype, insights['key_strengths'], insights['development_areas']
        )
        
        # Suggest career alignments
        insights['career_alignment'] = self._suggest_career_alignments(archetype_score.archetype)
        
        return insights
    
    def _generate_archetype_recommendations(self, archetype: ArchetypeType, 
                                          strengths: List[Dict], 
                                          development_areas: List[Dict]) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Archetype-specific recommendations
        archetype_recs = {
            ArchetypeType.STRATEGIC_INNOVATION: [
                "Develop structured innovation frameworks",
                "Focus on strategic planning and market analysis",
                "Build skills in technology assessment and trend analysis"
            ],
            ArchetypeType.RESILIENT_LEADERSHIP: [
                "Enhance crisis management capabilities",
                "Develop advanced conflict resolution skills",
                "Focus on team resilience and change management"
            ],
            ArchetypeType.COLLABORATIVE_RESPONSIBILITY: [
                "Strengthen servant leadership practices",
                "Build advanced team development skills",
                "Focus on accountability systems and trust-building"
            ],
            ArchetypeType.AMBITIOUS_DRIVE: [
                "Set challenging long-term goals with clear metrics",
                "Develop persistence and grit training",
                "Focus on achievement psychology and motivation"
            ],
            ArchetypeType.ADAPTIVE_INTELLIGENCE: [
                "Enhance analytical problem-solving frameworks",
                "Develop emotional intelligence competencies",
                "Focus on customer empathy and market understanding"
            ]
        }
        
        recommendations.extend(archetype_recs.get(archetype, []))
        
        # Add development-specific recommendations
        for area in development_areas[:2]:  # Top 2 development areas
            trait = area['trait']
            if trait == "Leadership":
                recommendations.append("Consider leadership development programs or mentoring")
            elif trait == "Innovation":
                recommendations.append("Engage in creative thinking workshops or innovation labs")
            elif trait == "Risk Taking":
                recommendations.append("Practice calculated risk-taking in low-stakes situations")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _suggest_career_alignments(self, archetype: ArchetypeType) -> List[str]:
        """Suggest career paths aligned with the archetype"""
        career_alignments = {
            ArchetypeType.STRATEGIC_INNOVATION: [
                "Chief Innovation Officer",
                "Strategic Planning Director", 
                "R&D Leadership",
                "Technology Strategy Consultant"
            ],
            ArchetypeType.RESILIENT_LEADERSHIP: [
                "CEO/Executive Leadership",
                "Crisis Management Consultant",
                "Change Management Director",
                "Team Leadership Roles"
            ],
            ArchetypeType.COLLABORATIVE_RESPONSIBILITY: [
                "Team Development Manager",
                "Servant Leadership Roles",
                "HR Leadership",
                "Mentorship and Coaching"
            ],
            ArchetypeType.AMBITIOUS_DRIVE: [
                "Entrepreneur/Founder",
                "Sales Leadership",
                "Business Development",
                "Growth Strategy Roles"
            ],
            ArchetypeType.ADAPTIVE_INTELLIGENCE: [
                "Management Consulting",
                "Business Analysis",
                "Customer Experience Leadership",
                "Strategic Advisory"
            ]
        }
        
        return career_alignments.get(archetype, [
            "Leadership Development",
            "Strategic Roles",
            "Team Management",
            "Business Strategy"
        ])