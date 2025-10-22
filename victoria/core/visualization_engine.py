"""
Visualization Engine - Creates all visualizations for the report
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class VisualizationEngine:
    """
    Generates all visualizations for the Victoria assessment report
    """
    
    def __init__(self):
        """Initialize visualization engine"""
        self.colors = {
            'primary': '#570F27',      # Burgundy
            'secondary': '#151A4A',    # Navy
            'accent': '#FFDC58',       # Yellow
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        }
        
        self.trait_names = [
            'IN', 'DM', 'RB', 'N', 'CT', 'PS', 'A',
            'EI', 'C', 'TB', 'SL', 'AD', 'F', 'RG', 'IO', 'DA', 'RT'
        ]
        
        self.trait_descriptions = {
            'IN': 'Introversion and Extroversion',
            'DM': 'Decision-Making',
            'RB': 'Relationship-Building',
            'N': 'Negotiation',
            'CT': 'Critical Thinking',
            'PS': 'Problem-Solving',
            'A': 'Accountability',
            'EI': 'Emotional Intelligence',
            'C': 'Conflict Resolution',
            'TB': 'Team Building',
            'SL': 'Servant Leadership',
            'AD': 'Adaptability',
            'F': 'Approach to Failure',
            'RG': 'Resilience and Grit',
            'IO': 'Innovation Orientation',
            'DA': 'Drive and Ambition',
            'RT': 'Risk-Taking'
        }
    
    def create_archetype_heatmap(self, profile_data: Dict[str, Any]) -> str:
        """Create archetype-trait heatmap showing correlation scores"""
        try:
            # Define trait names in exact order (matching the heatmap)
            trait_names = [
                'Resilience & Grit', 'Servant Leadership', 'Emotional Intelligence',
                'Decision Making', 'Problem Solving', 'Drive & Ambition',
                'Innovation & Orientation', 'Adaptability', 'Critical Thinking',
                'Team Building', 'Risk Taking', 'Accountability'
            ]
            
            # Define archetypes in exact order
            archetypes = [
                'Adaptive Intelligence', 'Ambitious Drive', 'Collaborative Responsibility', 
                'Resilient Leadership', 'Strategic Innovation'
            ]
            
            # Get archetype correlation data
            from victoria.core.archetype_detector import ArchetypeDetector
            detector = ArchetypeDetector()
            correlation_data = detector.get_archetype_correlation_data()
            
            # Create trait score matrix and text matrix
            trait_score_matrix = []
            text_matrix = []
            
            for archetype in archetypes:
                # Get correlation scores for this archetype
                correlation_scores = correlation_data.get(archetype, [0.0] * len(trait_names))
                score_row = []
                text_row = []
                
                for i, trait_name in enumerate(trait_names):
                    score = correlation_scores[i] if i < len(correlation_scores) else 0.0
                    score_row.append(score)
                    text_row.append(f"{score:.2f}")
                
                trait_score_matrix.append(score_row)
                text_matrix.append(text_row)
            
            # Debug: Print the text matrix to ensure it's populated
            logger.info(f"Text matrix: {text_matrix}")
            logger.info(f"Trait names: {trait_names}")
            logger.info(f"Archetypes: {archetypes}")
            
            # Create heatmap
            heatmap_data = go.Heatmap(
                z=trait_score_matrix,
                x=trait_names,
                y=archetypes,
                text=text_matrix,
                texttemplate="%{text}",
                textfont={"color": "black", "size": 12, "family": "Arial, sans-serif", "weight": "bold"},
                hovertext=text_matrix,
                hoverinfo="text",
                colorscale=[
                    [0.0, '#FFFFFF'], [0.2, '#E6F3FF'], [0.4, '#CCE7FF'],
                    [0.6, '#99CFFF'], [0.8, '#66B7FF'], [1.0, '#339FFF']
                ],
                zmin=0,
                zmax=1,
                showscale=True,
                colorbar=dict(
                    title="Trait<br>Score",
                    tickmode="array",
                    tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    ticktext=["Low", "Low-Med", "Medium", "High", "Very High", "Perfect"],
                    len=0.8, thickness=25, x=1.02, xpad=10
                ),
                hovertemplate="<b>%{y}</b><br>%{x}<br>Trait Score: %{z:.2f}<br><extra></extra>"
            )
            
            fig = go.Figure(data=heatmap_data)
            
            # Add annotations for each cell to ensure text is visible
            annotations = []
            for i, archetype in enumerate(archetypes):
                for j, trait in enumerate(trait_names):
                    annotations.append(
                        dict(
                            x=j, y=i,
                            text=text_matrix[i][j],
                            showarrow=False,
                            font=dict(color="black", size=12, family="Arial, sans-serif"),
                            xref="x", yref="y"
                        )
                    )
            
            # Add highlighting for detected archetype
            detected_archetype = profile_data.get('archetype_name', 'Resilient Leadership')
            if detected_archetype in archetypes:
                resilient_leadership_index = archetypes.index(detected_archetype)
                for j in range(len(trait_names)):
                    fig.add_shape(
                        type="rect",
                        x0=j-0.5, x1=j+0.5,
                        y0=resilient_leadership_index-0.5, y1=resilient_leadership_index+0.5,
                        line=dict(color="black", width=3),
                        fillcolor="rgba(0,0,0,0)",
                        layer="above"
                    )
            
            fig.update_layout(
                title=dict(
                    text=f"Trait Scores by Archetype<br><sub>Detected: {detected_archetype} (Highlighted)</sub>",
                    font=dict(size=14, color="#2c3e50"), x=0.5
                ),
                xaxis=dict(title="Personality Traits", tickfont=dict(size=9), 
                          title_font=dict(size=11), tickangle=45),
                yaxis=dict(title="Entrepreneurial Archetypes", tickfont=dict(size=9), 
                          title_font=dict(size=11)),
                font=dict(family="Arial, sans-serif"),
                margin=dict(l=80, r=40, t=60, b=80),
                height=400, width=800,
                paper_bgcolor="#FEFEFE", plot_bgcolor="#FAFAFA",
                autosize=True,
                annotations=annotations
            )
            
            return fig.to_html(include_plotlyjs=False, div_id="archetype-heatmap", full_html=False)
            
        except Exception as e:
            logger.error(f"Error creating archetype heatmap: {e}")
            return '<div>Correlation heatmap unavailable</div>'
    
    def create_trait_radar_chart(self, trait_scores: Dict[str, float]) -> str:
        """Create radar chart for trait scores"""
        try:
            # Prepare data
            categories = [self.trait_descriptions.get(trait, trait) for trait in self.trait_names]
            values = [trait_scores.get(trait, 0) for trait in self.trait_names]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Trait Scores',
                line_color=self.colors['primary'],
                fillcolor=f"rgba(87, 15, 39, 0.3)"
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1],
                        tickfont=dict(size=10)
                    )
                ),
                showlegend=True,
                title="Trait Profile Radar Chart",
                font=dict(family="Arial, sans-serif"),
                height=500,
                width=600
            )
            
            return fig.to_html(include_plotlyjs=False, div_id="trait-radar", full_html=False)
            
        except Exception as e:
            logger.error(f"Error creating radar chart: {e}")
            return '<div>Radar chart unavailable</div>'
    
    def create_trait_bar_chart(self, trait_scores: Dict[str, float]) -> str:
        """Create bar chart for trait scores"""
        try:
            # Sort traits by score
            sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)
            traits, scores = zip(*sorted_traits)
            
            # Debug: Print all traits being processed
            logger.info(f"Bar chart processing {len(traits)} traits: {list(traits)}")
            logger.info(f"Trait scores: {dict(zip(traits, scores))}")
            
            # Define colors based on score levels
            def get_score_color(score):
                if score >= 0.70:  # Adjusted threshold for green
                    return '#2E8B57'  # High scores - Green
                elif score >= 0.50:  # Adjusted threshold for orange
                    return '#FFA500'  # Medium scores - Orange
                else:
                    return '#DC143C'  # Low scores - Red
            
            # Create color array
            colors = [get_score_color(score) for score in scores]
            
            # Ensure all traits are included with proper names
            trait_labels = []
            for trait in traits:
                if trait in self.trait_descriptions:
                    trait_labels.append(self.trait_descriptions[trait])
                else:
                    trait_labels.append(trait)  # Fallback to trait code if not found
                    logger.warning(f"Trait {trait} not found in trait_descriptions")
            
            # Debug: Print final trait labels
            logger.info(f"Final trait labels for bar chart: {len(trait_labels)} traits")
            logger.info(f"Trait labels: {trait_labels}")
            
            # Debug: Print data being passed to Plotly
            logger.info(f"Plotly data - x (scores): {len(list(scores))} values")
            logger.info(f"Plotly data - y (labels): {len(trait_labels)} values")
            logger.info(f"Plotly data - colors: {len(colors)} values")
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=list(scores),
                    y=trait_labels,
                    orientation='h',
                    marker_color=colors,
                    text=[f"{score:.2f}" for score in scores],
                    textposition='inside',
                    textfont=dict(color='white', size=11, weight='bold')
                )
            ])
            
            # Add legend annotations
            fig.add_annotation(
                x=0.98, y=0.98,
                xref="paper", yref="paper",
                text="<b>Score Levels:</b><br><span style='color:#2E8B57'>●</span> High (≥0.70)<br><span style='color:#FFA500'>●</span> Medium (0.50-0.70)<br><span style='color:#DC143C'>●</span> Low (<0.50)",
                showarrow=False,
                align="right",
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="gray",
                borderwidth=1,
                font=dict(size=11),
                xanchor="right",
                yanchor="top"
            )
            
            # Calculate dynamic height based on number of traits
            num_traits = len(traits)
            bar_height = 30  # Further reduced height per bar
            min_height = 400  # Further reduced minimum height
            calculated_height = max(min_height, num_traits * bar_height + 100)
            
            fig.update_layout(
                title="Trait Scores Ranking",
                xaxis_title="Score",
                yaxis_title="Traits",
                font=dict(family="Arial, sans-serif"),
                height=calculated_height,
                width=900,
                margin=dict(l=180, r=60, t=40, b=40),  # Further reduced margins
                showlegend=False
            )
            
            return fig.to_html(include_plotlyjs=False, div_id="trait-bars", full_html=False)
            
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}")
            return '<div>Bar chart unavailable</div>'
    
    def create_top_trait_gauges(self, trait_scores: Dict[str, float]) -> str:
        """Create gauges for top 3 traits"""
        try:
            # Get top 3 traits
            sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
            fig = make_subplots(
                rows=1, cols=3,
                specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
            )
            
            for i, (trait, score) in enumerate(sorted_traits, 1):
                trait_name = self.trait_descriptions.get(trait, trait)
                percentage = round(score * 100, 1)
                
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=percentage,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': trait_name, 'font': {'size': 10}},
                    gauge={
                        'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': "#2D3748"},
                        'bar': {'color': "#570F27"},
                        'bgcolor': "white",
                        'borderwidth': 3,
                        'bordercolor': "#E2E8F0",
                        'steps': [
                            {'range': [0, 20], 'color': "#FEF2F2"},
                            {'range': [20, 40], 'color': "#FED7D7"},
                            {'range': [40, 60], 'color': "#FBB6CE"},
                            {'range': [60, 80], 'color': "#F687B3"},
                            {'range': [80, 100], 'color': "#ED64A6"}
                        ],
                        'threshold': {
                            'line': {'color': "#E53E3E", 'width': 4},
                            'thickness': 0.8,
                            'value': 90
                        }
                    },
                    number={'font': {'size': 16, 'color': '#570F27'}, 'suffix': '%'}
                ), row=1, col=i)
            
            fig.update_layout(
                title="Top 3 Trait Scores",
                font={'family': "Arial, sans-serif", 'size': 10},  # Added size parameter
                height=300,
                width=800,
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            return fig.to_html(include_plotlyjs=False, div_id="trait-gauges", full_html=False)
            
        except Exception as e:
            logger.error(f"Error creating trait gauges: {e}")
            return '<div>Trait gauges unavailable</div>'

    def generate_all_visualizations(self, profile_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all visualizations for the report"""
        try:
            trait_scores = profile_data.get('trait_scores', {})
            
            return {
                'archetype_heatmap': self.create_archetype_heatmap(profile_data),
                'trait_radar_chart': self.create_trait_radar_chart(trait_scores),
                'trait_bar_chart': self.create_trait_bar_chart(trait_scores),
                'top_trait_gauges': self.create_top_trait_gauges(trait_scores),
                'growth_gauges_chart': self.create_growth_opportunities_gauges(trait_scores)
            }
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
            return {
                'archetype_heatmap': '<div>Visualization unavailable</div>',
                'trait_radar_chart': '<div>Visualization unavailable</div>',
                'trait_bar_chart': '<div>Visualization unavailable</div>',
                'top_trait_gauges': '<div>Visualization unavailable</div>',
                'growth_gauges_chart': '<div>Visualization unavailable</div>'
            }
    
    def create_growth_opportunities_gauges(self, trait_scores: Dict[str, float]) -> str:
        """Create gauge charts for growth opportunities (bottom 3 traits)"""
        try:
            # Get bottom 3 traits (lowest scores) - exclude top 3 to avoid duplication
            sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1])  # Sort lowest to highest
            # Get the actual bottom 3 traits with lowest scores, but exclude any that are in top 3
            top_3_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            top_3_codes = [trait[0] for trait in top_3_traits]
            
            # Get the bottom 3 traits from the lowest scores, excluding top 3
            bottom_traits = []
            for trait, score in sorted_traits:
                if trait not in top_3_codes:
                    bottom_traits.append((trait, score))
                if len(bottom_traits) >= 3:
                    break
            
            # If we don't have 3 traits after filtering, take the actual bottom 3
            if len(bottom_traits) < 3:
                bottom_traits = sorted_traits[:3]
            
            # Debug logging
            print(f"DEBUG - All traits sorted by score: {[(trait, round(score*100, 1)) for trait, score in sorted_traits]}")
            print(f"DEBUG - Top 3 traits: {[(trait, round(score*100, 1)) for trait, score in top_3_traits]}")
            print(f"DEBUG - Bottom 3 traits for growth: {[(trait, round(score*100, 1)) for trait, score in bottom_traits]}")
            
            if not bottom_traits:
                return '<div>No growth opportunities data available</div>'
            
            # Create subplots for 3 gauges with smaller size
            from plotly.subplots import make_subplots
            fig = make_subplots(
                rows=1, cols=3,
                specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]]
            )
            
            # Add gauges
            for i, (trait, score) in enumerate(bottom_traits, 1):
                trait_name = self.trait_descriptions.get(trait, trait)
                percentage = round(score * 100, 1)
                
                fig.add_trace(
                    go.Indicator(
                        mode="gauge+number",
                        value=percentage,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': trait_name, 'font': {'size': 10}},
                        gauge={
                            'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': "#2D3748"},
                            'bar': {'color': "#F57F17"},
                            'bgcolor': "white",
                            'borderwidth': 3,
                            'bordercolor': "#E2E8F0",
                            'steps': [
                                {'range': [0, 20], 'color': "#FFF8E1"},
                                {'range': [20, 40], 'color': "#FFECB3"},
                                {'range': [40, 60], 'color': "#FFE082"},
                                {'range': [60, 80], 'color': "#FFD54F"},
                                {'range': [80, 100], 'color': "#FFC107"}
                            ],
                            'threshold': {
                                'line': {'color': "#E65100", 'width': 4},
                                'thickness': 0.8,
                                'value': 90
                            }
                        },
                        number={'font': {'size': 16, 'color': '#570F27'}, 'suffix': '%'}
                    ),
                    row=1, col=i
                )
            
            fig.update_layout(
                height=300,
                width=800,
                font={'family': "Arial, sans-serif"},
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            return fig.to_html(include_plotlyjs=False, div_id="growth-opportunities-gauges", full_html=False)
            
        except Exception as e:
            logger.error(f"Error creating growth opportunities gauges: {e}")
            return '<div>Growth opportunities gauges unavailable</div>'
