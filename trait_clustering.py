"""
Trait Clustering System - Clusters traits based on correlations across individuals
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

# Import configuration
from config import config

@dataclass
class TraitCluster:
    """Information about a trait cluster"""
    cluster_id: int
    traits: List[str]
    cluster_name: str
    description: str
    centroid: np.ndarray
    size: int

class TraitClusteringEngine:
    """
    Clusters traits based on their correlations across individuals
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define trait categories and their full names
        self.trait_mapping = {
            'RT': 'Risk Taking',
            'IO': 'Innovation Orientation', 
            'DA': 'Drive and Ambition',
            'AD': 'Adaptability',
            'DM': 'Decision Making',
            'F': 'Failure Handling',
            'RG': 'Resilience and Grit',
            'E(': 'Leadership',
            'RB': 'Relationship Building',
            'CT': 'Critical Thinking',
            'PS': 'Problem Solving',
            'A': 'Accountability',
            'EI': 'Emotional Intelligence',
            'SUS': 'Sustainability',
            'IN': 'Introversion',
            'TB': 'Team Building',
            'N': 'Negotiation',
            'C': 'Conflict',
            'SL': 'Servant Leadership'
        }
        
        # Dynamic cluster naming will be generated based on actual traits
    
    def load_trait_mapping(self, traits_file_path: str) -> Dict[str, List[str]]:
        """Load trait mappings from the assessment file"""
        try:
            df = pd.read_csv(traits_file_path, header=None)
            
            item_trait_map = {}
            for _, row in df.iterrows():
                if len(row) >= 3:
                    item_code = row[0]
                    trait_codes = []
                    if pd.notna(row[2]) and row[2].strip():
                        trait_codes.append(row[2].strip())
                    if len(row) > 3 and pd.notna(row[3]) and row[3].strip():
                        trait_codes.append(row[3].strip())
                    
                    if trait_codes:
                        item_trait_map[item_code] = trait_codes
            
            return item_trait_map
            
        except Exception as e:
            self.logger.error(f"Error loading trait mappings: {e}")
            return {}
    
    def calculate_trait_correlation_matrix(self, processed_data_path: str, 
                                         traits_file_path: str) -> pd.DataFrame:
        """Calculate correlation matrix between traits across all individuals"""
        try:
            # Load processed data
            df = pd.read_csv(processed_data_path, sep='\t')
            
            # Load trait mappings
            item_trait_map = self.load_trait_mapping(traits_file_path)
            
            # Create trait scores for each person
            person_trait_scores = {}
            
            for person_id in df['Persons'].unique():
                person_data = df[df['Persons'] == person_id]
                trait_measures = {}
                
                # Group measures by trait
                for _, row in person_data.iterrows():
                    item_code = row['Assessment_Items']
                    measure = row['Measure']
                    
                    if item_code in item_trait_map:
                        trait_codes = item_trait_map[item_code]
                        
                        for trait_code in trait_codes:
                            if trait_code not in trait_measures:
                                trait_measures[trait_code] = []
                            trait_measures[trait_code].append(measure)
                
                # Calculate mean trait scores for this person
                person_scores = {}
                for trait_code, measures in trait_measures.items():
                    if measures:  # Only include traits with data
                        mean_measure = np.mean(measures)
                        # Normalize to 0-1 scale
                        normalized_score = (mean_measure + 3) / 6
                        normalized_score = max(0, min(1, normalized_score))
                        person_scores[trait_code] = normalized_score
                
                person_trait_scores[person_id] = person_scores
            
            # Convert to DataFrame for correlation analysis
            trait_data = []
            for person_id, scores in person_trait_scores.items():
                row = {'person_id': person_id}
                row.update(scores)
                trait_data.append(row)
            
            trait_df = pd.DataFrame(trait_data).set_index('person_id')
            
            # Calculate correlation matrix
            correlation_matrix = trait_df.corr()
            
            # Handle NaN values by dropping traits with insufficient data
            correlation_matrix = correlation_matrix.dropna(axis=0, how='all').dropna(axis=1, how='all')
            
            # Fill any remaining NaN values with 0 (no correlation)
            correlation_matrix = correlation_matrix.fillna(0)
            
            self.logger.info(f"Calculated correlation matrix for {len(correlation_matrix)} traits")
            return correlation_matrix, trait_df
            
        except Exception as e:
            self.logger.error(f"Error calculating trait correlation matrix: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def cluster_traits(self, correlation_matrix: pd.DataFrame, 
                      n_clusters: int = None) -> List[TraitCluster]:
        """Cluster traits based on correlation matrix"""
        try:
            if correlation_matrix.empty:
                return []
            
            # Determine optimal number of clusters if not specified
            if n_clusters is None:
                n_clusters = self._determine_optimal_clusters(correlation_matrix)
            
            # Use distance matrix (1 - correlation) for clustering
            distance_matrix = 1 - correlation_matrix.abs()
            
            # Apply hierarchical clustering
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='precomputed',
                linkage='average'
            )
            
            cluster_labels = clustering.fit_predict(distance_matrix)
            
            # Create trait clusters
            clusters = []
            for cluster_id in range(n_clusters):
                cluster_traits = [trait for i, trait in enumerate(correlation_matrix.index) 
                                if cluster_labels[i] == cluster_id]
                
                if cluster_traits:
                    # Calculate centroid (mean correlation within cluster)
                    cluster_corr = correlation_matrix.loc[cluster_traits, cluster_traits]
                    centroid = cluster_corr.mean(axis=1).values
                    
                    # Generate dynamic cluster name and description based on actual traits
                    cluster_name = self._generate_cluster_name(cluster_traits)
                    description = self._generate_cluster_description(cluster_traits)
                    
                    cluster = TraitCluster(
                        cluster_id=cluster_id,
                        traits=cluster_traits,
                        cluster_name=cluster_name,
                        description=description,
                        centroid=centroid,
                        size=len(cluster_traits)
                    )
                    
                    clusters.append(cluster)
            
            self.logger.info(f"Created {len(clusters)} trait clusters")
            return clusters
            
        except Exception as e:
            self.logger.error(f"Error clustering traits: {e}")
            return []
    
    def _generate_cluster_name(self, traits: List[str]) -> str:
        """Generate dynamic cluster name based on actual traits"""
        trait_names = [self.trait_mapping.get(trait, trait) for trait in traits]
        
        # Identify common themes in trait names
        trait_keywords = []
        for name in trait_names:
            words = name.lower().split()
            trait_keywords.extend(words)
        
        # Count keyword frequency to identify dominant themes
        from collections import Counter
        keyword_counts = Counter(trait_keywords)
        
        # Remove common words that don't indicate personality themes
        common_words = {'and', 'the', 'of', 'to', 'in', 'for', 'with', 'on', 'at', 'by'}
        keyword_counts = {k: v for k, v in keyword_counts.items() if k not in common_words}
        
        # Get top 2 most common keywords for naming
        top_keywords = [word.title() for word, count in keyword_counts.most_common(2)]
        
        if len(top_keywords) >= 2:
            return f"{top_keywords[0]} & {top_keywords[1]} Cluster"
        elif len(top_keywords) == 1:
            return f"{top_keywords[0]} Focused Cluster"
        else:
            # Fallback to first few trait names
            if len(trait_names) >= 2:
                return f"{trait_names[0]} & {trait_names[1]} Cluster"
            elif trait_names:
                return f"{trait_names[0]} Cluster"
            else:
                return "Mixed Traits Cluster"
    
    def _generate_cluster_description(self, traits: List[str]) -> str:
        """Generate description for a trait cluster"""
        trait_names = [self.trait_mapping.get(trait, trait) for trait in traits]
        
        if len(trait_names) <= 3:
            return f"Contains traits: {', '.join(trait_names)}"
        else:
            return f"Contains traits: {', '.join(trait_names[:3])} and {len(trait_names)-3} others"
    
    def _determine_optimal_clusters(self, correlation_matrix: pd.DataFrame) -> int:
        """Determine optimal number of clusters using silhouette analysis"""
        try:
            from sklearn.metrics import silhouette_score
            
            n_traits = len(correlation_matrix)
            
            # Limit cluster range based on number of traits
            min_clusters = 2
            max_clusters = min(8, max(2, n_traits // 2))  # At least 2 traits per cluster on average
            
            if max_clusters <= min_clusters:
                return min_clusters
            
            distance_matrix = 1 - correlation_matrix.abs()
            
            best_score = -1
            best_n_clusters = min_clusters
            
            for n_clusters in range(min_clusters, max_clusters + 1):
                clustering = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    metric='precomputed',
                    linkage='average'
                )
                
                try:
                    cluster_labels = clustering.fit_predict(distance_matrix)
                    
                    # Calculate silhouette score
                    score = silhouette_score(distance_matrix, cluster_labels, metric='precomputed')
                    
                    if score > best_score:
                        best_score = score
                        best_n_clusters = n_clusters
                        
                except Exception as e:
                    self.logger.warning(f"Error evaluating {n_clusters} clusters: {e}")
                    continue
            
            self.logger.info(f"Optimal number of clusters determined: {best_n_clusters} (silhouette score: {best_score:.3f})")
            return best_n_clusters
            
        except Exception as e:
            self.logger.error(f"Error determining optimal clusters: {e}")
            # Fallback to a reasonable default
            n_traits = len(correlation_matrix)
            return min(5, max(2, n_traits // 3))
    
    def generate_personality_recommendations(self, person_trait_scores: Dict[str, float], 
                                           clusters: List[TraitCluster]) -> Dict[str, Any]:
        """Generate personality-based recommendations for an individual"""
        try:
            recommendations = {
                'person_profile': {},
                'dominant_clusters': [],
                'development_areas': [],
                'strengths': [],
                'recommendations': []
            }
            
            # Calculate person's affinity to each cluster
            cluster_affinities = []
            
            for cluster in clusters:
                # Calculate mean score for traits in this cluster
                cluster_scores = [person_trait_scores.get(trait, 0.5) for trait in cluster.traits]
                mean_score = np.mean(cluster_scores) if cluster_scores else 0.5
                
                cluster_affinities.append({
                    'cluster': cluster,
                    'affinity_score': mean_score,
                    'trait_count': len([t for t in cluster.traits if t in person_trait_scores])
                })
            
            # Sort by affinity score
            cluster_affinities.sort(key=lambda x: x['affinity_score'], reverse=True)
            
            # Identify dominant clusters (top 2-3)
            dominant_clusters = cluster_affinities[:min(3, len(cluster_affinities))]
            recommendations['dominant_clusters'] = [
                {
                    'name': ca['cluster'].cluster_name,
                    'description': ca['cluster'].description,
                    'score': ca['affinity_score'],
                    'traits': ca['cluster'].traits
                }
                for ca in dominant_clusters if ca['affinity_score'] > 0.6
            ]
            
            # Identify strengths (high-scoring traits)
            strengths = [(trait, score) for trait, score in person_trait_scores.items() if score > 0.7]
            strengths.sort(key=lambda x: x[1], reverse=True)
            recommendations['strengths'] = [
                {
                    'trait': self.trait_mapping.get(trait, trait),
                    'code': trait,
                    'score': score
                }
                for trait, score in strengths[:5]  # Top 5 strengths
            ]
            
            # Identify development areas (low-scoring traits)
            development_areas = [(trait, score) for trait, score in person_trait_scores.items() if score < 0.4]
            development_areas.sort(key=lambda x: x[1])
            recommendations['development_areas'] = [
                {
                    'trait': self.trait_mapping.get(trait, trait),
                    'code': trait,
                    'score': score
                }
                for trait, score in development_areas[:3]  # Top 3 development areas
            ]
            
            # Generate personalized recommendations
            recommendations['recommendations'] = self._generate_personalized_recommendations(
                dominant_clusters, strengths, development_areas
            )
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating personality recommendations: {e}")
            return {}
    
    def _generate_personalized_recommendations(self, dominant_clusters, strengths, development_areas):
        """Generate specific recommendations based on personality analysis"""
        recommendations = []
        
        # Recommendations based on dominant clusters
        if dominant_clusters:
            top_cluster = dominant_clusters[0]['cluster']
            cluster_name = top_cluster.cluster_name.lower()
            
            if 'innovation' in cluster_name or 'risk' in cluster_name:
                recommendations.extend([
                    "Consider roles in product development, R&D, or startup environments",
                    "Seek opportunities to lead innovation projects or pilot programs",
                    "Develop skills in design thinking and creative problem-solving"
                ])
            elif 'leadership' in cluster_name or 'execution' in cluster_name:
                recommendations.extend([
                    "Pursue leadership development programs or management roles",
                    "Focus on team building and strategic planning skills",
                    "Consider mentoring others and leading cross-functional projects"
                ])
            elif 'analytical' in cluster_name or 'strategic' in cluster_name:
                recommendations.extend([
                    "Explore roles in data analysis, consulting, or strategic planning",
                    "Develop expertise in analytical tools and frameworks",
                    "Consider positions requiring complex problem-solving"
                ])
        
        # Recommendations based on development areas
        if development_areas:
            low_traits = [da[0] for da in development_areas]
            
            if any('leadership' in trait.lower() for trait in low_traits):
                recommendations.append("Consider leadership training or coaching to develop management skills")
            
            if any('innovation' in trait.lower() for trait in low_traits):
                recommendations.append("Engage in creative workshops or brainstorming sessions to enhance innovative thinking")
            
            if any('resilience' in trait.lower() or 'adaptability' in trait.lower() for trait in low_traits):
                recommendations.append("Practice stress management techniques and seek feedback on handling change")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def visualize_trait_clusters(self, correlation_matrix: pd.DataFrame, 
                               clusters: List[TraitCluster]) -> go.Figure:
        """Create visualization of trait clusters"""
        try:
            # Create a hierarchical clustering dendrogram
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    'Trait Correlation Heatmap',
                    'Cluster Visualization (PCA)', 
                    'Cluster Sizes',
                    'Trait Relationships'
                ],
                specs=[[{"type": "heatmap"}, {"type": "scatter"}],
                       [{"type": "bar"}, {"type": "scatter"}]]
            )
            
            # 1. Correlation heatmap
            fig.add_trace(
                go.Heatmap(
                    z=correlation_matrix.values,
                    x=[self.trait_mapping.get(t, t) for t in correlation_matrix.columns],
                    y=[self.trait_mapping.get(t, t) for t in correlation_matrix.index],
                    colorscale='RdBu',
                    zmid=0,
                    showscale=True,
                    colorbar=dict(title="Correlation", x=0.48)
                ),
                row=1, col=1
            )
            
            # 2. PCA visualization of clusters
            if not correlation_matrix.empty and len(correlation_matrix) > 2:
                # Apply PCA to correlation matrix
                pca = PCA(n_components=2)
                pca_result = pca.fit_transform(correlation_matrix.values)
                
                colors = px.colors.qualitative.Set3[:len(clusters)]
                
                for i, cluster in enumerate(clusters):
                    cluster_indices = [correlation_matrix.index.get_loc(trait) 
                                     for trait in cluster.traits]
                    
                    fig.add_trace(
                        go.Scatter(
                            x=pca_result[cluster_indices, 0],
                            y=pca_result[cluster_indices, 1],
                            mode='markers+text',
                            text=[self.trait_mapping.get(trait, trait) for trait in cluster.traits],
                            textposition="middle center",
                            marker=dict(size=12, color=colors[i]),
                            name=cluster.cluster_name,
                            hovertemplate="<b>%{text}</b><br>Cluster: " + cluster.cluster_name + "<extra></extra>"
                        ),
                        row=1, col=2
                    )
            
            # 3. Cluster sizes
            cluster_names = [cluster.cluster_name for cluster in clusters]
            cluster_sizes = [cluster.size for cluster in clusters]
            
            fig.add_trace(
                go.Bar(
                    x=cluster_names,
                    y=cluster_sizes,
                    marker_color=px.colors.qualitative.Set3[:len(clusters)],
                    text=cluster_sizes,
                    textposition='auto'
                ),
                row=2, col=1
            )
            
            # 4. Network-style trait relationships
            # Show strongest correlations as connections
            strongest_corrs = []
            for i in range(len(correlation_matrix)):
                for j in range(i+1, len(correlation_matrix)):
                    corr = correlation_matrix.iloc[i, j]
                    if abs(corr) > 0.6:  # Strong correlation threshold
                        strongest_corrs.append((
                            correlation_matrix.index[i],
                            correlation_matrix.index[j],
                            corr
                        ))
            
            # Plot network
            if strongest_corrs:
                # Create node positions in a circle
                n_traits = len(correlation_matrix)
                angles = np.linspace(0, 2*np.pi, n_traits, endpoint=False)
                positions = {trait: (np.cos(angle), np.sin(angle)) 
                           for trait, angle in zip(correlation_matrix.index, angles)}
                
                # Draw edges (correlations)
                for trait1, trait2, corr in strongest_corrs:
                    x1, y1 = positions[trait1]
                    x2, y2 = positions[trait2]
                    
                    fig.add_trace(
                        go.Scatter(
                            x=[x1, x2, None],
                            y=[y1, y2, None],
                            mode='lines',
                            line=dict(width=abs(corr)*5, color='rgba(100,100,100,0.5)'),
                            showlegend=False,
                            hoverinfo='skip'
                        ),
                        row=2, col=2
                    )
                
                # Draw nodes
                for trait, (x, y) in positions.items():
                    fig.add_trace(
                        go.Scatter(
                            x=[x],
                            y=[y],
                            mode='markers+text',
                            text=[self.trait_mapping.get(trait, trait)],
                            textposition="middle center",
                            marker=dict(size=15, color='lightblue'),
                            showlegend=False,
                            hovertemplate=f"<b>{self.trait_mapping.get(trait, trait)}</b><extra></extra>"
                        ),
                        row=2, col=2
                    )
            
            fig.update_layout(
                height=800,
                title_text="Trait Clustering Analysis",
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating trait cluster visualization: {e}")
            return go.Figure()
    
    def create_cluster_summary(self, clusters: List[TraitCluster]) -> pd.DataFrame:
        """Create a summary DataFrame of trait clusters"""
        try:
            summary_data = []
            
            for cluster in clusters:
                trait_names = [self.trait_mapping.get(trait, trait) for trait in cluster.traits]
                
                summary_data.append({
                    'Cluster ID': cluster.cluster_id,
                    'Cluster Name': cluster.cluster_name,
                    'Size': cluster.size,
                    'Traits': ', '.join(trait_names),
                    'Description': cluster.description
                })
            
            return pd.DataFrame(summary_data)
            
        except Exception as e:
            self.logger.error(f"Error creating cluster summary: {e}")
            return pd.DataFrame()

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = TraitClusteringEngine()
    
    # Calculate trait correlations
    corr_matrix, trait_data = engine.calculate_trait_correlation_matrix(
        processed_data_path=config.get_file_path("test_output_corrected.csv"),
        traits_file_path=config.traits_file_path
    )
    
    print("Trait Correlation Matrix:")
    print(corr_matrix)
    
    # Cluster traits
    clusters = engine.cluster_traits(corr_matrix, n_clusters=5)
    
    print(f"\nCreated {len(clusters)} trait clusters:")
    for cluster in clusters:
        print(f"Cluster {cluster.cluster_id}: {cluster.cluster_name}")
        print(f"  Traits: {cluster.traits}")
        print(f"  Size: {cluster.size}")
        print()
    
    # Create summary
    summary = engine.create_cluster_summary(clusters)
    print("Cluster Summary:")
    print(summary)