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
            'IN': 'Social Orientation*',
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
            # Use shorter names for x-axis to prevent truncation
            trait_names = [
                'Social Orientation',  # IN - Always include first
                'Resilience & Grit', 'Servant Leadership', 'Emotional Intelligence',
                'Decision-Making', 'Problem-Solving', 'Drive & Ambition',
                'Innovation Orientation', 'Adaptability', 'Critical Thinking',
                'Team Building', 'Risk Taking', 'Accountability',
                'Relationship-Building', 'Negotiation', 'Conflict Resolution', 'Approach to Failure'
            ]
            
            # Shorter display names for x-axis labels to prevent truncation
            trait_display_names = [
                'Social Orientation',
                'Resilience & Grit', 'Servant Leadership', 'Emotional Intel.',
                'Decision-Making', 'Problem-Solving', 'Drive & Ambition',
                'Innovation Orient.', 'Adaptability', 'Critical Thinking',
                'Team Building', 'Risk Taking', 'Accountability',
                'Relationship-Bldg', 'Negotiation', 'Conflict Resol.', 'Approach to Failure'
            ]
            
            # Mapping from heatmap trait names to archetype trait names (for key trait detection)
            heatmap_to_archetype_mapping = {
                'Social Orientation': 'Social Orientation',
                'Resilience & Grit': 'Resilience and Grit',  # Map & to and
                'Servant Leadership': 'Servant Leadership',
                'Emotional Intelligence': 'Emotional Intelligence',
                'Decision-Making': 'Decision Making',  # Map hyphen to space
                'Problem-Solving': 'Problem Solving',  # Map hyphen to space
                'Drive & Ambition': 'Drive and Ambition',  # Map & to and
                'Innovation Orientation': 'Innovation Orientation',
                'Adaptability': 'Adaptability',
                'Critical Thinking': 'Critical Thinking',
                'Team Building': 'Team Building',
                'Risk Taking': 'Risk Taking',
                'Accountability': 'Accountability',
                'Relationship-Building': 'Relationship-Building',
                'Negotiation': 'Negotiation',
                'Conflict Resolution': 'Conflict Resolution',
                'Approach to Failure': 'Approach to Failure'
            }
            
            # Get archetype correlation data first
            from victoria.core.archetype_detector import ArchetypeDetector
            detector = ArchetypeDetector()
            correlation_data = detector.get_archetype_correlation_data()
            
            # Get key traits for each archetype for highlighting
            archetype_key_traits = {}
            for archetype_id, archetype_obj in detector.archetypes.items():
                archetype_name = archetype_obj.name
                archetype_key_traits[archetype_name] = archetype_obj.key_traits
            
            # Define archetypes in exact order with line breaks for long names (for y-axis display)
            archetypes = [
                'Adaptive<br>Intelligence', 'Ambitious Drive', 'Collaborative<br>Responsibility', 
                'Resilient<br>Leadership', 'Strategic<br>Innovation'
            ]
            
            # Map display names (with line breaks) to full names for correlation data and key trait matching
            archetype_display_to_full = {
                'Adaptive<br>Intelligence': 'Adaptive Intelligence',
                'Ambitious Drive': 'Ambitious Drive',
                'Collaborative<br>Responsibility': 'Collaborative Responsibility',
                'Resilient<br>Leadership': 'Resilient Leadership',
                'Strategic<br>Innovation': 'Strategic Innovation'
            }
            
            # Create trait score matrix and text matrix
            trait_score_matrix = []
            text_matrix = []
            
            for archetype_display in archetypes:
                # Map display name (with line breaks) to full name for correlation data lookup
                archetype_full = archetype_display_to_full.get(archetype_display, archetype_display)
                # Get correlation scores for this archetype (should have 17 values)
                correlation_scores = correlation_data.get(archetype_full, [0.0] * 17)
                # Ensure we have exactly 17 values
                if len(correlation_scores) < 17:
                    # Pad with zeros if needed
                    correlation_scores.extend([0.0] * (17 - len(correlation_scores)))
                
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
            
            # Create compact heatmap with smaller cells and borders
            heatmap_data = go.Heatmap(
                z=trait_score_matrix,
                x=trait_display_names,  # Use shorter display names for x-axis
                y=archetypes,  # Use archetypes with line breaks for y-axis
                text=text_matrix,
                texttemplate="%{text}",
                textfont={"color": "black", "size": 11, "family": "Arial, sans-serif", "weight": "bold"},  # Larger text for better readability
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
                    title=dict(text="Trait<br>Score", font=dict(size=9)),  # Fixed: use title dict with font
                    tickmode="array",
                    tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    ticktext=["Low", "Low-Med", "Medium", "High", "Very High", "Perfect"],
                    len=0.6, thickness=15, x=0.78, xpad=3,  # Smaller, closer colorbar
                    tickfont=dict(size=7)  # Smaller tick font
                ),
                hovertemplate="<b>%{y}</b><br>%{x}<br>Trait Score: %{z:.2f}<br><extra></extra>",
                # Add visible cell borders
                xgap=0.5,  # Gap between columns for visible borders
                ygap=0.5   # Gap between rows for visible borders
            )
            
            fig = go.Figure(data=heatmap_data)
            
            # Add annotations for each cell to ensure text is visible
            annotations = []
            for i, archetype in enumerate(archetypes):
                for j, trait in enumerate(trait_display_names):
                    annotations.append(
                        dict(
                            x=j, y=i,
                            text=text_matrix[i][j],
                            showarrow=False,
                            font=dict(color="black", size=11, family="Arial, sans-serif", weight="bold"),  # Larger annotation text for readability
                            xref="x", yref="y"
                        )
                    )
            
            # Add highlighting for key traits in each archetype
            for i, archetype_display in enumerate(archetypes):
                # Map display name (with line breaks) to full name for key trait lookup
                archetype_full = archetype_display_to_full.get(archetype_display, archetype_display)
                key_traits = archetype_key_traits.get(archetype_full, [])
                for j, trait_display_name in enumerate(trait_display_names):
                    # Map display name back to full name for key trait matching
                    trait_name = trait_names[j]
                    # Map heatmap trait name to archetype trait name
                    archetype_trait_name = heatmap_to_archetype_mapping.get(trait_name, trait_name)
                    # Check if this trait is a key trait for this archetype
                    if archetype_trait_name in key_traits:
                        # Add a border/shape to highlight key trait cells
                        fig.add_shape(
                            type="rect",
                            x0=j-0.5, x1=j+0.5,
                            y0=i-0.5, y1=i+0.5,
                            line=dict(color="#FF6B35", width=3),  # Orange-red border for key traits
                            fillcolor="rgba(0,0,0,0)",
                            layer="above"
                        )
                        # Add a star annotation to indicate key trait
                        annotations.append(
                            dict(
                                x=j, y=i,
                                text="★",
                                showarrow=False,
                                font=dict(color="#FF6B35", size=8, family="Arial, sans-serif"),  # Smaller star for compact cells
                                xref="x", yref="y",
                                xanchor="left",
                                yanchor="top"
                            )
                        )
            
            # Add highlighting for detected archetype (thicker border)
            detected_archetype = profile_data.get('archetype_name', 'Resilient Leadership')
            # Map full archetype name to display name with line breaks
            detected_display = None
            for display_name, full_name in archetype_display_to_full.items():
                if full_name == detected_archetype:
                    detected_display = display_name
                    break
            if detected_display and detected_display in archetypes:
                detected_index = archetypes.index(detected_display)
                for j in range(len(trait_display_names)):
                    fig.add_shape(
                        type="rect",
                        x0=j-0.5, x1=j+0.5,
                        y0=detected_index-0.5, y1=detected_index+0.5,
                        line=dict(color="#570F27", width=4),  # Dark burgundy for detected archetype row
                        fillcolor="rgba(0,0,0,0)",
                        layer="above"
                    )
            
            fig.update_layout(
                title=dict(
                    text=f"Trait Scores by Archetype<br><sub style='font-size: 9px; line-height: 1.3;'>Detected: {detected_archetype} (Dark Border) | ★ = Key Traits for Each Archetype</sub>",
                    font=dict(size=13, color="#2c3e50", family="Arial, sans-serif"),  # Smaller title
                    x=0.4,  # Centered but slightly left (40% from left)
                    xanchor='center',  # Center anchor
                    y=1.0,  # Position at absolute top
                    yref='paper',  # Reference to paper coordinates
                    pad=dict(t=0, b=20)  # Minimal bottom padding to reduce gap
                ),
                xaxis=dict(
                    title="Personality Traits", 
                    tickfont=dict(size=8, weight='bold', family="Arial, sans-serif"),  # Bold x-axis labels
                    title_font=dict(size=10, weight='bold', family="Arial, sans-serif"),  # Bold title font
                    tickangle=-60,  # Steeper angle for more compact labels
                    tickmode='linear',
                    dtick=1,  # Show all ticks
                    side='bottom',
                    showgrid=False,
                    zeroline=False,
                    automargin=True,  # Auto-adjust margins to prevent truncation
                    ticklabeloverflow='allow',  # Allow labels to extend if needed
                    ticklabelposition='outside',  # Place labels outside plot area
                    anchor='free',  # Allow positioning
                    position=0.0  # Position at bottom
                ),
                yaxis=dict(
                    title="Entrepreneurial Archetypes", 
                    tickfont=dict(size=9, weight='bold', family="Arial, sans-serif"),  # Bold y-axis labels
                    title_font=dict(size=10, weight='bold', family="Arial, sans-serif"),  # Bold title font
                    showgrid=False,  # Remove grid lines (we have cell borders)
                    zeroline=False,
                    domain=[0.0, 0.85],  # Start y-axis lower (0.85) to leave more space for title and subtitle above
                    tickmode='array',  # Use array mode for custom labels
                    tickvals=list(range(len(archetypes))),  # Position ticks at each archetype
                    ticktext=archetypes  # Use archetypes with line breaks
                ),
                font=dict(family="Arial, sans-serif"),
                margin=dict(l=40, r=70, t=60, b=100),  # Reduced top margin to minimize gap
                height=480, width=1100,  # Further reduced height to make cells smaller
                paper_bgcolor="#FEFEFE", plot_bgcolor="#D0D0D0",  # Darker background to make borders more visible
                autosize=True,  # Enable autosize for responsive behavior
                annotations=annotations,
                # Reduce spacing to make cells more compact
                bargap=0,
                bargroupgap=0
            )
            
            # Update xaxis domain to use more width, bringing colorbar closer
            fig.update_xaxes(domain=[0, 0.75])  # Use 75% of width, leaving 25% on right for labels and colorbar
            
            # Make the plot responsive with proper config
            config = {
                'responsive': True,
                'displayModeBar': False,  # Hide toolbar for cleaner look
                'staticPlot': False,
                'autosizable': True  # Allow auto-sizing
            }
            
            return fig.to_html(include_plotlyjs=False, div_id="archetype-heatmap", full_html=False, config=config)
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Error creating archetype heatmap: {e}")
            logger.error(f"Traceback: {error_trace}")
            return f'<div>Correlation heatmap unavailable: {str(e)}</div>'
    
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
                width=600,
                annotations=[
                    dict(
                        text="*Higher social orientation is extroversion, lower social orientation is introversion",
                        xref="paper", yref="paper",
                        x=0.05, y=-0.15,
                        showarrow=False,
                        font=dict(size=10, color="#666666"),
                        align="left",
                        xanchor="left"
                    )
                ]
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
            # Filter out IN (Social Orientation) from trait scores
            filtered_scores = {k: v for k, v in trait_scores.items() if k != 'IN'}
            # Get top 3 traits (excluding IN)
            sorted_traits = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            
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
            # Filter out IN (Social Orientation) from trait scores
            filtered_scores = {k: v for k, v in trait_scores.items() if k != 'IN'}
            # Get bottom 3 traits (lowest scores) - exclude top 3 to avoid duplication
            sorted_traits = sorted(filtered_scores.items(), key=lambda x: x[1])  # Sort lowest to highest
            # Get the actual bottom 3 traits with lowest scores, but exclude any that are in top 3
            top_3_traits = sorted(filtered_scores.items(), key=lambda x: x[1], reverse=True)[:3]
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
