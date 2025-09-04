"""
Visualization helpers for Victoria Project
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging

from victoria.config.settings import brand_config

logger = logging.getLogger(__name__)

def create_trait_radar_chart(profile) -> str:
    """Create HTML radar chart for individual profile"""
    try:
        # Extract trait data
        trait_names = [trait.trait_name for trait in profile.traits]
        trait_scores = [trait.percentile for trait in profile.traits]  # Use percentile (1-100 range)
        
        # Create the radar chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=trait_scores,
            theta=trait_names,
            fill='toself',
            name='Your Profile',
            line=dict(color=brand_config.COLORS['primary_burgundy'], width=3),
            marker=dict(color=brand_config.COLORS['primary_burgundy'], size=8),
            fillcolor=f"rgba(87, 15, 39, 0.3)"
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickmode='linear',
                    tick0=0,
                    dtick=20,
                    gridcolor='rgba(21, 26, 74, 0.25)',
                    linecolor='rgba(21, 26, 74, 0.37)'
                ),
                angularaxis=dict(
                    tickfont=dict(size=10, color=brand_config.COLORS['dark_blue']),
                    gridcolor='rgba(21, 26, 74, 0.25)',
                    linecolor='rgba(21, 26, 74, 0.37)'
                ),
                bgcolor='rgba(248, 249, 250, 0.3)'
            ),
            title=dict(
                text=f"Entrepreneurial Trait Profile: {profile.person_id}",
                font=dict(size=18, color=brand_config.COLORS['dark_blue'], family=brand_config.FONTS['header']),
                x=0.5,
                xanchor='center'
            ),
            legend=dict(
                font=dict(color=brand_config.COLORS['dark_blue']),
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor=brand_config.COLORS['dark_blue'],
                borderwidth=1
            ),
            font=dict(family=brand_config.FONTS['body']),
            margin=dict(l=20, r=20, t=80, b=20),
            showlegend=True,
            paper_bgcolor='#FEFEFE',
            plot_bgcolor='#FAFAFA',
            height=500
        )
        
        # Convert to HTML - generate just the div, not full HTML
        html_string = fig.to_html(
            include_plotlyjs='cdn', 
            div_id=f"trait_radar_{profile.person_id}",
            full_html=False,
            config={'responsive': True}
        )
        return html_string
        
    except Exception as e:
        logger.error(f"Error creating trait radar chart: {e}")
        return "<p>Unable to generate radar chart</p>"

def create_archetype_bar_chart(profile) -> str:
    """Create HTML bar chart for archetype matches"""
    try:
        # For now, create a simple archetype comparison
        # In a full implementation, you'd get all archetype scores
        archetype_name = profile.primary_archetype.archetype.value.replace('_', ' ').title()
        archetype_score = profile.primary_archetype.score * 100
        
        # Mock data for other archetypes (in real implementation, get from profile)
        archetypes = [archetype_name, 'Ambitious Drive', 'Resilient Leadership', 'Adaptive Intelligence', 'Collaborative Responsibility']
        scores = [archetype_score, archetype_score-1, archetype_score-3, archetype_score-5, archetype_score-7]
        
        fig = go.Figure()
        
        colors = [brand_config.COLORS['primary_burgundy'] if i == 0 else brand_config.COLORS['dark_blue'] for i in range(len(archetypes))]
        
        fig.add_trace(go.Bar(
            x=scores,
            y=archetypes,
            orientation='h',
            marker=dict(color=colors, line=dict(color='white', width=1)),
            text=[f"{score:.1f}%" for score in scores],
            textposition='inside',
            textfont=dict(color='white', family=brand_config.FONTS['body'], size=11)
        ))
        
        fig.update_layout(
            title=dict(
                text=f"Entrepreneurial Archetype Matches: {profile.person_id}",
                font=dict(size=16, color=brand_config.COLORS['dark_blue'], family=brand_config.FONTS['header']),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title='Archetype Match Percentage (%)',
                range=[0, 100],
                gridcolor='rgba(21, 26, 74, 0.12)'
            ),
            yaxis=dict(
                tickfont=dict(size=10),
                title=''
            ),
            font=dict(family=brand_config.FONTS['body']),
            margin=dict(l=150, r=50, t=80, b=50),
            height=400,
            paper_bgcolor='#FEFEFE',
            plot_bgcolor='#FAFAFA',
            showlegend=False
        )
        
        # Convert to HTML
        html_string = fig.to_html(include_plotlyjs='cdn', div_id=f"archetype_bar_{profile.person_id}")
        return html_string
        
    except Exception as e:
        logger.error(f"Error creating archetype bar chart: {e}")
        return "<p>Unable to generate archetype chart</p>"

class VisualizationHelper:
    """Helper class for creating visualizations"""
    
    @staticmethod
    def create_trait_radar_chart(trait_data: Dict[str, float], title: str = "Trait Profile") -> go.Figure:
        """Create a radar chart for trait scores"""
        try:
            traits = list(trait_data.keys())
            scores = list(trait_data.values())
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=scores,
                theta=traits,
                fill='toself',
                name='Trait Profile',
                line=dict(color=brand_config.COLORS['primary_burgundy'])
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False,
                title=title,
                font=dict(family=brand_config.FONTS['body'])
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating radar chart: {e}")
            return go.Figure()
    
    @staticmethod
    def create_archetype_distribution(archetype_counts: Dict[str, int]) -> go.Figure:
        """Create pie chart for archetype distribution"""
        try:
            if not archetype_counts:
                return go.Figure()
            
            labels = [name.replace('_', ' ').title() for name in archetype_counts.keys()]
            values = list(archetype_counts.values())
            
            colors = [
                brand_config.COLORS['primary_burgundy'],
                brand_config.COLORS['dark_blue'],
                brand_config.COLORS['accent_yellow'],
                brand_config.COLORS['deep_burgundy'],
                brand_config.COLORS['light_gray']
            ]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors[:len(labels)],
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig.update_layout(
                title="Archetype Distribution",
                font=dict(family=brand_config.FONTS['body'])
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating archetype distribution: {e}")
            return go.Figure()
    
    @staticmethod
    def create_trait_heatmap(cluster_data: pd.DataFrame) -> go.Figure:
        """Create heatmap for cluster trait profiles"""
        try:
            fig = px.imshow(
                cluster_data,
                title="Cluster Trait Profiles",
                color_continuous_scale='RdBu_r',
                aspect='auto'
            )
            
            fig.update_layout(
                font=dict(family=brand_config.FONTS['body'])
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            return go.Figure()