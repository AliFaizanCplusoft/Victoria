"""
Dashboard Integration Module
Integrates the personality dashboard with the existing ML pipeline.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import json
import numpy as np
from datetime import datetime

# Import existing components
from ..scoring.scoring_engine import PsychometricScoringEngine
from ..clustering.clustering_engine import PsychometricClusteringEngine
from ..data.data_preprocessor import PsychometricDataPreprocessor

# Import new personality components
from .personality_dashboard import PersonalityDashboard, PersonalityProfile, PersonalityTrait
from ..reports.personality_report_generator import PersonalityReportGenerator, ReportConfig


class DashboardIntegration:
    """Integrates personality dashboard with existing ML pipeline."""
    
    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.scoring_engine = PsychometricScoringEngine()
        self.clustering_engine = PsychometricClusteringEngine()
        self.personality_dashboard = PersonalityDashboard()
        self.report_generator = PersonalityReportGenerator()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        self.logger.info("DashboardIntegration initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration for dashboard integration."""
        default_config = {
            "trait_mappings": {
                "innovation_orientation": "Innovation Orientation",
                "risk_taking": "Risk Taking",
                "servant_leadership": "Servant Leadership",
                "analytical_thinking": "Analytical Thinking",
                "communication": "Communication",
                "collaboration": "Collaboration",
                "adaptability": "Adaptability",
                "execution": "Execution"
            },
            "archetype_mappings": {
                "innovator": "Innovator",
                "executor": "Executor", 
                "strategist": "Strategist",
                "collaborator": "Collaborator",
                "analyst": "Analyst"
            },
            "visualization_config": {
                "theme": "plotly_white",
                "color_scheme": "professional",
                "include_comparisons": True,
                "include_population_data": True
            },
            "report_config": {
                "include_development_plan": True,
                "include_archetype_analysis": True,
                "format": "html",
                "color_theme": "professional"
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge with default config
                for key, value in user_config.items():
                    if key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            except Exception as e:
                self.logger.warning(f"Error loading config from {config_path}: {e}")
        
        return default_config
    
    def process_assessment_data(self, assessment_data: Dict[str, Any]) -> PersonalityProfile:
        """Process assessment data and create personality profile."""
        try:
            # Extract person information
            person_id = assessment_data.get('person_id', 'unknown')
            name = assessment_data.get('name', f'Person {person_id}')
            
            # Process scoring
            scores = self.scoring_engine.calculate_scores(assessment_data)
            
            # Create personality traits
            traits = []
            trait_mappings = self.config.get('trait_mappings', {})
            
            for trait_key, trait_name in trait_mappings.items():
                if trait_key in scores:
                    score_data = scores[trait_key]
                    
                    # Extract score and percentile
                    raw_score = score_data.get('raw_score', 0.0)
                    percentile = score_data.get('percentile', 50.0)
                    
                    # Normalize score to 1-10 scale
                    normalized_score = self._normalize_score(raw_score, trait_key)
                    
                    # Get trait description
                    description = self._get_trait_description(trait_key)
                    
                    # Determine category
                    category = self._get_trait_category(trait_key)
                    
                    trait = PersonalityTrait(
                        name=trait_name,
                        score=normalized_score,
                        percentile=percentile,
                        description=description,
                        category=category
                    )
                    traits.append(trait)
            
            # Calculate overall scores
            overall_score = np.mean([trait.score for trait in traits]) if traits else 0.0
            overall_percentile = np.mean([trait.percentile for trait in traits]) if traits else 0.0
            
            # Determine archetype
            archetype_info = self._determine_archetype(traits)
            
            # Generate strengths and weaknesses
            strengths = [trait.name for trait in traits if trait.percentile > 75][:5]
            weaknesses = [trait.name for trait in traits if trait.percentile < 25][:3]
            
            # Generate recommendations
            recommendations = self._generate_recommendations(traits, archetype_info['archetype'])
            
            # Create personality profile
            profile = PersonalityProfile(
                person_id=person_id,
                name=name,
                traits=traits,
                overall_score=overall_score,
                overall_percentile=overall_percentile,
                archetype=archetype_info['archetype'],
                archetype_match=archetype_info['match_percentage'],
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations
            )
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error processing assessment data: {e}")
            raise
    
    def _normalize_score(self, raw_score: float, trait_key: str) -> float:
        """Normalize raw score to 1-10 scale."""
        # This would typically be based on normative data
        # For now, we'll use a simple normalization
        
        # Assume raw scores are typically in 0-100 range
        if raw_score > 100:
            raw_score = 100
        elif raw_score < 0:
            raw_score = 0
        
        # Convert to 1-10 scale
        normalized = (raw_score / 100.0) * 9.0 + 1.0
        return round(normalized, 1)
    
    def _get_trait_description(self, trait_key: str) -> str:
        """Get description for a trait."""
        descriptions = {
            "innovation_orientation": "Tendency to generate and implement creative solutions",
            "risk_taking": "Willingness to take calculated risks for potential rewards",
            "servant_leadership": "Focus on serving others and empowering team members",
            "analytical_thinking": "Ability to analyze complex problems systematically",
            "communication": "Effectiveness in conveying ideas and listening to others",
            "collaboration": "Ability to work effectively with diverse teams",
            "adaptability": "Flexibility in adjusting to changing circumstances",
            "execution": "Ability to implement plans and achieve results"
        }
        return descriptions.get(trait_key, "Personality trait assessment")
    
    def _get_trait_category(self, trait_key: str) -> str:
        """Get category for a trait."""
        categories = {
            "innovation_orientation": "cognitive",
            "risk_taking": "behavioral",
            "servant_leadership": "interpersonal",
            "analytical_thinking": "cognitive",
            "communication": "interpersonal",
            "collaboration": "interpersonal",
            "adaptability": "behavioral",
            "execution": "behavioral"
        }
        return categories.get(trait_key, "general")
    
    def _determine_archetype(self, traits: List[PersonalityTrait]) -> Dict[str, Any]:
        """Determine personality archetype based on traits."""
        # Create trait score dictionary
        trait_scores = {trait.name: trait.score for trait in traits}
        
        # Define archetype profiles (ideal trait combinations)
        archetype_profiles = {
            "Innovator": {
                "Innovation Orientation": 8.0,
                "Risk Taking": 7.0,
                "Adaptability": 7.5,
                "Analytical Thinking": 6.5,
                "Communication": 6.0,
                "Collaboration": 5.5,
                "Execution": 5.0,
                "Servant Leadership": 6.0
            },
            "Executor": {
                "Execution": 8.5,
                "Servant Leadership": 7.0,
                "Analytical Thinking": 6.5,
                "Communication": 7.0,
                "Collaboration": 6.0,
                "Innovation Orientation": 5.0,
                "Risk Taking": 5.5,
                "Adaptability": 6.5
            },
            "Strategist": {
                "Analytical Thinking": 8.5,
                "Innovation Orientation": 7.0,
                "Risk Taking": 6.0,
                "Communication": 6.5,
                "Execution": 6.0,
                "Adaptability": 6.5,
                "Collaboration": 5.5,
                "Servant Leadership": 5.0
            },
            "Collaborator": {
                "Collaboration": 8.5,
                "Servant Leadership": 8.0,
                "Communication": 7.5,
                "Adaptability": 7.0,
                "Analytical Thinking": 6.0,
                "Execution": 6.5,
                "Innovation Orientation": 5.5,
                "Risk Taking": 4.5
            },
            "Analyst": {
                "Analytical Thinking": 9.0,
                "Execution": 7.0,
                "Communication": 6.0,
                "Innovation Orientation": 6.0,
                "Adaptability": 5.5,
                "Collaboration": 5.0,
                "Risk Taking": 4.0,
                "Servant Leadership": 5.5
            }
        }
        
        # Calculate match percentages
        best_match = None
        best_percentage = 0.0
        
        for archetype, ideal_profile in archetype_profiles.items():
            # Calculate similarity
            matches = []
            for trait_name, ideal_score in ideal_profile.items():
                actual_score = trait_scores.get(trait_name, 5.0)
                # Calculate similarity (inverse of absolute difference)
                similarity = 1.0 - abs(actual_score - ideal_score) / 10.0
                matches.append(max(0.0, similarity))
            
            # Average similarity as match percentage
            match_percentage = (np.mean(matches) * 100)
            
            if match_percentage > best_percentage:
                best_percentage = match_percentage
                best_match = archetype
        
        return {
            "archetype": best_match or "Balanced",
            "match_percentage": best_percentage
        }
    
    def _generate_recommendations(self, traits: List[PersonalityTrait], archetype: str) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        # General archetype recommendations
        archetype_recommendations = {
            "Innovator": [
                "Leverage your creativity to drive innovation initiatives",
                "Seek opportunities to prototype and test new ideas",
                "Build networks with other creative professionals"
            ],
            "Executor": [
                "Take on project management roles to utilize your execution skills",
                "Focus on process improvement and efficiency gains",
                "Mentor others in planning and implementation"
            ],
            "Strategist": [
                "Contribute to long-term planning and strategy development",
                "Use your analytical skills to solve complex problems",
                "Share insights through reports and presentations"
            ],
            "Collaborator": [
                "Facilitate team meetings and group decision-making",
                "Take on roles that involve conflict resolution",
                "Build cross-functional relationships"
            ],
            "Analyst": [
                "Focus on data-driven decision making",
                "Develop expertise in analytical tools and methods",
                "Provide detailed analysis to support strategic decisions"
            ]
        }
        
        recommendations.extend(archetype_recommendations.get(archetype, []))
        
        # Trait-specific recommendations
        weak_traits = [trait for trait in traits if trait.percentile < 25]
        for trait in weak_traits[:2]:  # Focus on top 2 weaknesses
            trait_recommendations = {
                "Innovation Orientation": "Explore creative thinking techniques and innovation methodologies",
                "Risk Taking": "Practice taking calculated risks in low-stakes situations",
                "Servant Leadership": "Focus on developing empathy and team support skills",
                "Analytical Thinking": "Strengthen problem-solving and data analysis abilities",
                "Communication": "Improve presentation and interpersonal communication skills",
                "Collaboration": "Work on team dynamics and conflict resolution skills",
                "Adaptability": "Practice flexibility and change management techniques",
                "Execution": "Develop project management and implementation skills"
            }
            
            rec = trait_recommendations.get(trait.name)
            if rec:
                recommendations.append(rec)
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def generate_comprehensive_report(self, assessment_data: Dict[str, Any],
                                    population_data: List[Dict[str, Any]] = None,
                                    output_dir: str = None) -> Dict[str, str]:
        """Generate comprehensive personality report with visualizations."""
        try:
            # Process main assessment
            profile = self.process_assessment_data(assessment_data)
            
            # Process population data if provided
            all_profiles = []
            if population_data:
                for data in population_data:
                    try:
                        pop_profile = self.process_assessment_data(data)
                        all_profiles.append(pop_profile)
                    except Exception as e:
                        self.logger.warning(f"Error processing population data: {e}")
                        continue
            
            # Add main profile to population
            all_profiles.append(profile)
            
            # Generate visualizations
            if not output_dir:
                output_dir = f"output/personality_report_{profile.person_id}"
            
            viz_files = self.personality_dashboard.generate_comprehensive_dashboard(
                profile=profile,
                comparison_profiles=all_profiles[:3] if len(all_profiles) > 1 else None,
                all_profiles=all_profiles,
                output_dir=output_dir
            )
            
            # Generate HTML report
            report_config = ReportConfig(**self.config.get('report_config', {}))
            html_report = self.report_generator.generate_html_report(
                profile=profile,
                config=report_config,
                all_profiles=all_profiles
            )
            
            # Combine results
            results = {
                "profile": profile,
                "visualizations": viz_files,
                "html_report": html_report,
                "output_directory": output_dir
            }
            
            self.logger.info(f"Comprehensive report generated for {profile.name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            raise
    
    def process_batch_assessments(self, assessment_batch: List[Dict[str, Any]],
                                output_dir: str = None) -> List[Dict[str, Any]]:
        """Process multiple assessments and generate batch reports."""
        try:
            if not output_dir:
                output_dir = "output/batch_personality_reports"
            
            # Process all assessments
            all_profiles = []
            for assessment_data in assessment_batch:
                try:
                    profile = self.process_assessment_data(assessment_data)
                    all_profiles.append(profile)
                except Exception as e:
                    self.logger.warning(f"Error processing assessment {assessment_data.get('person_id', 'unknown')}: {e}")
                    continue
            
            # Generate individual reports
            results = []
            for profile in all_profiles:
                try:
                    # Other profiles for comparison
                    comparison_profiles = [p for p in all_profiles if p.person_id != profile.person_id]
                    
                    # Generate comprehensive report
                    individual_results = {
                        "profile": profile,
                        "visualizations": {},
                        "html_report": None,
                        "output_directory": f"{output_dir}/{profile.person_id}"
                    }
                    
                    # Generate visualizations
                    viz_files = self.personality_dashboard.generate_comprehensive_dashboard(
                        profile=profile,
                        comparison_profiles=comparison_profiles[:3],
                        all_profiles=all_profiles,
                        output_dir=individual_results["output_directory"]
                    )
                    individual_results["visualizations"] = viz_files
                    
                    # Generate HTML report
                    report_config = ReportConfig(**self.config.get('report_config', {}))
                    html_report = self.report_generator.generate_html_report(
                        profile=profile,
                        config=report_config,
                        all_profiles=all_profiles
                    )
                    individual_results["html_report"] = html_report
                    
                    results.append(individual_results)
                    
                except Exception as e:
                    self.logger.error(f"Error generating report for {profile.person_id}: {e}")
                    continue
            
            self.logger.info(f"Batch processing completed: {len(results)} reports generated")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing batch assessments: {e}")
            raise
    
    def update_existing_dashboard(self, dashboard_file: str, 
                                new_assessment_data: Dict[str, Any]) -> bool:
        """Update existing ML dashboard with personality insights."""
        try:
            # Process new assessment
            profile = self.process_assessment_data(new_assessment_data)
            
            # Read existing dashboard
            if not os.path.exists(dashboard_file):
                self.logger.error(f"Dashboard file not found: {dashboard_file}")
                return False
            
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                dashboard_content = f.read()
            
            # Generate personality section HTML
            personality_section = self._generate_personality_section(profile)
            
            # Insert personality section into dashboard
            # Look for insertion point (could be a comment or specific div)
            insertion_point = "<!-- PERSONALITY_SECTION -->"
            if insertion_point in dashboard_content:
                dashboard_content = dashboard_content.replace(
                    insertion_point, 
                    personality_section
                )
            else:
                # Append to end of body
                dashboard_content = dashboard_content.replace(
                    "</body>", 
                    f"{personality_section}</body>"
                )
            
            # Write updated dashboard
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                f.write(dashboard_content)
            
            self.logger.info(f"Dashboard updated with personality insights for {profile.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")
            return False
    
    def _generate_personality_section(self, profile: PersonalityProfile) -> str:
        """Generate HTML section for personality insights."""
        html = f"""
        <div class="personality-section">
            <h2>Personality Insights: {profile.name}</h2>
            <div class="personality-overview">
                <div class="personality-card">
                    <h3>Archetype</h3>
                    <div class="archetype-value">{profile.archetype}</div>
                    <div class="archetype-match">{profile.archetype_match:.1f}% match</div>
                </div>
                <div class="personality-card">
                    <h3>Overall Score</h3>
                    <div class="score-value">{profile.overall_score:.1f}/10</div>
                    <div class="percentile-value">{profile.overall_percentile:.0f}th percentile</div>
                </div>
            </div>
            <div class="personality-traits">
                <h3>Key Traits</h3>
                <div class="traits-grid">
        """
        
        # Add top traits
        for trait in profile.traits[:6]:  # Show top 6 traits
            strength_class = "strength" if trait.percentile > 75 else "weakness" if trait.percentile < 25 else "moderate"
            html += f"""
                    <div class="trait-item {strength_class}">
                        <div class="trait-name">{trait.name}</div>
                        <div class="trait-score">{trait.score:.1f}</div>
                        <div class="trait-percentile">{trait.percentile:.0f}th</div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        </div>
        
        <style>
        .personality-section {
            margin: 20px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .personality-overview {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .personality-card {
            flex: 1;
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .archetype-value, .score-value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }
        .traits-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .trait-item {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .trait-item.strength {
            background: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .trait-item.weakness {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        .trait-item.moderate {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
        }
        .trait-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .trait-score {
            font-size: 1.5em;
            font-weight: bold;
        }
        .trait-percentile {
            font-size: 0.9em;
            color: #666;
        }
        </style>
        """
        
        return html