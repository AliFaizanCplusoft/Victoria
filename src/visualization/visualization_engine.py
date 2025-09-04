"""
Merged Visualization Engine for Psychometric Assessment System
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union, Any
import logging
from dataclasses import dataclass

# Import the new individual personality report system
try:
    from .individual_personality_report import (
        IndividualPersonalityVisualizer, 
        PersonalityProfile, 
        PersonalityTrait
    )
    INDIVIDUAL_REPORTS_AVAILABLE = True
except ImportError:
    INDIVIDUAL_REPORTS_AVAILABLE = False

# Fallback classes for standalone usage
@dataclass
class ConstructScore:
    construct_id: str
    construct_name: str
    score: float
    percentile: float
    
@dataclass
class PersonScore:
    person_id: str
    overall_score: float
    overall_percentile: float
    construct_scores: List[ConstructScore]

class PsychometricVisualizationEngine:
    """Main visualization engine for psychometric assessment results."""
    
    def __init__(self, theme: str = "plotly_white"):
        self.logger = logging.getLogger(__name__)
        self.theme = theme
        self.colors = px.colors.qualitative.Set3
        self.layout_defaults = {
            'template': theme,
            'font': {'family': 'Arial, sans-serif', 'size': 12},
            'margin': {'l': 50, 'r': 50, 't': 80, 'b': 50}
        }
        self.title_defaults = {'font': {'size': 16, 'color': '#2c3e50'}}
        self.logger.info("PsychometricVisualizationEngine initialized")
    
    def _extract_person_data(self, person_scores: List[Any]) -> List[Dict]:
        """Extract and validate person data from various input formats."""
        df_data = []
        for person in person_scores:
            try:
                # Use more robust attribute extraction
                person_id = str(getattr(person, 'person_id', 'Unknown'))
                overall_score = float(getattr(person, 'overall_score', 0))
                
                row = {
                    'person_id': person_id,
                    'overall_score': overall_score
                }
                
                # Add construct scores if available
                if hasattr(person, 'construct_scores') and person.construct_scores:
                    for construct in person.construct_scores:
                        if hasattr(construct, 'construct_name') and hasattr(construct, 'score'):
                            construct_name = str(construct.construct_name)
                            construct_score = float(construct.score)
                            row[construct_name] = construct_score
                
                df_data.append(row)
            except Exception as e:
                self.logger.warning(f"Error processing person {getattr(person, 'person_id', 'Unknown')}: {e}")
                continue
        
        return df_data
    
    def create_comprehensive_dashboard(self, person_scores: Union[List[PersonScore], List[Any]], 
                                     output_path: str) -> bool:
        """Create a comprehensive dashboard with all visualizations."""
        try:
            # Handle different input types
            if not person_scores:
                self.logger.error("No person scores provided")
                return False
                
            # Convert to proper format if needed
            processed_scores = []
            for score in person_scores:
                if hasattr(score, 'person_id') and hasattr(score, 'overall_score'):
                    processed_scores.append(score)
                else:
                    self.logger.warning(f"Invalid score object: {type(score)}")
                    continue
            
            if not processed_scores:
                self.logger.error("No valid person scores found")
                return False
            
            # Extract data using the helper method
            df_data = self._extract_person_data(processed_scores)
            
            if not df_data:
                self.logger.error("No valid data to visualize")
                return False
            
            df = pd.DataFrame(df_data)
            
            # Create comprehensive dashboard
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    'Overall Score Distribution',
                    'Top Performers',
                    'Score Statistics', 
                    'Summary Statistics'
                ]
            )
            
            # Overall score distribution
            fig.add_trace(
                go.Histogram(
                    x=df['overall_score'],
                    nbinsx=min(20, len(df)),
                    name='Overall Scores',
                    marker_color='skyblue'
                ),
                row=1, col=1
            )
            
            # Top performers (limit to available data)
            top_n = min(10, len(df))
            top_performers = df.nlargest(top_n, 'overall_score')
            fig.add_trace(
                go.Bar(
                    x=list(range(1, len(top_performers) + 1)),
                    y=top_performers['overall_score'],
                    name=f'Top {top_n}',
                    marker_color='gold',
                    text=[f'ID: {pid}' for pid in top_performers['person_id']],
                    textposition='auto'
                ),
                row=1, col=2
            )
            
            # Score statistics (box plot)
            fig.add_trace(
                go.Box(
                    y=df['overall_score'],
                    name='Score Distribution',
                    marker_color='lightgreen'
                ),
                row=2, col=1
            )
            
            # Summary statistics
            avg_score = df['overall_score'].mean()
            std_score = df['overall_score'].std()
            median_score = df['overall_score'].median()
            fig.add_trace(
                go.Scatter(
                    x=[1, 2, 3],
                    y=[avg_score, median_score, avg_score + std_score],
                    mode='markers+text',
                    text=[f'Avg: {avg_score:.1f}', f'Median: {median_score:.1f}', f'Avg+Std: {avg_score + std_score:.1f}'],
                    textposition="middle right",
                    marker=dict(size=15, color=['red', 'orange', 'blue']),
                    name='Statistics'
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                height=800,
                title_text=f"Psychometric Assessment Dashboard ({len(df)} participants)",
                showlegend=False,
                **self.layout_defaults
            )
            
            # Save the figure
            fig.write_html(output_path)
            self.logger.info(f"Dashboard saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating dashboard: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def create_person_profile(self, person_score: Union[PersonScore, Any], output_path: str) -> bool:
        """Create an individual person profile visualization."""
        try:
            # Robust attribute extraction
            person_id = str(getattr(person_score, 'person_id', 'Unknown'))
            overall_score = float(getattr(person_score, 'overall_score', 0))
            
            if not hasattr(person_score, 'person_id'):
                self.logger.error("Invalid person score object")
                return False
                
            fig = go.Figure()
            
            # Check if construct scores are available
            if hasattr(person_score, 'construct_scores') and person_score.construct_scores:
                construct_names = []
                construct_scores = []
                construct_percentiles = []
                
                for construct in person_score.construct_scores:
                    if hasattr(construct, 'construct_name') and hasattr(construct, 'score'):
                        construct_names.append(str(construct.construct_name))
                        construct_scores.append(float(construct.score))
                        
                        # Add percentile if available
                        percentile = getattr(construct, 'percentile', None)
                        if percentile is not None:
                            construct_percentiles.append(float(percentile))
                
                if construct_names:
                    # Create bar chart with construct scores
                    fig.add_trace(
                        go.Bar(
                            x=construct_names,
                            y=construct_scores,
                            marker_color=self.colors[:len(construct_names)],
                            text=[f'{score:.1f}' for score in construct_scores],
                            textposition='auto'
                        )
                    )
                    
                    # Add percentile information if available
                    if construct_percentiles and len(construct_percentiles) == len(construct_names):
                        fig.add_trace(
                            go.Scatter(
                                x=construct_names,
                                y=construct_percentiles,
                                mode='markers+text',
                                text=[f'{p:.0f}th' for p in construct_percentiles],
                                textposition='top center',
                                marker=dict(size=10, color='red'),
                                name='Percentiles',
                                yaxis='y2'
                            )
                        )
                        
                        # Add second y-axis for percentiles
                        fig.update_layout(
                            yaxis2=dict(
                                title='Percentile',
                                overlaying='y',
                                side='right',
                                range=[0, 100]
                            )
                        )
            else:
                # Just show overall score
                fig.add_trace(
                    go.Bar(
                        x=['Overall Score'],
                        y=[overall_score],
                        marker_color='skyblue',
                        text=[f'{overall_score:.1f}'],
                        textposition='auto'
                    )
                )
            
            # Update layout
            layout_update = {
                "title": {
                    "text": f"Profile: {person_id} (Overall: {overall_score:.1f})",
                    **self.title_defaults
                },
                "xaxis_title": "Constructs",
                "yaxis_title": "Scores",
                **self.layout_defaults
            }
            fig.update_layout(**layout_update)
            
            fig.write_html(output_path)
            self.logger.info(f"Person profile saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating person profile: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def create_construct_comparison(self, person_scores: List[Any], construct_names: List[str], 
                                  output_path: str) -> bool:
        """Create a comparison visualization across constructs."""
        try:
            df_data = self._extract_person_data(person_scores)
            if not df_data:
                return False
            
            df = pd.DataFrame(df_data)
            
            # Filter for requested constructs
            available_constructs = [col for col in df.columns if col in construct_names and col != 'person_id']
            
            if not available_constructs:
                self.logger.error("No valid constructs found for comparison")
                return False
            
            fig = go.Figure()
            
            # Create box plots for each construct
            for construct in available_constructs:
                fig.add_trace(
                    go.Box(
                        y=df[construct],
                        name=construct,
                        marker_color=self.colors[available_constructs.index(construct) % len(self.colors)]
                    )
                )
            
            fig.update_layout(
                title="Construct Comparison",
                xaxis_title="Constructs",
                yaxis_title="Scores",
                **self.layout_defaults
            )
            
            fig.write_html(output_path)
            self.logger.info(f"Construct comparison saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating construct comparison: {e}")
            return False
    
    def create_correlation_matrix(self, person_scores: List[Any], output_path: str) -> bool:
        """Create a correlation matrix of constructs."""
        try:
            df_data = self._extract_person_data(person_scores)
            if not df_data:
                return False
            
            df = pd.DataFrame(df_data)
            
            # Get numeric columns (excluding person_id)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            numeric_cols = [col for col in numeric_cols if col != 'person_id']
            
            if len(numeric_cols) < 2:
                self.logger.error("Not enough numeric columns for correlation matrix")
                return False
            
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr()
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmid=0,
                text=corr_matrix.values.round(2),
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="Correlation")
            ))
            
            fig.update_layout(
                title="Construct Correlation Matrix",
                **self.layout_defaults
            )
            
            fig.write_html(output_path)
            self.logger.info(f"Correlation matrix saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating correlation matrix: {e}")
            return False
    
    def create_radar_chart(self, person_score: Any, output_path: str, 
                          comparison_data: List[Any] = None) -> bool:
        """Create a radar chart for psychometric assessment results."""
        try:
            # Extract construct scores
            if not hasattr(person_score, 'construct_scores') or not person_score.construct_scores:
                self.logger.error("No construct scores available for radar chart")
                return False
            
            constructs = []
            scores = []
            for construct in person_score.construct_scores:
                constructs.append(construct.construct_name)
                scores.append(construct.score)
            
            # Add first point again to close the radar chart
            constructs_closed = constructs + [constructs[0]]
            scores_closed = scores + [scores[0]]
            
            fig = go.Figure()
            
            # Main person's scores
            fig.add_trace(go.Scatterpolar(
                r=scores_closed,
                theta=constructs_closed,
                fill='toself',
                name=f"Individual: {person_score.person_id}",
                line_color='blue'
            ))
            
            # Add comparison data if provided
            if comparison_data:
                for i, comp_person in enumerate(comparison_data[:3]):  # Limit to 3 comparisons
                    if hasattr(comp_person, 'construct_scores') and comp_person.construct_scores:
                        comp_scores = []
                        for construct_name in constructs:
                            # Find matching construct
                            score = 50.0  # Default
                            for comp_construct in comp_person.construct_scores:
                                if comp_construct.construct_name == construct_name:
                                    score = comp_construct.score
                                    break
                            comp_scores.append(score)
                        
                        comp_scores_closed = comp_scores + [comp_scores[0]]
                        
                        fig.add_trace(go.Scatterpolar(
                            r=comp_scores_closed,
                            theta=constructs_closed,
                            name=f"Comparison {i+1}",
                            line=dict(dash='dash')
                        ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                title=f"Psychometric Profile: {person_score.person_id}",
                **self.layout_defaults
            )
            
            fig.write_html(output_path)
            self.logger.info(f"Radar chart saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating radar chart: {e}")
            return False
    
    def create_archetype_map(self, cluster_results: List[Any], output_path: str) -> bool:
        """Create an archetype positioning map."""
        try:
            if not cluster_results:
                self.logger.error("No cluster results provided for archetype map")
                return False
            
            # Extract cluster data
            x_coords = []
            y_coords = []
            cluster_names = []
            cluster_sizes = []
            hover_texts = []
            
            for i, cluster in enumerate(cluster_results):
                # Use first two dominant traits as x,y coordinates
                if hasattr(cluster, 'center_scores') and cluster.center_scores:
                    scores = list(cluster.center_scores.values())
                    x_coords.append(scores[0] if len(scores) > 0 else 50)
                    y_coords.append(scores[1] if len(scores) > 1 else 50)
                else:
                    x_coords.append(50)
                    y_coords.append(50)
                
                # Get cluster info
                archetype_name = getattr(cluster, 'archetype_name', f'Cluster {i+1}')
                cluster_names.append(archetype_name)
                cluster_sizes.append(getattr(cluster, 'size', 1))
                
                # Create hover text
                description = getattr(cluster, 'description', 'No description available')
                hover_text = f"<b>{archetype_name}</b><br>Size: {cluster_sizes[-1]}<br>{description}"
                hover_texts.append(hover_text)
            
            fig = go.Figure()
            
            # Create scatter plot
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers+text',
                marker=dict(
                    size=[max(10, min(50, size * 3)) for size in cluster_sizes],
                    color=self.colors[:len(cluster_results)],
                    opacity=0.7,
                    line=dict(width=2, color='white')
                ),
                text=cluster_names,
                textposition="middle center",
                hovertext=hover_texts,
                hoverinfo='text',
                name='Archetypes'
            ))
            
            layout_update = {
                "title": {
                    "text": "Entrepreneurial Archetype Map",
                    **self.title_defaults
                },
                "xaxis_title": "Leadership & Execution →",
                "yaxis_title": "Innovation & Risk-Taking →",
                "xaxis": dict(range=[0, 100]),
                "yaxis": dict(range=[0, 100]),
                **self.layout_defaults
            }
            fig.update_layout(**layout_update)
            
            fig.write_html(output_path)
            self.logger.info(f"Archetype map saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating archetype map: {e}")
            return False
    
    def create_trait_distribution(self, person_scores: List[Any], trait_name: str, 
                                 output_path: str) -> bool:
        """Create distribution chart for a specific trait."""
        try:
            trait_scores = []
            person_ids = []
            
            for person in person_scores:
                if hasattr(person, 'construct_scores') and person.construct_scores:
                    for construct in person.construct_scores:
                        if construct.construct_name == trait_name:
                            trait_scores.append(construct.score)
                            person_ids.append(person.person_id)
                            break
            
            if not trait_scores:
                self.logger.error(f"No scores found for trait: {trait_name}")
                return False
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=[f'{trait_name} Distribution', f'{trait_name} by Individual'],
                vertical_spacing=0.1
            )
            
            # Histogram
            fig.add_trace(
                go.Histogram(
                    x=trait_scores,
                    nbinsx=20,
                    name='Distribution',
                    marker_color='lightblue'
                ),
                row=1, col=1
            )
            
            # Individual scores
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(trait_scores))),
                    y=trait_scores,
                    mode='markers+lines',
                    name='Individual Scores',
                    text=person_ids,
                    hovertemplate='%{text}: %{y:.1f}<extra></extra>',
                    marker_color='orange'
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                title=f"Trait Analysis: {trait_name}",
                showlegend=False,
                **self.layout_defaults
            )
            
            fig.write_html(output_path)
            self.logger.info(f"Trait distribution saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating trait distribution: {e}")
            return False
    
    def create_individual_personality_report(self, person_score: Any, 
                                           population_avg: Optional[Dict[str, float]] = None,
                                           output_path: str = None) -> bool:
        """
        Create comprehensive individual personality report using the new visualization system.
        
        Args:
            person_score: Individual person score object
            population_avg: Population averages for comparison
            output_path: Path to save the report
            
        Returns:
            True if successful, False otherwise
        """
        if not INDIVIDUAL_REPORTS_AVAILABLE:
            self.logger.warning("Individual personality report system not available")
            return False
            
        try:
            # Convert person_score to PersonalityProfile format
            profile = self._convert_to_personality_profile(person_score)
            
            if not profile:
                self.logger.error("Failed to convert person score to personality profile")
                return False
            
            # Create individual report visualizer
            individual_visualizer = IndividualPersonalityVisualizer(theme=self.theme)
            
            # Generate comprehensive report
            if output_path is None:
                output_path = f"output/individual_report_{profile.person_id}.html"
            
            report_path = individual_visualizer.generate_comprehensive_report(
                profile, population_avg, output_path
            )
            
            self.logger.info(f"Individual personality report created: {report_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating individual personality report: {e}")
            return False
    
    def _convert_to_personality_profile(self, person_score: Any) -> Optional[PersonalityProfile]:
        """Convert person score object to PersonalityProfile format."""
        try:
            # Extract basic info with safe type conversion
            person_id = str(getattr(person_score, 'person_id', 'Unknown'))
            person_name = str(getattr(person_score, 'person_name', person_id))
            
            # Safely convert overall_score
            overall_score_raw = getattr(person_score, 'overall_score', 0)
            overall_score = float(overall_score_raw) if overall_score_raw is not None else 0.0
            
            # Extract traits
            traits = []
            if hasattr(person_score, 'construct_scores') and person_score.construct_scores:
                for construct in person_score.construct_scores:
                    # Safe attribute extraction
                    name = str(getattr(construct, 'construct_name', 'Unknown'))
                    
                    # Safe score conversion
                    score_raw = getattr(construct, 'score', 0)
                    score = float(score_raw) if score_raw is not None else 0.0
                    
                    # Safe percentile conversion
                    percentile_raw = getattr(construct, 'percentile', 0)
                    percentile = float(percentile_raw) if percentile_raw is not None else 0.0
                    
                    # Safe string conversions
                    description = str(getattr(construct, 'description', ''))
                    category = str(getattr(construct, 'category', 'General'))
                    
                    trait = PersonalityTrait(
                        name=name,
                        score=score,
                        percentile=percentile,
                        description=description,
                        category=category
                    )
                    traits.append(trait)
            
            # Create profile
            archetype = getattr(person_score, 'archetype', '')
            completion_date = getattr(person_score, 'completion_date', '')
            
            profile = PersonalityProfile(
                person_id=person_id,
                person_name=person_name,
                traits=traits,
                overall_score=overall_score,
                archetype=str(archetype) if archetype is not None else '',
                completion_date=str(completion_date) if completion_date is not None else ''
            )
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error converting to personality profile: {e}")
            return None

    def create_percentile_chart(self, person_score: Any, output_path: str) -> bool:
        """Create percentile comparison chart."""
        try:
            if not hasattr(person_score, 'construct_scores') or not person_score.construct_scores:
                self.logger.error("No construct scores available for percentile chart")
                return False
            
            constructs = []
            percentiles = []
            scores = []
            
            for construct in person_score.construct_scores:
                constructs.append(construct.construct_name)
                # Handle None percentiles safely
                percentile = getattr(construct, 'percentile', 50.0)
                percentile = percentile if percentile is not None else 50.0
                percentiles.append(float(percentile))
                scores.append(construct.score)
            
            fig = go.Figure()
            
            # Percentile bars
            fig.add_trace(go.Bar(
                x=constructs,
                y=percentiles,
                name='Percentile Rank',
                marker_color='lightgreen',
                text=[f'{p:.0f}th' for p in percentiles],
                textposition='auto',
                yaxis='y'
            ))
            
            # Raw scores line
            fig.add_trace(go.Scatter(
                x=constructs,
                y=scores,
                mode='markers+lines',
                name='Raw Scores',
                marker=dict(size=10, color='red'),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title=f"Percentile Analysis: {person_score.person_id}",
                xaxis_title="Constructs",
                yaxis=dict(title='Percentile Rank', range=[0, 100]),
                yaxis2=dict(
                    title='Raw Score',
                    overlaying='y',
                    side='right'
                ),
                **self.layout_defaults
            )
            
            fig.write_html(output_path)
            self.logger.info(f"Percentile chart saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating percentile chart: {e}")
            return False
    
    def create_comprehensive_report_visuals(self, person_score: Any, 
                                          cluster_results: List[Any], 
                                          all_person_scores: List[Any],
                                          output_dir: str) -> Dict[str, str]:
        """Create all visualizations needed for a comprehensive report."""
        from pathlib import Path
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        created_files = {}
        
        # 1. Radar Chart
        radar_path = output_dir / f"radar_{person_score.person_id}.html"
        if self.create_radar_chart(person_score, str(radar_path)):
            created_files['radar'] = str(radar_path)
        
        # 2. Individual Profile
        profile_path = output_dir / f"profile_{person_score.person_id}.html"
        if self.create_person_profile(person_score, str(profile_path)):
            created_files['profile'] = str(profile_path)
        
        # 3. Percentile Chart
        percentile_path = output_dir / f"percentiles_{person_score.person_id}.html"
        if self.create_percentile_chart(person_score, str(percentile_path)):
            created_files['percentiles'] = str(percentile_path)
        
        # 4. Archetype Map (if cluster results available)
        if cluster_results:
            archetype_path = output_dir / "archetype_map.html"
            if self.create_archetype_map(cluster_results, str(archetype_path)):
                created_files['archetype_map'] = str(archetype_path)
        
        # 5. Trait Distributions for key traits
        key_traits = ['Innovation Orientation', 'Risk Taking', 'Servant Leadership']
        for trait in key_traits:
            trait_path = output_dir / f"trait_{trait.replace(' ', '_').lower()}.html"
            if self.create_trait_distribution(all_person_scores, trait, str(trait_path)):
                created_files[f'trait_{trait.replace(" ", "_").lower()}'] = str(trait_path)
        
        return created_files
    
    def create_embedded_chart_html(self, person_score: Any) -> str:
        """Create embeddable HTML for radar chart to include in reports with RaschPy-processed data."""
        try:
            if not hasattr(person_score, 'construct_scores') or not person_score.construct_scores:
                return "<p>No data available for visualization.</p>"
            
            constructs = []
            scores = []
            percentiles = []
            
            for construct in person_score.construct_scores:
                constructs.append(construct.construct_name)
                # Use actual RaschPy-processed scores instead of arbitrary scaling
                raw_score = float(construct.score)
                scores.append(raw_score)
                # Handle None percentiles safely
                percentile = construct.percentile if construct.percentile is not None else 50.0
                percentiles.append(float(percentile))
            
            # Add first point to close the radar chart
            constructs_closed = constructs + [constructs[0]]
            scores_closed = scores + [scores[0]]
            percentiles_closed = percentiles + [percentiles[0]]
            
            fig = go.Figure()
            
            # Add raw scores trace
            fig.add_trace(go.Scatterpolar(
                r=scores_closed,
                theta=constructs_closed,
                fill='toself',
                name='Your Profile',
                line=dict(color='rgba(102, 126, 234, 0.8)', width=3),
                fillcolor='rgba(102, 126, 234, 0.3)',
                marker=dict(size=8),
                hovertemplate='%{theta}<br>Score: %{r:.2f}<extra></extra>'
            ))
            
            # Add percentile reference line (scaled to match score range)
            max_score = max(scores) if scores else 3
            percentile_scale = max_score / 100  # Scale percentiles to match score range
            percentiles_scaled = [p * percentile_scale for p in percentiles_closed]
            
            fig.add_trace(go.Scatterpolar(
                r=percentiles_scaled,
                theta=constructs_closed,
                name='Percentile Rank',
                line=dict(color='rgba(255, 159, 64, 0.8)', width=2, dash='dash'),
                marker=dict(size=6),
                hovertemplate='%{theta}<br>Percentile: %{customdata:.0f}<extra></extra>',
                customdata=percentiles_closed
            ))
            
            # Dynamic range based on actual data
            range_max = max(max_score * 1.2, 3)  # Ensure minimum range
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, range_max],
                        tickmode='linear',
                        tick0=0,
                        dtick=max(1, range_max/5)  # Dynamic tick spacing
                    )
                ),
                title=f"Trait Profile: {person_score.person_id}",
                showlegend=True,
                height=500,
                margin=dict(l=20, r=20, t=60, b=20),
                font=dict(size=12)
            )
            
            return fig.to_html(
                include_plotlyjs='cdn', 
                div_id=f"radar_chart_{person_score.person_id}",
                config={'displayModeBar': False, 'responsive': True}
            )
            
        except Exception as e:
            self.logger.error(f"Error creating embedded chart: {e}")
            return "<p>Error generating visualization.</p>"