"""
Enhanced Personality Report Generator
Generates comprehensive HTML and PDF reports with interactive visualizations.
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
from jinja2 import Environment, FileSystemLoader, Template
import pdfkit
from io import BytesIO
try:
      import weasyprint
      WEASYPRINT_AVAILABLE = True
except ImportError:
      WEASYPRINT_AVAILABLE = False
      weasyprint = None

# Import our visualization components
from ..visualization.personality_dashboard import PersonalityDashboard, PersonalityProfile, PersonalityTrait


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    include_comparisons: bool = True
    include_archetype_analysis: bool = True
    include_development_plan: bool = True
    include_detailed_explanations: bool = True
    color_theme: str = "professional"  # professional, vibrant, minimal
    format: str = "html"  # html, pdf, both
    

class PersonalityReportGenerator:
    """Enhanced report generator for personality assessments."""
    
    def __init__(self, template_dir: str = None, output_dir: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Set up directories
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent.parent.parent / "templates" / "html"
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent / "output" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Initialize visualization dashboard
        self.dashboard = PersonalityDashboard()
        
        # Color themes
        self.color_themes = {
            "professional": {
                "primary": "#2c3e50",
                "secondary": "#3498db",
                "accent": "#e74c3c",
                "success": "#27ae60",
                "warning": "#f39c12",
                "background": "#ffffff",
                "text": "#2c3e50"
            },
            "vibrant": {
                "primary": "#9b59b6",
                "secondary": "#3498db",
                "accent": "#e67e22",
                "success": "#2ecc71",
                "warning": "#f1c40f",
                "background": "#ffffff",
                "text": "#2c3e50"
            },
            "minimal": {
                "primary": "#34495e",
                "secondary": "#7f8c8d",
                "accent": "#95a5a6",
                "success": "#2c3e50",
                "warning": "#7f8c8d",
                "background": "#ffffff",
                "text": "#2c3e50"
            }
        }
        
        self.logger.info("PersonalityReportGenerator initialized")
    
    def _generate_visualizations(self, profile: PersonalityProfile,
                               comparison_profiles: List[PersonalityProfile] = None,
                               all_profiles: List[PersonalityProfile] = None,
                               temp_dir: str = None) -> Dict[str, str]:
        """Generate all visualizations and return their file paths."""
        try:
            if not temp_dir:
                temp_dir = self.output_dir / "temp_visualizations"
            
            temp_path = Path(temp_dir)
            temp_path.mkdir(exist_ok=True)
            
            # Generate all visualizations
            viz_files = self.dashboard.generate_comprehensive_dashboard(
                profile=profile,
                comparison_profiles=comparison_profiles,
                all_profiles=all_profiles,
                output_dir=str(temp_path)
            )
            
            # Convert HTML files to embedded content
            embedded_content = {}
            for viz_name, file_path in viz_files.items():
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    embedded_content[viz_name] = content
                    
            return embedded_content
            
        except Exception as e:
            self.logger.error(f"Error generating visualizations: {e}")
            return {}
    
    def _calculate_insights(self, profile: PersonalityProfile) -> Dict[str, Any]:
        """Calculate insights and recommendations based on personality profile."""
        try:
            insights = {
                "key_strengths": [],
                "development_areas": [],
                "leadership_style": "",
                "communication_preferences": "",
                "work_environment": "",
                "career_suggestions": [],
                "development_plan": [],
                "risk_factors": [],
                "collaboration_style": ""
            }
            
            # Analyze strengths and weaknesses
            strengths = []
            weaknesses = []
            
            for trait in profile.traits:
                if trait.percentile >= 75 or trait.score >= 8.0:
                    strengths.append({
                        "name": trait.name,
                        "score": trait.score,
                        "percentile": trait.percentile,
                        "description": trait.description
                    })
                elif trait.percentile <= 25 or trait.score <= 4.0:
                    weaknesses.append({
                        "name": trait.name,
                        "score": trait.score,
                        "percentile": trait.percentile,
                        "description": trait.description
                    })
            
            # Sort and get top insights
            insights["key_strengths"] = sorted(strengths, key=lambda x: x["percentile"], reverse=True)[:5]
            insights["development_areas"] = sorted(weaknesses, key=lambda x: x["percentile"])[:3]
            
            # Generate archetype-based insights
            archetype_insights = self._get_archetype_insights(profile.archetype)
            insights.update(archetype_insights)
            
            # Generate development plan
            insights["development_plan"] = self._generate_development_plan(profile)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error calculating insights: {e}")
            return {}
    
    def _get_archetype_insights(self, archetype: str) -> Dict[str, str]:
        """Get insights based on archetype."""
        archetype_data = {
            "Innovator": {
                "leadership_style": "Visionary and transformational, inspiring others through creative solutions",
                "communication_preferences": "Brainstorming sessions, visual presentations, and open dialogue",
                "work_environment": "Dynamic, flexible environments that encourage experimentation",
                "collaboration_style": "Facilitates creative thinking and encourages diverse perspectives"
            },
            "Executor": {
                "leadership_style": "Results-oriented and decisive, focusing on efficient implementation",
                "communication_preferences": "Clear directives, structured meetings, and progress reports",
                "work_environment": "Organized, goal-oriented settings with clear processes",
                "collaboration_style": "Coordinates team efforts and ensures timely delivery"
            },
            "Strategist": {
                "leadership_style": "Analytical and forward-thinking, emphasizing long-term planning",
                "communication_preferences": "Data-driven presentations, strategic reviews, and thorough analysis",
                "work_environment": "Quiet, analytical spaces with access to information and resources",
                "collaboration_style": "Provides strategic direction and analytical insights"
            },
            "Collaborator": {
                "leadership_style": "Inclusive and supportive, building consensus and team harmony",
                "communication_preferences": "Team meetings, one-on-one discussions, and collaborative platforms",
                "work_environment": "Open, team-oriented spaces that foster communication",
                "collaboration_style": "Facilitates team cohesion and ensures everyone's voice is heard"
            },
            "Analyst": {
                "leadership_style": "Detail-oriented and methodical, ensuring accuracy and quality",
                "communication_preferences": "Detailed reports, technical discussions, and structured formats",
                "work_environment": "Structured, quiet environments with minimal distractions",
                "collaboration_style": "Provides detailed analysis and ensures quality standards"
            }
        }
        
        return archetype_data.get(archetype, {
            "leadership_style": "Balanced approach adapting to situational needs",
            "communication_preferences": "Flexible communication style based on context",
            "work_environment": "Adaptable to various work environments",
            "collaboration_style": "Versatile collaboration approach"
        })
    
    def _generate_development_plan(self, profile: PersonalityProfile) -> List[Dict[str, str]]:
        """Generate a personalized development plan."""
        development_plan = []
        
        # Focus on lowest scoring traits
        weak_traits = [trait for trait in profile.traits if trait.percentile <= 25 or trait.score <= 4.0]
        weak_traits.sort(key=lambda x: x.score)
        
        for trait in weak_traits[:3]:  # Focus on top 3 areas
            plan_item = {
                "area": trait.name,
                "current_level": f"{trait.score:.1f}/10 ({trait.percentile:.0f}th percentile)",
                "target": "Improve to moderate level (5-7 range)",
                "timeline": "3-6 months",
                "actions": self._get_development_actions(trait.name),
                "resources": self._get_development_resources(trait.name)
            }
            development_plan.append(plan_item)
        
        return development_plan
    
    def _get_development_actions(self, trait_name: str) -> List[str]:
        """Get specific development actions for a trait."""
        actions_map = {
            "Leadership": [
                "Volunteer for team leadership opportunities",
                "Seek mentorship from experienced leaders",
                "Practice public speaking and presentation skills",
                "Take on cross-functional project management roles"
            ],
            "Communication": [
                "Practice active listening techniques",
                "Join a public speaking group (e.g., Toastmasters)",
                "Seek feedback on communication style",
                "Practice presenting to different audiences"
            ],
            "Innovation": [
                "Engage in creative problem-solving exercises",
                "Explore new technologies and methodologies",
                "Participate in brainstorming sessions",
                "Challenge existing processes and propose improvements"
            ],
            "Collaboration": [
                "Participate in team-building activities",
                "Practice conflict resolution skills",
                "Seek diverse perspectives on projects",
                "Volunteer for cross-departmental initiatives"
            ],
            "Analytical Thinking": [
                "Take courses in data analysis or statistics",
                "Practice breaking down complex problems",
                "Use structured problem-solving frameworks",
                "Seek opportunities to analyze and interpret data"
            ]
        }
        
        return actions_map.get(trait_name, [
            "Seek specific training or coaching in this area",
            "Find a mentor who excels in this competency",
            "Practice deliberately in low-risk situations",
            "Get regular feedback on progress"
        ])
    
    def _get_development_resources(self, trait_name: str) -> List[str]:
        """Get development resources for a trait."""
        resources_map = {
            "Leadership": [
                "Book: 'The Leadership Challenge' by Kouzes & Posner",
                "Online: LinkedIn Learning Leadership courses",
                "Program: Executive leadership development programs",
                "Assessment: 360-degree feedback tools"
            ],
            "Communication": [
                "Book: 'Crucial Conversations' by Kerry Patterson",
                "Organization: Toastmasters International",
                "Course: Business communication workshops",
                "Tool: Video recording for presentation practice"
            ],
            "Innovation": [
                "Book: 'The Innovator's Dilemma' by Clayton Christensen",
                "Method: Design thinking workshops",
                "Platform: Innovation challenges and hackathons",
                "Tool: Creativity assessment and training"
            ],
            "Collaboration": [
                "Book: 'Getting to Yes' by Roger Fisher",
                "Training: Conflict resolution workshops",
                "Assessment: Team dynamics evaluations",
                "Platform: Collaborative project management tools"
            ],
            "Analytical Thinking": [
                "Book: 'Thinking, Fast and Slow' by Daniel Kahneman",
                "Course: Statistics and data analysis training",
                "Tool: Statistical software training (R, Python)",
                "Method: Case study analysis practice"
            ]
        }
        
        return resources_map.get(trait_name, [
            "Professional development courses",
            "Relevant books and articles",
            "Mentorship opportunities",
            "Practice opportunities"
        ])
    
    def generate_html_report(self, profile: PersonalityProfile,
                           config: ReportConfig = None,
                           comparison_profiles: List[PersonalityProfile] = None,
                           all_profiles: List[PersonalityProfile] = None) -> str:
        """Generate comprehensive HTML report."""
        try:
            if not config:
                config = ReportConfig()
            
            # Generate visualizations
            visualizations = self._generate_visualizations(
                profile, comparison_profiles, all_profiles
            )
            
            # Calculate insights
            insights = self._calculate_insights(profile)
            
            # Get color theme
            colors = self.color_themes.get(config.color_theme, self.color_themes["professional"])
            
            # Prepare template data
            template_data = {
                "profile": profile,
                "insights": insights,
                "visualizations": visualizations,
                "colors": colors,
                "config": config,
                "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "comparison_profiles": comparison_profiles or [],
                "has_population_data": bool(all_profiles)
            }
            
            # Load and render template
            template = self._get_html_template()
            html_content = template.render(**template_data)
            
            # Save HTML report
            output_file = self.output_dir / f"personality_report_{profile.person_id}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def generate_pdf_report(self, profile: PersonalityProfile,
                          config: ReportConfig = None,
                          comparison_profiles: List[PersonalityProfile] = None,
                          all_profiles: List[PersonalityProfile] = None) -> str:
        """Generate PDF report from HTML."""
        try:
            # First generate HTML report
            html_file = self.generate_html_report(profile, config, comparison_profiles, all_profiles)
            if not html_file:
                return None
            
            # Convert to PDF
            pdf_file = self.output_dir / f"personality_report_{profile.person_id}.pdf"
            
            # Use weasyprint for better CSS support
            try:
                if WEASYPRINT_AVAILABLE:
                    weasyprint.HTML(filename=html_file).write_pdf(str(pdf_file))
                else:
                    print(f"Skipping PDF generation - WeasyPrint not available")
                self.logger.info(f"PDF report generated: {pdf_file}")
                return str(pdf_file)
            except Exception as e:
                self.logger.warning(f"WeasyPrint failed, trying pdfkit: {e}")
                
                # Fallback to pdfkit
                options = {
                    'page-size': 'A4',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': "UTF-8",
                    'no-outline': None,
                    'enable-local-file-access': None
                }
                
                pdfkit.from_file(html_file, str(pdf_file), options=options)
                self.logger.info(f"PDF report generated: {pdf_file}")
                return str(pdf_file)
                
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            return None
    
    def _get_html_template(self) -> Template:
        """Get the HTML template for personality reports."""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personality Assessment Report - {{ profile.name }}</title>
    <style>
        /* Enhanced styling for personality reports */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: {{ colors.text }};
            background: {{ colors.background }};
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header styling */
        .header {
            background: linear-gradient(135deg, {{ colors.primary }}, {{ colors.secondary }});
            color: white;
            padding: 40px 0;
            text-align: center;
            margin: -20px -20px 40px -20px;
            border-radius: 0 0 20px 20px;
        }
        
        .header h1 {
            font-size: 2.8em;
            margin-bottom: 10px;
            font-weight: 300;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .subtitle {
            font-size: 1.3em;
            opacity: 0.9;
            margin-bottom: 20px;
        }
        
        .header .meta-info {
            font-size: 1em;
            opacity: 0.8;
        }
        
        /* Executive summary */
        .executive-summary {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 40px;
            border-radius: 15px;
            border-left: 5px solid {{ colors.primary }};
            margin-bottom: 40px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .executive-summary h2 {
            color: {{ colors.primary }};
            font-size: 2em;
            margin-bottom: 20px;
            border-bottom: 2px solid {{ colors.primary }};
            padding-bottom: 10px;
        }
        
        /* Profile overview */
        .profile-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .profile-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .profile-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .profile-card h3 {
            color: {{ colors.primary }};
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .profile-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: {{ colors.secondary }};
            margin-bottom: 5px;
        }
        
        .profile-card .label {
            color: #666;
            font-size: 0.9em;
        }
        
        /* Section styling */
        .section {
            margin-bottom: 50px;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: {{ colors.primary }};
            font-size: 1.8em;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid {{ colors.primary }};
            display: flex;
            align-items: center;
        }
        
        .section h2::before {
            content: '';
            width: 4px;
            height: 25px;
            background: {{ colors.accent }};
            margin-right: 15px;
        }
        
        .section h3 {
            color: {{ colors.secondary }};
            font-size: 1.4em;
            margin-bottom: 20px;
            margin-top: 30px;
        }
        
        /* Visualization containers */
        .visualization-container {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }
        
        .visualization-title {
            font-size: 1.2em;
            font-weight: 600;
            color: {{ colors.primary }};
            margin-bottom: 15px;
            text-align: center;
        }
        
        .visualization-content {
            min-height: 400px;
            background: white;
            border-radius: 8px;
            padding: 10px;
        }
        
        /* Insights styling */
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        
        .insight-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .insight-card h4 {
            color: {{ colors.primary }};
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .insight-card ul {
            padding-left: 20px;
        }
        
        .insight-card li {
            margin-bottom: 8px;
            line-height: 1.5;
        }
        
        /* Strength/Weakness indicators */
        .strength-indicator {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .strength {
            background: {{ colors.success }};
            color: white;
        }
        
        .weakness {
            background: {{ colors.accent }};
            color: white;
        }
        
        .moderate {
            background: {{ colors.warning }};
            color: white;
        }
        
        /* Development plan styling */
        .development-plan {
            background: linear-gradient(135deg, #e8f5e8, #f0f8f0);
            padding: 30px;
            border-radius: 10px;
            border-left: 5px solid {{ colors.success }};
            margin-top: 30px;
        }
        
        .development-item {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }
        
        .development-item h5 {
            color: {{ colors.primary }};
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .development-meta {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            font-size: 0.9em;
            color: #666;
        }
        
        .development-actions {
            margin-top: 15px;
        }
        
        .development-actions h6 {
            color: {{ colors.secondary }};
            margin-bottom: 10px;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 10px;
            color: #666;
        }
        
        /* Print styles */
        @media print {
            .header {
                margin: 0;
                page-break-inside: avoid;
            }
            
            .section {
                page-break-inside: avoid;
                break-inside: avoid;
            }
            
            .visualization-container {
                page-break-inside: avoid;
            }
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .profile-overview {
                grid-template-columns: 1fr;
            }
            
            .insights-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>Personality Assessment Report</h1>
            <div class="subtitle">{{ profile.name }}</div>
            <div class="meta-info">
                Generated on {{ generation_date }} | 
                Archetype: {{ profile.archetype }} ({{ profile.archetype_match }}% match)
            </div>
        </div>
        
        <!-- Executive Summary -->
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <p>This comprehensive personality assessment provides insights into {{ profile.name }}'s behavioral patterns, strengths, and development opportunities. The assessment identifies {{ profile.name }} as a <strong>{{ profile.archetype }}</strong> with a {{ profile.archetype_match }}% match, indicating strong alignment with this personality archetype.</p>
            
            <div class="profile-overview">
                <div class="profile-card">
                    <h3>Overall Score</h3>
                    <div class="value">{{ "%.1f"|format(profile.overall_score) }}</div>
                    <div class="label">out of 10</div>
                </div>
                <div class="profile-card">
                    <h3>Percentile Rank</h3>
                    <div class="value">{{ "%.0f"|format(profile.overall_percentile) }}</div>
                    <div class="label">percentile</div>
                </div>
                <div class="profile-card">
                    <h3>Archetype Match</h3>
                    <div class="value">{{ "%.0f"|format(profile.archetype_match) }}%</div>
                    <div class="label">{{ profile.archetype }}</div>
                </div>
                <div class="profile-card">
                    <h3>Traits Assessed</h3>
                    <div class="value">{{ profile.traits|length }}</div>
                    <div class="label">personality dimensions</div>
                </div>
            </div>
        </div>
        
        <!-- Interactive Radar Chart -->
        {% if visualizations.radar_chart %}
        <div class="section">
            <h2>Personality Profile Overview</h2>
            <div class="visualization-container">
                <div class="visualization-title">Interactive Radar Chart</div>
                <div class="visualization-content">
                    {{ visualizations.radar_chart|safe }}
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- Trait Gauges -->
        {% if visualizations.gauge_charts %}
        <div class="section">
            <h2>Individual Trait Analysis</h2>
            <div class="visualization-container">
                <div class="visualization-title">Trait Strength Meters</div>
                <div class="visualization-content">
                    {{ visualizations.gauge_charts|safe }}
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- Personality Breakdown -->
        {% if visualizations.personality_breakdown %}
        <div class="section">
            <h2>Comprehensive Personality Breakdown</h2>
            <div class="visualization-container">
                <div class="visualization-title">Multi-Dimensional Analysis</div>
                <div class="visualization-content">
                    {{ visualizations.personality_breakdown|safe }}
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- Strengths & Weaknesses -->
        <div class="section">
            <h2>Strengths & Development Areas</h2>
            
            {% if visualizations.strengths_weaknesses %}
            <div class="visualization-container">
                <div class="visualization-title">Strengths & Weaknesses Analysis</div>
                <div class="visualization-content">
                    {{ visualizations.strengths_weaknesses|safe }}
                </div>
            </div>
            {% endif %}
            
            <div class="insights-grid">
                <div class="insight-card">
                    <h4>Key Strengths</h4>
                    <ul>
                        {% for strength in insights.key_strengths %}
                        <li>
                            <strong>{{ strength.name }}</strong>
                            <span class="strength-indicator strength">{{ "%.0f"|format(strength.percentile) }}th</span>
                            <br>{{ strength.description }}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                
                <div class="insight-card">
                    <h4>Development Areas</h4>
                    <ul>
                        {% for weakness in insights.development_areas %}
                        <li>
                            <strong>{{ weakness.name }}</strong>
                            <span class="strength-indicator weakness">{{ "%.0f"|format(weakness.percentile) }}th</span>
                            <br>{{ weakness.description }}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Archetype Analysis -->
        {% if visualizations.archetype_analysis %}
        <div class="section">
            <h2>Archetype Analysis</h2>
            <div class="visualization-container">
                <div class="visualization-title">Archetype Matching & Comparison</div>
                <div class="visualization-content">
                    {{ visualizations.archetype_analysis|safe }}
                </div>
            </div>
            
            <div class="insights-grid">
                <div class="insight-card">
                    <h4>Leadership Style</h4>
                    <p>{{ insights.leadership_style }}</p>
                </div>
                
                <div class="insight-card">
                    <h4>Communication Preferences</h4>
                    <p>{{ insights.communication_preferences }}</p>
                </div>
                
                <div class="insight-card">
                    <h4>Work Environment</h4>
                    <p>{{ insights.work_environment }}</p>
                </div>
                
                <div class="insight-card">
                    <h4>Collaboration Style</h4>
                    <p>{{ insights.collaboration_style }}</p>
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- Heatmap Visualization -->
        {% if visualizations.heatmap %}
        <div class="section">
            <h2>Personality Heatmap</h2>
            <div class="visualization-container">
                <div class="visualization-title">Trait Intensity Mapping</div>
                <div class="visualization-content">
                    {{ visualizations.heatmap|safe }}
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- Development Plan -->
        {% if insights.development_plan %}
        <div class="section">
            <h2>Personalized Development Plan</h2>
            <div class="development-plan">
                <h3>Recommended Development Areas</h3>
                
                {% for item in insights.development_plan %}
                <div class="development-item">
                    <h5>{{ item.area }}</h5>
                    <div class="development-meta">
                        <span><strong>Current:</strong> {{ item.current_level }}</span>
                        <span><strong>Target:</strong> {{ item.target }}</span>
                        <span><strong>Timeline:</strong> {{ item.timeline }}</span>
                    </div>
                    
                    <div class="development-actions">
                        <h6>Recommended Actions:</h6>
                        <ul>
                            {% for action in item.actions %}
                            <li>{{ action }}</li>
                            {% endfor %}
                        </ul>
                        
                        <h6>Resources:</h6>
                        <ul>
                            {% for resource in item.resources %}
                            <li>{{ resource }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <!-- Footer -->
        <div class="footer">
            <p>This report was generated using advanced psychometric assessment algorithms.</p>
            <p>For questions about this report, please contact your assessment administrator.</p>
            <p><em>Generated on {{ generation_date }}</em></p>
        </div>
    </div>
</body>
</html>
        """
        
        return Template(template_content)
    
    def generate_batch_reports(self, profiles: List[PersonalityProfile],
                             config: ReportConfig = None) -> List[str]:
        """Generate reports for multiple profiles."""
        try:
            if not config:
                config = ReportConfig()
            
            generated_files = []
            
            for profile in profiles:
                # Use all other profiles as comparison population
                other_profiles = [p for p in profiles if p.person_id != profile.person_id]
                
                if config.format in ["html", "both"]:
                    html_file = self.generate_html_report(profile, config, None, other_profiles)
                    if html_file:
                        generated_files.append(html_file)
                
                if config.format in ["pdf", "both"]:
                    pdf_file = self.generate_pdf_report(profile, config, None, other_profiles)
                    if pdf_file:
                        generated_files.append(pdf_file)
            
            self.logger.info(f"Generated {len(generated_files)} reports")
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error generating batch reports: {e}")
            return []