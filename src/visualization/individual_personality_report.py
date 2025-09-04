"""
Individual Personality Visualization Report System
Comprehensive personality visualization with radar charts, bar charts, and gauge charts
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class PersonalityTrait:
    """Represents a single personality trait with score and metadata."""
    name: str
    score: float
    percentile: Optional[float] = None
    description: str = ""
    category: str = ""
    
@dataclass
class PersonalityProfile:
    """Complete personality profile for an individual."""
    person_id: str
    person_name: str
    traits: List[PersonalityTrait]
    overall_score: float
    archetype: str = ""
    completion_date: str = ""

class IndividualPersonalityVisualizer:
    """
    Creates comprehensive individual personality visualization reports
    with radar charts, bar charts, and gauge charts.
    """
    
    def __init__(self, theme: str = "plotly_white"):
        """
        Initialize the personality visualizer.
        
        Args:
            theme: Plotly theme to use for charts
        """
        self.theme = theme
        self.logger = logging.getLogger(__name__)
        
        # Color schemes
        self.colors = {
            'primary': '#4285f4',
            'strength': '#00aa44',
            'moderate': '#ffaa00', 
            'development': '#ff4444',
            'grid': '#e0e0e0',
            'text': '#333333',
            'subtitle': '#666666'
        }
        
        # Score thresholds
        self.thresholds = {
            'strength': 0.7,
            'moderate_low': 0.4,
            'moderate_high': 0.7
        }
        
        self.logger.info("IndividualPersonalityVisualizer initialized")
    
    def create_radar_chart(self, profile: PersonalityProfile, 
                          population_avg: Optional[Dict[str, float]] = None) -> go.Figure:
        """
        Create enhanced radar chart with all specifications.
        
        Args:
            profile: Individual personality profile
            population_avg: Population averages for comparison
            
        Returns:
            Plotly figure object
        """
        # Prepare data
        traits = [trait.name for trait in profile.traits]
        scores = [trait.score * 100 for trait in profile.traits]  # Convert to 0-100 scale
        
        # Create radar chart
        fig = go.Figure()
        
        # Add main data trace
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=traits,
            fill='toself',
            fillcolor=f'rgba(66, 133, 244, 0.3)',  # Semi-transparent blue
            line=dict(color=self.colors['primary'], width=2),
            marker=dict(
                size=8,
                color=self.colors['primary'],
                symbol='circle'
            ),
            name=f'{profile.person_name} Profile',
            hovertemplate='<b>%{theta}</b><br>Score: %{r:.1f}<br><extra></extra>'
        ))
        
        # Add population average if provided
        if population_avg:
            avg_scores = [population_avg.get(trait, 50) for trait in traits]
            fig.add_trace(go.Scatterpolar(
                r=avg_scores,
                theta=traits,
                mode='lines',
                line=dict(color='gray', width=1, dash='dash'),
                name='Population Average',
                hovertemplate='<b>%{theta}</b><br>Average: %{r:.1f}<br><extra></extra>'
            ))
        
        # Configure layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[0, 20, 40, 60, 80, 100],
                    ticktext=['0', '20', '40', '60', '80', '100'],
                    tickfont=dict(size=10, color=self.colors['text']),
                    gridcolor=self.colors['grid'],
                    gridwidth=1
                ),
                angularaxis=dict(
                    tickfont=dict(size=12, color='#1f4e79'),  # Dark blue
                    rotation=90,
                    direction='clockwise'
                ),
                bgcolor='white'
            ),
            showlegend=True,
            title=dict(
                text=f'<b>Trait Profile Radar Chart</b><br><span style="font-size:14px; color:{self.colors["subtitle"]}">{profile.person_name} ({profile.person_id})</span>',
                x=0.5,
                font=dict(size=18, color=self.colors['text'])
            ),
            template=self.theme,
            width=600,
            height=600,
            margin=dict(l=80, r=80, t=100, b=80)
        )
        
        return fig
    
    def create_trait_breakdown_chart(self, profile: PersonalityProfile) -> go.Figure:
        """
        Create individual trait breakdown bar chart.
        
        Args:
            profile: Individual personality profile
            
        Returns:
            Plotly figure object
        """
        # Prepare data
        traits = [trait.name for trait in profile.traits]
        scores = [trait.score for trait in profile.traits]
        
        # Determine colors based on score thresholds
        colors = []
        for score in scores:
            if score >= self.thresholds['strength']:
                colors.append(self.colors['strength'])
            elif score >= self.thresholds['moderate_low']:
                colors.append(self.colors['moderate'])
            else:
                colors.append(self.colors['development'])
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=traits,
            y=scores,
            marker_color=colors,
            text=[f'{score:.2f}' for score in scores],
            textposition='outside',
            textfont=dict(size=10, color=self.colors['text']),
            hovertemplate='<b>%{x}</b><br>Score: %{y:.2f}<br><extra></extra>'
        ))
        
        # Add average benchmark line
        avg_score = np.mean(scores)
        fig.add_hline(
            y=avg_score,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Average: {avg_score:.2f}",
            annotation_position="top right"
        )
        
        # Configure layout
        fig.update_layout(
            title=dict(
                text='<b>Individual Trait Breakdown</b>',
                x=0.5,
                font=dict(size=16, color=self.colors['text'])
            ),
            xaxis=dict(
                title='Traits',
                tickangle=45,
                tickfont=dict(size=10),
                gridcolor=self.colors['grid']
            ),
            yaxis=dict(
                title='Score (0.0 - 1.0)',
                range=[0, 1.0],
                tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                gridcolor=self.colors['grid']
            ),
            template=self.theme,
            showlegend=False,
            height=500,
            margin=dict(l=60, r=60, t=80, b=120)
        )
        
        return fig
    
    def create_strengths_development_chart(self, profile: PersonalityProfile) -> go.Figure:
        """
        Create side-by-side strengths vs development areas chart.
        
        Args:
            profile: Individual personality profile
            
        Returns:
            Plotly figure object
        """
        # Sort traits by score
        sorted_traits = sorted(profile.traits, key=lambda x: x.score, reverse=True)
        
        # Get top 5 strengths and bottom 5 development areas
        strengths = sorted_traits[:5]
        development = sorted_traits[-5:]
        
        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Top 5 Strengths', 'Key Development Areas'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]],
            horizontal_spacing=0.15
        )
        
        # Add strengths chart (left panel)
        fig.add_trace(
            go.Bar(
                y=[trait.name for trait in strengths],
                x=[trait.score for trait in strengths],
                orientation='h',
                marker_color=self.colors['strength'],
                text=[f'{trait.score:.2f}' for trait in strengths],
                textposition='outside',
                textfont=dict(size=10),
                name='Strengths',
                hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<br><extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add development areas chart (right panel)
        fig.add_trace(
            go.Bar(
                y=[trait.name for trait in development],
                x=[trait.score for trait in development],
                orientation='h',
                marker_color=self.colors['moderate'],
                text=[f'{trait.score:.2f}' for trait in development],
                textposition='outside',
                textfont=dict(size=10),
                name='Development Areas',
                hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<br><extra></extra>'
            ),
            row=1, col=2
        )
        
        # Configure layout
        fig.update_layout(
            title=dict(
                text='<b>Strengths Vs Development Areas</b>',
                x=0.5,
                font=dict(size=16, color=self.colors['text'])
            ),
            showlegend=False,
            template=self.theme,
            height=400,
            margin=dict(l=120, r=120, t=80, b=60)
        )
        
        # Update x-axes
        fig.update_xaxes(
            title_text="Score",
            range=[0, 1.0],
            tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            gridcolor=self.colors['grid'],
            row=1, col=1
        )
        fig.update_xaxes(
            title_text="Score",
            range=[0, 1.0],
            tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            gridcolor=self.colors['grid'],
            row=1, col=2
        )
        
        # Update y-axes
        fig.update_yaxes(
            tickfont=dict(size=10),
            row=1, col=1
        )
        fig.update_yaxes(
            tickfont=dict(size=10),
            row=1, col=2
        )
        
        return fig
    
    def create_gauge_chart(self, trait_name: str, value: float, 
                          title: str = None) -> go.Figure:
        """
        Create gauge chart for a key trait.
        
        Args:
            trait_name: Name of the trait
            value: Score value (0.0 to 1.0)
            title: Custom title for the gauge
            
        Returns:
            Plotly figure object
        """
        if title is None:
            title = f"{trait_name} Effectiveness"
        
        # Convert to 0-100 scale for display
        display_value = value * 100
        
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=display_value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"<b>{title}</b>", 'font': {'size': 16}},
            number={'font': {'size': 20}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': self.colors['primary']},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 30], 'color': self.colors['development']},
                    {'range': [30, 70], 'color': self.colors['moderate']},
                    {'range': [70, 100], 'color': self.colors['strength']}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            template=self.theme,
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            annotations=[
                dict(
                    text="Needs Development",
                    x=0.15, y=0.1,
                    showarrow=False,
                    font=dict(size=10, color=self.colors['development'])
                ),
                dict(
                    text="Developing",
                    x=0.5, y=0.1,
                    showarrow=False,
                    font=dict(size=10, color=self.colors['moderate'])
                ),
                dict(
                    text="Strength",
                    x=0.85, y=0.1,
                    showarrow=False,
                    font=dict(size=10, color=self.colors['strength'])
                )
            ]
        )
        
        return fig
    
    def generate_comprehensive_report(self, profile: PersonalityProfile,
                                    population_avg: Optional[Dict[str, float]] = None,
                                    output_path: str = None,
                                    generate_pdf: bool = False) -> str:
        """
        Generate comprehensive HTML report with all visualizations.
        
        Args:
            profile: Individual personality profile
            population_avg: Population averages for comparison
            output_path: Path to save the HTML report
            
        Returns:
            Path to generated HTML file
        """
        if output_path is None:
            output_path = f"output/personality_report_{profile.person_id}.html"
        
        # Create all visualizations
        radar_fig = self.create_radar_chart(profile, population_avg)
        breakdown_fig = self.create_trait_breakdown_chart(profile)
        strengths_fig = self.create_strengths_development_chart(profile)
        
        # Create gauge charts for top 3 traits
        sorted_traits = sorted(profile.traits, key=lambda x: x.score, reverse=True)
        gauge_figures = []
        for trait in sorted_traits[:3]:
            gauge_fig = self.create_gauge_chart(trait.name, trait.score)
            gauge_figures.append(gauge_fig)
        
        # Generate HTML report
        html_content = self._generate_html_template(
            profile, radar_fig, breakdown_fig, strengths_fig, gauge_figures
        )
        
        # Save to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Comprehensive personality report saved to {output_path}")
        
        # Generate PDF if requested
        if generate_pdf:
            pdf_path = output_path.replace('.html', '.pdf')
            self._generate_pdf_report(html_content, pdf_path)
        
        return output_path
    
    def _generate_html_template(self, profile: PersonalityProfile,
                               radar_fig: go.Figure,
                               breakdown_fig: go.Figure,
                               strengths_fig: go.Figure,
                               gauge_figures: List[go.Figure]) -> str:
        """Generate HTML template with all visualizations."""
        
        # Convert figures to HTML
        radar_html = radar_fig.to_html(full_html=False, include_plotlyjs=False)
        breakdown_html = breakdown_fig.to_html(full_html=False, include_plotlyjs=False)
        strengths_html = strengths_fig.to_html(full_html=False, include_plotlyjs=False)
        
        gauge_htmls = []
        for gauge_fig in gauge_figures:
            gauge_html = gauge_fig.to_html(full_html=False, include_plotlyjs=False)
            gauge_htmls.append(gauge_html)
        
        # Calculate summary statistics
        scores = [trait.score for trait in profile.traits]
        avg_score = np.mean(scores)
        strengths_count = len([s for s in scores if s >= self.thresholds['strength']])
        development_count = len([s for s in scores if s < self.thresholds['moderate_low']])
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personality Report - {profile.person_name}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 3px solid #4285f4;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #4285f4;
            font-size: 2.5em;
            margin: 0;
        }}
        .header p {{
            color: #666;
            font-size: 1.1em;
            margin: 10px 0;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .summary-item {{
            text-align: center;
            padding: 15px;
            background-color: white;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .summary-item h3 {{
            color: #4285f4;
            margin: 0 0 10px 0;
            font-size: 1.8em;
        }}
        .summary-item p {{
            color: #666;
            margin: 0;
        }}
        .chart-section {{
            margin-bottom: 40px;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 5px rgba(0,0,0,0.1);
        }}
        .gauge-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .insights {{
            background-color: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4285f4;
        }}
        .insights h3 {{
            color: #4285f4;
            margin-top: 0;
        }}
        .insight-item {{
            margin-bottom: 15px;
            padding: 10px;
            background-color: white;
            border-radius: 4px;
        }}
        .strength {{ color: #00aa44; font-weight: bold; }}
        .development {{ color: #ff4444; font-weight: bold; }}
        .moderate {{ color: #ffaa00; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Individual Personality Report</h1>
            <p><strong>{profile.person_name}</strong> (ID: {profile.person_id})</p>
            <p>Assessment Date: {profile.completion_date or 'N/A'} | Archetype: {profile.archetype or 'N/A'}</p>
        </div>

        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <h3>{avg_score:.2f}</h3>
                    <p>Overall Score</p>
                </div>
                <div class="summary-item">
                    <h3>{strengths_count}</h3>
                    <p>Key Strengths</p>
                </div>
                <div class="summary-item">
                    <h3>{development_count}</h3>
                    <p>Development Areas</p>
                </div>
                <div class="summary-item">
                    <h3>{len(profile.traits)}</h3>
                    <p>Traits Assessed</p>
                </div>
            </div>
        </div>

        <div class="chart-section">
            <div class="chart-container">
                <h2>Primary Visualization</h2>
                {radar_html}
            </div>
        </div>

        <div class="chart-section">
            <div class="chart-container">
                {breakdown_html}
            </div>
        </div>

        <div class="chart-section">
            <div class="chart-container">
                {strengths_html}
            </div>
        </div>

        <div class="chart-section">
            <h2>Key Trait Analysis</h2>
            <div class="gauge-grid">
                {"".join(f'<div class="chart-container">{gauge_html}</div>' for gauge_html in gauge_htmls)}
            </div>
        </div>

        <div class="insights">
            <h3>Key Insights & Recommendations</h3>
            {self._generate_insights_html(profile)}
        </div>
    </div>
</body>
</html>
"""
        return html_template
    
    def _generate_insights_html(self, profile: PersonalityProfile) -> str:
        """Generate insights and recommendations based on profile."""
        sorted_traits = sorted(profile.traits, key=lambda x: x.score, reverse=True)
        
        insights = []
        
        # Top strengths
        top_strengths = [t for t in sorted_traits[:3] if t.score >= self.thresholds['strength']]
        if top_strengths:
            strength_names = ", ".join([t.name for t in top_strengths])
            insights.append(f'<div class="insight-item"><span class="strength">Strengths:</span> {strength_names} are key areas of excellence that should be leveraged in leadership roles.</div>')
        
        # Development areas
        development_areas = [t for t in sorted_traits[-3:] if t.score < self.thresholds['moderate_low']]
        if development_areas:
            dev_names = ", ".join([t.name for t in development_areas])
            insights.append(f'<div class="insight-item"><span class="development">Development Focus:</span> {dev_names} represent opportunities for growth and skill enhancement.</div>')
        
        # Moderate areas
        moderate_areas = [t for t in sorted_traits if self.thresholds['moderate_low'] <= t.score < self.thresholds['strength']]
        if moderate_areas:
            mod_names = ", ".join([t.name for t in moderate_areas[:2]])
            insights.append(f'<div class="insight-item"><span class="moderate">Balanced Areas:</span> {mod_names} show solid foundation with room for strategic improvement.</div>')
        
        return "".join(insights)
    
    def _generate_pdf_report(self, html_content: str, output_path: str) -> bool:
        """Generate PDF report from HTML content."""
        try:
            # Import PDF generator
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            
            from reports.pdf_generator import PsychometricPDFGenerator
            
            # Generate PDF
            pdf_generator = PsychometricPDFGenerator()
            success = pdf_generator.html_to_pdf_enhanced(html_content, output_path)
            
            if success:
                self.logger.info(f"PDF report generated: {output_path}")
                print(f"✅ PDF report generated: {output_path}")
            else:
                self.logger.warning(f"PDF generation failed, HTML report available")
                print(f"❌ PDF generation failed, HTML report available")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            print(f"❌ Error generating PDF report: {e}")
            return False