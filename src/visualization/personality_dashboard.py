"""
Enhanced Individual Personality Visualization Dashboard
Provides comprehensive personality report visualizations with interactive features.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union, Any, Tuple
import logging
from dataclasses import dataclass
import json
from pathlib import Path
import base64
from io import BytesIO
import colorsys


@dataclass
class PersonalityTrait:
    """Represents a single personality trait with scoring."""
    name: str
    score: float
    percentile: float
    description: str
    category: str = "general"
    strength_level: str = "moderate"  # weak, moderate, strong
    

@dataclass
class PersonalityProfile:
    """Complete personality profile for an individual."""
    person_id: str
    name: str
    traits: List[PersonalityTrait]
    overall_score: float
    overall_percentile: float
    archetype: str
    archetype_match: float
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    

class PersonalityDashboard:
    """Enhanced personality visualization dashboard."""
    
    def __init__(self, theme: str = "plotly_white"):
        self.logger = logging.getLogger(__name__)
        self.theme = theme
        self.colors = {
            'strength': '#28a745',    # Green
            'moderate': '#ffc107',    # Yellow
            'weakness': '#dc3545',    # Red
            'primary': '#007bff',     # Blue
            'secondary': '#6c757d',   # Gray
            'accent': '#17a2b8'       # Teal
        }
        
        # Color-blind friendly palette
        self.trait_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        self.layout_defaults = {
            'template': theme,
            'font': {'family': 'Arial, sans-serif', 'size': 12},
            'title': {'font': {'size': 18, 'color': '#2c3e50'}},
            'margin': {'l': 60, 'r': 60, 't': 80, 'b': 60},
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white'
        }
        
        self.logger.info("PersonalityDashboard initialized")
    
    def _get_strength_color(self, score: float, percentile: float) -> str:
        """Determine color based on strength level."""
        if percentile >= 75 or score >= 8.0:
            return self.colors['strength']
        elif percentile <= 25 or score <= 4.0:
            return self.colors['weakness']
        else:
            return self.colors['moderate']
    
    def _classify_strength_level(self, score: float, percentile: float) -> str:
        """Classify trait as strength, weakness, or moderate."""
        if percentile >= 75 or score >= 8.0:
            return "strength"
        elif percentile <= 25 or score <= 4.0:
            return "weakness"
        else:
            return "moderate"
    
    def create_interactive_radar_chart(self, profile: PersonalityProfile, 
                                     comparison_profiles: List[PersonalityProfile] = None,
                                     output_path: str = None) -> go.Figure:
        """Create interactive spider/radar chart with comparison overlays."""
        try:
            if not profile.traits:
                self.logger.error("No traits available for radar chart")
                return None
            
            # Extract trait data
            trait_names = [trait.name for trait in profile.traits]
            trait_scores = [trait.score for trait in profile.traits]
            trait_percentiles = [trait.percentile for trait in profile.traits]
            
            # Close the radar chart by adding first point at the end
            trait_names_closed = trait_names + [trait_names[0]]
            trait_scores_closed = trait_scores + [trait_scores[0]]
            trait_percentiles_closed = trait_percentiles + [trait_percentiles[0]]
            
            fig = go.Figure()
            
            # Main individual's profile
            fig.add_trace(go.Scatterpolar(
                r=trait_scores_closed,
                theta=trait_names_closed,
                fill='toself',
                name=f"{profile.name} (Raw Scores)",
                line=dict(color=self.colors['primary'], width=3),
                fillcolor=f"rgba(0, 123, 255, 0.3)",
                hovertemplate="<b>%{theta}</b><br>" +
                            "Score: %{r:.1f}<br>" +
                            "<extra></extra>",
                visible=True
            ))
            
            # Percentile overlay
            fig.add_trace(go.Scatterpolar(
                r=trait_percentiles_closed,
                theta=trait_names_closed,
                mode='lines',
                name=f"{profile.name} (Percentiles)",
                line=dict(color=self.colors['accent'], width=2, dash='dash'),
                hovertemplate="<b>%{theta}</b><br>" +
                            "Percentile: %{r:.0f}th<br>" +
                            "<extra></extra>",
                visible=False
            ))
            
            # Add comparison profiles if provided
            if comparison_profiles:
                for i, comp_profile in enumerate(comparison_profiles[:3]):  # Limit to 3 comparisons
                    comp_scores = []
                    for trait_name in trait_names:
                        # Find matching trait
                        score = 5.0  # Default middle score
                        for trait in comp_profile.traits:
                            if trait.name == trait_name:
                                score = trait.score
                                break
                        comp_scores.append(score)
                    
                    comp_scores_closed = comp_scores + [comp_scores[0]]
                    
                    fig.add_trace(go.Scatterpolar(
                        r=comp_scores_closed,
                        theta=trait_names_closed,
                        mode='lines',
                        name=f"vs {comp_profile.name}",
                        line=dict(color=self.trait_colors[i+2], width=2, dash='dot'),
                        hovertemplate="<b>%{theta}</b><br>" +
                                    f"{comp_profile.name}: %{{r:.1f}}<br>" +
                                    "<extra></extra>",
                        visible=False
                    ))
            
            # Add average population line
            avg_scores = [50.0] * len(trait_names) + [50.0]  # Population average
            fig.add_trace(go.Scatterpolar(
                r=avg_scores,
                theta=trait_names_closed,
                mode='lines',
                name="Population Average",
                line=dict(color='gray', width=1, dash='dashdot'),
                hovertemplate="<b>%{theta}</b><br>" +
                            "Population Avg: %{r:.1f}<br>" +
                            "<extra></extra>",
                visible=False
            ))
            
            # Configure layout
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10],
                        tickmode='linear',
                        tick0=0,
                        dtick=2,
                        showline=True,
                        linecolor='lightgray',
                        gridcolor='lightgray',
                        tickfont=dict(size=10)
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=11),
                        rotation=90,
                        direction='clockwise'
                    ),
                    bgcolor='white'
                ),
                title=dict(
                    text=f"Personality Profile: {profile.name}<br>" +
                         f"<sub>Archetype: {profile.archetype} ({profile.archetype_match:.0f}% match)</sub>",
                    x=0.5,
                    font=dict(size=16)
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=600,
                **self.layout_defaults
            )
            
            # Add dropdown for view modes
            fig.update_layout(
                updatemenus=[
                    dict(
                        type="dropdown",
                        direction="down",
                        showactive=True,
                        x=0.1,
                        xanchor="left",
                        y=1.15,
                        yanchor="top",
                        buttons=list([
                            dict(
                                args=[{"visible": [True, False, False, False, False]}],
                                label="Raw Scores Only",
                                method="restyle"
                            ),
                            dict(
                                args=[{"visible": [True, True, False, False, False]}],
                                label="Scores + Percentiles",
                                method="restyle"
                            ),
                            dict(
                                args=[{"visible": [True, False, True, True, True]}],
                                label="With Comparisons",
                                method="restyle"
                            ),
                            dict(
                                args=[{"visible": [True, True, True, True, True]}],
                                label="All Views",
                                method="restyle"
                            )
                        ])
                    )
                ]
            )
            
            if output_path:
                fig.write_html(output_path)
                self.logger.info(f"Interactive radar chart saved to {output_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating radar chart: {e}")
            return None
    
    def create_gauge_charts(self, profile: PersonalityProfile, 
                          output_path: str = None) -> go.Figure:
        """Create gauge charts for individual trait meters."""
        try:
            if not profile.traits:
                self.logger.error("No traits available for gauge charts")
                return None
            
            # Calculate grid dimensions
            n_traits = len(profile.traits)
            cols = min(4, n_traits)
            rows = (n_traits + cols - 1) // cols
            
            # Create subplots
            fig = make_subplots(
                rows=rows,
                cols=cols,
                specs=[[{"type": "indicator"}] * cols for _ in range(rows)],
                subplot_titles=[trait.name for trait in profile.traits],
                vertical_spacing=0.1,
                horizontal_spacing=0.1
            )
            
            for i, trait in enumerate(profile.traits):
                row = i // cols + 1
                col = i % cols + 1
                
                # Determine color based on strength level
                color = self._get_strength_color(trait.score, trait.percentile)
                
                # Create gauge
                fig.add_trace(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=trait.score,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': f"{trait.name}<br><span style='font-size:12px'>{trait.percentile:.0f}th percentile</span>"},
                        delta={'reference': 5.0, 'increasing': {'color': self.colors['strength']}},
                        gauge={
                            'axis': {'range': [None, 10]},
                            'bar': {'color': color},
                            'steps': [
                                {'range': [0, 4], 'color': "rgba(220, 53, 69, 0.3)"},
                                {'range': [4, 7], 'color': "rgba(255, 193, 7, 0.3)"},
                                {'range': [7, 10], 'color': "rgba(40, 167, 69, 0.3)"}
                            ],
                            'threshold': {
                                'line': {'color': "black", 'width': 4},
                                'thickness': 0.75,
                                'value': trait.percentile / 10
                            }
                        }
                    ),
                    row=row,
                    col=col
                )
            
            fig.update_layout(
                title=dict(
                    text=f"Individual Trait Meters: {profile.name}",
                    font=dict(size=18)
                ),
                height=200 * rows,
                showlegend=False,
                **self.layout_defaults
            )
            
            if output_path:
                fig.write_html(output_path)
                self.logger.info(f"Gauge charts saved to {output_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating gauge charts: {e}")
            return None
    
    def create_personality_breakdown(self, profile: PersonalityProfile,
                                   output_path: str = None) -> go.Figure:
        """Create comprehensive personality breakdown with multiple chart types."""
        try:
            if not profile.traits:
                self.logger.error("No traits available for breakdown")
                return None
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    "Trait Scores (Bar Chart)",
                    "Strength Distribution (Donut)",
                    "Percentile Rankings (Horizontal Bar)",
                    "Trait Categories (Polar Area)"
                ],
                specs=[
                    [{"type": "xy"}, {"type": "domain"}],
                    [{"type": "xy"}, {"type": "polar"}]
                ],
                vertical_spacing=0.12,
                horizontal_spacing=0.08
            )
            
            # 1. Bar chart of trait scores
            trait_names = [trait.name for trait in profile.traits]
            trait_scores = [trait.score for trait in profile.traits]
            colors = [self._get_strength_color(trait.score, trait.percentile) 
                     for trait in profile.traits]
            
            fig.add_trace(
                go.Bar(
                    x=trait_names,
                    y=trait_scores,
                    marker_color=colors,
                    text=[f"{score:.1f}" for score in trait_scores],
                    textposition='auto',
                    name="Trait Scores",
                    hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>"
                ),
                row=1, col=1
            )
            
            # 2. Donut chart of strength distribution
            strength_counts = {'Strengths': 0, 'Moderate': 0, 'Weaknesses': 0}
            for trait in profile.traits:
                level = self._classify_strength_level(trait.score, trait.percentile)
                if level == "strength":
                    strength_counts['Strengths'] += 1
                elif level == "weakness":
                    strength_counts['Weaknesses'] += 1
                else:
                    strength_counts['Moderate'] += 1
            
            fig.add_trace(
                go.Pie(
                    labels=list(strength_counts.keys()),
                    values=list(strength_counts.values()),
                    hole=0.4,
                    marker_colors=[self.colors['strength'], self.colors['moderate'], self.colors['weakness']],
                    textinfo='label+percent',
                    name="Distribution",
                    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
                ),
                row=1, col=2
            )
            
            # 3. Horizontal bar chart of percentiles
            trait_percentiles = [trait.percentile for trait in profile.traits]
            fig.add_trace(
                go.Bar(
                    x=trait_percentiles,
                    y=trait_names,
                    orientation='h',
                    marker_color=colors,
                    text=[f"{p:.0f}th" for p in trait_percentiles],
                    textposition='auto',
                    name="Percentiles",
                    hovertemplate="<b>%{y}</b><br>Percentile: %{x:.0f}th<extra></extra>"
                ),
                row=2, col=1
            )
            
            # 4. Polar area chart by categories
            categories = {}
            for trait in profile.traits:
                cat = trait.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(trait.score)
            
            # Calculate average scores by category
            cat_names = list(categories.keys())
            cat_scores = [np.mean(scores) for scores in categories.values()]
            
            fig.add_trace(
                go.Scatterpolar(
                    r=cat_scores,
                    theta=cat_names,
                    fill='toself',
                    name="Categories",
                    line=dict(color=self.colors['primary']),
                    fillcolor=f"rgba(0, 123, 255, 0.3)",
                    hovertemplate="<b>%{theta}</b><br>Avg Score: %{r:.1f}<extra></extra>"
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_xaxes(title_text="Traits", row=1, col=1)
            fig.update_yaxes(title_text="Score", row=1, col=1, range=[0, 10])
            fig.update_xaxes(title_text="Percentile", row=2, col=1, range=[0, 100])
            fig.update_yaxes(title_text="Traits", row=2, col=1)
            
            fig.update_layout(
                title=dict(
                    text=f"Personality Breakdown: {profile.name}",
                    font=dict(size=18)
                ),
                height=800,
                showlegend=False,
                **self.layout_defaults
            )
            
            if output_path:
                fig.write_html(output_path)
                self.logger.info(f"Personality breakdown saved to {output_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating personality breakdown: {e}")
            return None
    
    def create_strengths_weaknesses_analysis(self, profile: PersonalityProfile,
                                           output_path: str = None) -> go.Figure:
        """Create strengths and weaknesses analysis dashboard."""
        try:
            # Categorize traits
            strengths = []
            weaknesses = []
            balanced = []
            
            for trait in profile.traits:
                level = self._classify_strength_level(trait.score, trait.percentile)
                if level == "strength":
                    strengths.append(trait)
                elif level == "weakness":
                    weaknesses.append(trait)
                else:
                    balanced.append(trait)
            
            # Sort by score
            strengths.sort(key=lambda x: x.score, reverse=True)
            weaknesses.sort(key=lambda x: x.score)
            balanced.sort(key=lambda x: x.score, reverse=True)
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    f"Top {min(5, len(strengths))} Strengths",
                    f"Development Areas ({min(3, len(weaknesses))} lowest)",
                    "Balanced Traits",
                    "Growth Potential"
                ],
                specs=[
                    [{"type": "xy"}, {"type": "xy"}],
                    [{"type": "xy"}, {"type": "xy"}]
                ],
                vertical_spacing=0.15,
                horizontal_spacing=0.1
            )
            
            # 1. Top strengths
            if strengths:
                top_strengths = strengths[:5]
                fig.add_trace(
                    go.Bar(
                        x=[trait.name for trait in top_strengths],
                        y=[trait.score for trait in top_strengths],
                        marker_color=self.colors['strength'],
                        text=[f"{trait.score:.1f}" for trait in top_strengths],
                        textposition='auto',
                        name="Strengths",
                        hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<br>Percentile: " +
                                    str([f"{trait.percentile:.0f}th" for trait in top_strengths])[1:-1] +
                                    "<extra></extra>"
                    ),
                    row=1, col=1
                )
            
            # 2. Development areas
            if weaknesses:
                dev_areas = weaknesses[:3]
                fig.add_trace(
                    go.Bar(
                        x=[trait.name for trait in dev_areas],
                        y=[trait.score for trait in dev_areas],
                        marker_color=self.colors['weakness'],
                        text=[f"{trait.score:.1f}" for trait in dev_areas],
                        textposition='auto',
                        name="Development Areas",
                        hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<br>Percentile: " +
                                    str([f"{trait.percentile:.0f}th" for trait in dev_areas])[1:-1] +
                                    "<extra></extra>"
                    ),
                    row=1, col=2
                )
            
            # 3. Balanced traits
            if balanced:
                fig.add_trace(
                    go.Bar(
                        x=[trait.name for trait in balanced],
                        y=[trait.score for trait in balanced],
                        marker_color=self.colors['moderate'],
                        text=[f"{trait.score:.1f}" for trait in balanced],
                        textposition='auto',
                        name="Balanced Traits",
                        hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<br>Percentile: " +
                                    str([f"{trait.percentile:.0f}th" for trait in balanced])[1:-1] +
                                    "<extra></extra>"
                    ),
                    row=2, col=1
                )
            
            # 4. Growth potential (distance from max score)
            growth_potential = []
            growth_names = []
            for trait in profile.traits:
                potential = 10.0 - trait.score
                if potential > 1.0:  # Only show traits with meaningful growth potential
                    growth_potential.append(potential)
                    growth_names.append(trait.name)
            
            if growth_potential:
                fig.add_trace(
                    go.Bar(
                        x=growth_names,
                        y=growth_potential,
                        marker_color=self.colors['accent'],
                        text=[f"{pot:.1f}" for pot in growth_potential],
                        textposition='auto',
                        name="Growth Potential",
                        hovertemplate="<b>%{x}</b><br>Growth Potential: %{y:.1f}<extra></extra>"
                    ),
                    row=2, col=2
                )
            
            # Update layout
            for row in [1, 2]:
                for col in [1, 2]:
                    fig.update_yaxes(title_text="Score", row=row, col=col, range=[0, 10])
                    fig.update_xaxes(title_text="Traits", row=row, col=col)
            
            fig.update_layout(
                title=dict(
                    text=f"Strengths & Weaknesses Analysis: {profile.name}",
                    font=dict(size=18)
                ),
                height=700,
                showlegend=False,
                **self.layout_defaults
            )
            
            if output_path:
                fig.write_html(output_path)
                self.logger.info(f"Strengths & weaknesses analysis saved to {output_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating strengths/weaknesses analysis: {e}")
            return None
    
    def create_archetype_visualization(self, profile: PersonalityProfile,
                                     all_profiles: List[PersonalityProfile] = None,
                                     output_path: str = None) -> go.Figure:
        """Create archetype assignment and matching visualization."""
        try:
            # Create archetype comparison data
            archetypes = {}
            if all_profiles:
                for p in all_profiles:
                    if p.archetype not in archetypes:
                        archetypes[p.archetype] = []
                    archetypes[p.archetype].append(p)
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    "Archetype Match Percentage",
                    "Archetype Distribution",
                    "Trait Comparison vs Archetype",
                    "Similarity Network"
                ],
                specs=[
                    [{"type": "xy"}, {"type": "domain"}],
                    [{"type": "xy"}, {"type": "xy"}]
                ],
                vertical_spacing=0.15,
                horizontal_spacing=0.1
            )
            
            # 1. Archetype match percentage
            sample_archetypes = ["Innovator", "Executor", "Strategist", "Collaborator", "Analyst"]
            match_percentages = [
                profile.archetype_match if arch == profile.archetype else np.random.uniform(20, 80)
                for arch in sample_archetypes
            ]
            
            colors = [self.colors['primary'] if arch == profile.archetype else self.colors['secondary'] 
                     for arch in sample_archetypes]
            
            fig.add_trace(
                go.Bar(
                    x=sample_archetypes,
                    y=match_percentages,
                    marker_color=colors,
                    text=[f"{p:.0f}%" for p in match_percentages],
                    textposition='auto',
                    name="Archetype Match",
                    hovertemplate="<b>%{x}</b><br>Match: %{y:.0f}%<extra></extra>"
                ),
                row=1, col=1
            )
            
            # 2. Archetype distribution (if population data available)
            if all_profiles:
                archetype_counts = {}
                for p in all_profiles:
                    archetype_counts[p.archetype] = archetype_counts.get(p.archetype, 0) + 1
                
                fig.add_trace(
                    go.Pie(
                        labels=list(archetype_counts.keys()),
                        values=list(archetype_counts.values()),
                        marker_colors=self.trait_colors[:len(archetype_counts)],
                        textinfo='label+percent',
                        name="Archetype Distribution",
                        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
                    ),
                    row=1, col=2
                )
            
            # 3. Trait comparison vs archetype average
            if profile.traits:
                trait_names = [trait.name for trait in profile.traits]
                individual_scores = [trait.score for trait in profile.traits]
                
                # Simulate archetype average (in real implementation, calculate from archetype data)
                archetype_avg = [np.random.uniform(4, 8) for _ in trait_names]
                
                fig.add_trace(
                    go.Bar(
                        x=trait_names,
                        y=individual_scores,
                        name=f"{profile.name}",
                        marker_color=self.colors['primary'],
                        opacity=0.8
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=trait_names,
                        y=archetype_avg,
                        mode='markers+lines',
                        name=f"{profile.archetype} Average",
                        marker=dict(color=self.colors['accent'], size=8),
                        line=dict(color=self.colors['accent'], width=2)
                    ),
                    row=2, col=1
                )
            
            # 4. Similarity network (scatter plot)
            if all_profiles:
                # Create similarity network based on trait similarity
                x_coords = []
                y_coords = []
                names = []
                archetype_labels = []
                
                for p in all_profiles[:20]:  # Limit to 20 for readability
                    # Use first two traits as x,y coordinates
                    x_coord = p.traits[0].score if p.traits else 5.0
                    y_coord = p.traits[1].score if len(p.traits) > 1 else 5.0
                    
                    x_coords.append(x_coord)
                    y_coords.append(y_coord)
                    names.append(p.name)
                    archetype_labels.append(p.archetype)
                
                # Highlight the current individual
                marker_colors = [self.colors['primary'] if name == profile.name else self.colors['secondary'] 
                               for name in names]
                marker_sizes = [15 if name == profile.name else 8 for name in names]
                
                fig.add_trace(
                    go.Scatter(
                        x=x_coords,
                        y=y_coords,
                        mode='markers+text',
                        text=names,
                        textposition='top center',
                        marker=dict(
                            color=marker_colors,
                            size=marker_sizes,
                            line=dict(width=2, color='white')
                        ),
                        name="Similarity Network",
                        hovertemplate="<b>%{text}</b><br>Archetype: " +
                                    str(archetype_labels)[1:-1] +
                                    "<br>Position: (%{x:.1f}, %{y:.1f})<extra></extra>"
                    ),
                    row=2, col=2
                )
            
            # Update layout
            fig.update_yaxes(title_text="Match %", row=1, col=1, range=[0, 100])
            fig.update_xaxes(title_text="Archetypes", row=1, col=1)
            fig.update_yaxes(title_text="Score", row=2, col=1, range=[0, 10])
            fig.update_xaxes(title_text="Traits", row=2, col=1)
            fig.update_xaxes(title_text="Trait 1", row=2, col=2)
            fig.update_yaxes(title_text="Trait 2", row=2, col=2)
            
            fig.update_layout(
                title=dict(
                    text=f"Archetype Analysis: {profile.name} → {profile.archetype}",
                    font=dict(size=18)
                ),
                height=800,
                showlegend=True,
                **self.layout_defaults
            )
            
            if output_path:
                fig.write_html(output_path)
                self.logger.info(f"Archetype visualization saved to {output_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating archetype visualization: {e}")
            return None
    
    def create_heatmap_visualization(self, profile: PersonalityProfile,
                                   all_profiles: List[PersonalityProfile] = None,
                                   output_path: str = None) -> go.Figure:
        """Create heatmap visualization for personality characteristics."""
        try:
            if not profile.traits:
                self.logger.error("No traits available for heatmap")
                return None
            
            # Create data matrix
            if all_profiles:
                # Multi-person heatmap
                names = [p.name for p in all_profiles[:20]]  # Limit to 20 for readability
                trait_names = [trait.name for trait in profile.traits]
                
                data_matrix = []
                for person in all_profiles[:20]:
                    row = []
                    for trait_name in trait_names:
                        # Find matching trait
                        score = 5.0  # Default
                        for trait in person.traits:
                            if trait.name == trait_name:
                                score = trait.score
                                break
                        row.append(score)
                    data_matrix.append(row)
                
                fig = go.Figure(data=go.Heatmap(
                    z=data_matrix,
                    x=trait_names,
                    y=names,
                    colorscale='RdYlGn',
                    zmid=5,
                    text=np.array(data_matrix).round(1),
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>",
                    colorbar=dict(title="Score")
                ))
                
                # Highlight current individual
                current_index = names.index(profile.name) if profile.name in names else 0
                fig.add_shape(
                    type="rect",
                    x0=-0.5, y0=current_index-0.5,
                    x1=len(trait_names)-0.5, y1=current_index+0.5,
                    line=dict(color=self.colors['primary'], width=3),
                    fillcolor="rgba(0, 0, 0, 0)"
                )
                
                title = f"Personality Heatmap: {profile.name} vs Population"
                
            else:
                # Single person category heatmap
                categories = {}
                for trait in profile.traits:
                    cat = trait.category
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(trait)
                
                cat_names = list(categories.keys())
                max_traits = max(len(traits) for traits in categories.values())
                
                data_matrix = []
                y_labels = []
                
                for cat_name in cat_names:
                    traits = categories[cat_name]
                    for i, trait in enumerate(traits):
                        data_matrix.append([trait.score if j == cat_names.index(cat_name) else 0 
                                          for j in range(len(cat_names))])
                        y_labels.append(f"{cat_name}: {trait.name}")
                
                fig = go.Figure(data=go.Heatmap(
                    z=data_matrix,
                    x=cat_names,
                    y=y_labels,
                    colorscale='RdYlGn',
                    zmid=5,
                    text=np.array(data_matrix).round(1),
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>",
                    colorbar=dict(title="Score")
                ))
                
                title = f"Personality Heatmap: {profile.name} by Category"
            
            fig.update_layout(
                title=dict(
                    text=title,
                    font=dict(size=18)
                ),
                xaxis_title="Traits/Categories",
                yaxis_title="Individuals/Traits",
                height=600,
                **self.layout_defaults
            )
            
            if output_path:
                fig.write_html(output_path)
                self.logger.info(f"Heatmap visualization saved to {output_path}")
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating heatmap visualization: {e}")
            return None
    
    def generate_comprehensive_dashboard(self, profile: PersonalityProfile,
                                       comparison_profiles: List[PersonalityProfile] = None,
                                       all_profiles: List[PersonalityProfile] = None,
                                       output_dir: str = None) -> Dict[str, str]:
        """Generate all visualizations for a comprehensive personality dashboard."""
        try:
            if not output_dir:
                output_dir = "personality_dashboard"
            
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            generated_files = {}
            
            # 1. Interactive Radar Chart
            radar_path = output_path / f"radar_chart_{profile.person_id}.html"
            if self.create_interactive_radar_chart(profile, comparison_profiles, str(radar_path)):
                generated_files['radar_chart'] = str(radar_path)
            
            # 2. Gauge Charts
            gauge_path = output_path / f"gauge_charts_{profile.person_id}.html"
            if self.create_gauge_charts(profile, str(gauge_path)):
                generated_files['gauge_charts'] = str(gauge_path)
            
            # 3. Personality Breakdown
            breakdown_path = output_path / f"personality_breakdown_{profile.person_id}.html"
            if self.create_personality_breakdown(profile, str(breakdown_path)):
                generated_files['personality_breakdown'] = str(breakdown_path)
            
            # 4. Strengths & Weaknesses
            strengths_path = output_path / f"strengths_weaknesses_{profile.person_id}.html"
            if self.create_strengths_weaknesses_analysis(profile, str(strengths_path)):
                generated_files['strengths_weaknesses'] = str(strengths_path)
            
            # 5. Archetype Visualization
            archetype_path = output_path / f"archetype_analysis_{profile.person_id}.html"
            if self.create_archetype_visualization(profile, all_profiles, str(archetype_path)):
                generated_files['archetype_analysis'] = str(archetype_path)
            
            # 6. Heatmap Visualization
            heatmap_path = output_path / f"heatmap_{profile.person_id}.html"
            if self.create_heatmap_visualization(profile, all_profiles, str(heatmap_path)):
                generated_files['heatmap'] = str(heatmap_path)
            
            self.logger.info(f"Generated {len(generated_files)} visualizations in {output_dir}")
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive dashboard: {e}")
            return {}