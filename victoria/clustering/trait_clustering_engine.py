"""
Enhanced Trait Clustering System with Vertria Archetype Integration
Clusters traits and maps them to entrepreneurial archetypes
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Any
import logging

from victoria.core.models import TraitCluster, ClusteringResult, PersonTraitProfile
from victoria.core.enums import ArchetypeType, TraitType
from victoria.config.settings import brand_config, archetype_config, trait_config

class TraitClusteringEngine:
    """
    Enhanced trait clustering engine that maps clusters to Vertria's entrepreneurial archetypes
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.pca = None
        self.clustering_model = None
        self.cluster_results = None
        
    def analyze_trait_clusters(self, profiles: Dict[str, PersonTraitProfile], 
                             method: str = 'kmeans', n_clusters: int = 5) -> ClusteringResult:
        """
        Analyze trait patterns and create archetype-aligned clusters
        """
        try:
            # Prepare data matrix
            trait_data = self._prepare_trait_matrix(profiles)
            
            if trait_data.empty:
                raise ValueError("No valid trait data available for clustering")
            
            # Perform clustering
            clusters, cluster_assignments = self._perform_clustering(trait_data, method, n_clusters)
            
            # Map clusters to archetypes
            archetype_mappings = self._map_clusters_to_archetypes(clusters, trait_data)
            
            # Calculate quality metrics
            silhouette = silhouette_score(self.scaler.fit_transform(trait_data), cluster_assignments)
            explained_variance = self._calculate_explained_variance(trait_data)
            
            result = ClusteringResult(
                clusters=clusters,
                silhouette_score=silhouette,
                explained_variance=explained_variance,
                method_used=method,
                n_clusters=n_clusters,
                archetype_mappings=archetype_mappings
            )
            
            self.cluster_results = result
            self.logger.info(f"Clustering completed: {n_clusters} clusters, silhouette={silhouette:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in trait clustering: {e}")
            raise
    
    def _prepare_trait_matrix(self, profiles: Dict[str, PersonTraitProfile]) -> pd.DataFrame:
        """Prepare trait data matrix for clustering"""
        trait_data = []
        person_ids = []
        
        for person_id, profile in profiles.items():
            if profile.completion_rate > 0.5:  # Only include profiles with >50% completion
                trait_scores = {}
                for trait in trait_config.CORE_TRAITS:
                    trait_score = profile.get_trait_score(trait)
                    trait_scores[trait] = trait_score.score if trait_score else 0.0
                
                trait_data.append(trait_scores)
                person_ids.append(person_id)
        
        df = pd.DataFrame(trait_data, index=person_ids)
        return df
    
    def _perform_clustering(self, trait_data: pd.DataFrame, method: str, 
                          n_clusters: int) -> Tuple[List[TraitCluster], np.ndarray]:
        """Perform the actual clustering"""
        # Standardize the data
        scaled_data = self.scaler.fit_transform(trait_data)
        
        # Perform clustering
        if method == 'kmeans':
            self.clustering_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        elif method == 'hierarchical':
            self.clustering_model = AgglomerativeClustering(n_clusters=n_clusters)
        else:
            raise ValueError(f"Unsupported clustering method: {method}")
        
        cluster_assignments = self.clustering_model.fit_predict(scaled_data)
        
        # Create cluster objects
        clusters = []
        for i in range(n_clusters):
            cluster_indices = np.where(cluster_assignments == i)[0]
            cluster_traits = trait_data.iloc[cluster_indices]
            
            # Calculate cluster centroid in original space
            centroid = cluster_traits.mean().values
            
            # Determine dominant traits for this cluster
            dominant_traits = self._identify_dominant_traits(cluster_traits)
            
            # Generate cluster name and description
            cluster_name, description = self._generate_cluster_info(i, dominant_traits, centroid)
            
            cluster = TraitCluster(
                cluster_id=i,
                traits=dominant_traits,
                cluster_name=cluster_name,
                description=description,
                centroid=centroid,
                size=len(cluster_indices)
            )
            
            clusters.append(cluster)
        
        return clusters, cluster_assignments
    
    def _identify_dominant_traits(self, cluster_data: pd.DataFrame) -> List[str]:
        """Identify the dominant traits in a cluster"""
        # Calculate mean scores for each trait in the cluster
        trait_means = cluster_data.mean()
        
        # Select traits that are above the 70th percentile
        threshold = trait_means.quantile(0.7)
        dominant_traits = trait_means[trait_means >= threshold].index.tolist()
        
        # Ensure we have at least 2 dominant traits
        if len(dominant_traits) < 2:
            dominant_traits = trait_means.nlargest(3).index.tolist()
        
        return dominant_traits
    
    def _generate_cluster_info(self, cluster_id: int, dominant_traits: List[str], 
                             centroid: np.ndarray) -> Tuple[str, str]:
        """Generate cluster name and description"""
        # Create name based on dominant traits
        if len(dominant_traits) >= 2:
            name = f"{dominant_traits[0]} + {dominant_traits[1]} Cluster"
        else:
            name = f"Cluster {cluster_id + 1}"
        
        # Generate description
        trait_strengths = [trait for i, trait in enumerate(trait_config.CORE_TRAITS) 
                          if i < len(centroid) and centroid[i] > 0.5]
        
        if trait_strengths:
            description = f"Individuals with strong {', '.join(trait_strengths[:3])} characteristics"
        else:
            description = f"Cluster of {len(dominant_traits)} dominant traits"
        
        return name, description
    
    def _map_clusters_to_archetypes(self, clusters: List[TraitCluster], 
                                   trait_data: pd.DataFrame) -> Dict[int, ArchetypeType]:
        """Map clusters to Vertria's entrepreneurial archetypes"""
        mappings = {}
        
        for cluster in clusters:
            best_match = self._find_best_archetype_match(cluster)
            if best_match:
                mappings[cluster.cluster_id] = best_match
                cluster.archetype_mapping = best_match
        
        return mappings
    
    def _find_best_archetype_match(self, cluster: TraitCluster) -> Optional[ArchetypeType]:
        """Find the best matching archetype for a cluster"""
        best_match = None
        best_score = 0.0
        
        for archetype_key, archetype_info in archetype_config.ARCHETYPES.items():
            archetype_type = ArchetypeType(archetype_key)
            core_traits = archetype_info['core_traits']
            
            # Calculate overlap between cluster traits and archetype traits
            overlap = set(cluster.traits) & set(core_traits)
            overlap_score = len(overlap) / len(core_traits)
            
            # Consider trait strength in the cluster centroid
            trait_strength = np.mean([cluster.centroid[trait_config.CORE_TRAITS.index(trait)] 
                                    for trait in overlap if trait in trait_config.CORE_TRAITS])
            
            # Combined score
            combined_score = overlap_score * (1 + trait_strength)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = archetype_type
        
        # Only return match if score is above threshold
        return best_match if best_score > 0.4 else None
    
    def _calculate_explained_variance(self, trait_data: pd.DataFrame) -> float:
        """Calculate explained variance using PCA"""
        try:
            self.pca = PCA()
            self.pca.fit(self.scaler.fit_transform(trait_data))
            return np.sum(self.pca.explained_variance_ratio_[:3])  # First 3 components
        except:
            return 0.0
    
    def create_cluster_visualizations(self, trait_data: pd.DataFrame, 
                                    cluster_assignments: np.ndarray) -> Dict[str, Any]:
        """Create visualizations for the clustering results"""
        visualizations = {}
        
        try:
            # PCA visualization
            if self.pca is None:
                self.pca = PCA(n_components=2)
                pca_data = self.pca.fit_transform(self.scaler.fit_transform(trait_data))
            else:
                pca_data = self.pca.transform(self.scaler.transform(trait_data))[:, :2]
            
            # Create PCA scatter plot
            fig = go.Figure()
            
            colors = [brand_config.COLORS['primary_burgundy'], brand_config.COLORS['dark_blue'],
                     brand_config.COLORS['accent_yellow'], brand_config.COLORS['deep_burgundy'],
                     brand_config.COLORS['light_gray']]
            
            for i in range(len(set(cluster_assignments))):
                cluster_indices = cluster_assignments == i
                fig.add_trace(go.Scatter(
                    x=pca_data[cluster_indices, 0],
                    y=pca_data[cluster_indices, 1],
                    mode='markers',
                    name=f'Cluster {i+1}',
                    marker=dict(color=colors[i % len(colors)], size=8)
                ))
            
            fig.update_layout(
                title="Trait Clusters - PCA Visualization",
                xaxis_title="First Principal Component",
                yaxis_title="Second Principal Component",
                font=dict(family=brand_config.FONTS['body']),
                plot_bgcolor='white'
            )
            
            visualizations['pca_plot'] = fig
            
            # Trait heatmap
            cluster_means = []
            for i in range(len(set(cluster_assignments))):
                cluster_data = trait_data[cluster_assignments == i]
                cluster_means.append(cluster_data.mean())
            
            heatmap_data = pd.DataFrame(cluster_means, 
                                      index=[f'Cluster {i+1}' for i in range(len(cluster_means))],
                                      columns=trait_data.columns)
            
            fig_heatmap = px.imshow(heatmap_data, 
                                   title="Cluster Trait Profiles",
                                   color_continuous_scale='RdBu_r',
                                   aspect='auto')
            
            visualizations['trait_heatmap'] = fig_heatmap
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")
            return {}
    
    def generate_cluster_report(self, clustering_result: ClusteringResult) -> Dict[str, Any]:
        """Generate a comprehensive cluster analysis report"""
        report = {
            'summary': {
                'n_clusters': clustering_result.n_clusters,
                'silhouette_score': clustering_result.silhouette_score,
                'explained_variance': clustering_result.explained_variance,
                'method_used': clustering_result.method_used
            },
            'clusters': [],
            'archetype_mappings': {}
        }
        
        # Add cluster details
        for cluster in clustering_result.clusters:
            cluster_info = {
                'id': cluster.cluster_id,
                'name': cluster.cluster_name,
                'description': cluster.description,
                'size': cluster.size,
                'dominant_traits': cluster.traits,
                'archetype': cluster.archetype_mapping.value if cluster.archetype_mapping else None
            }
            report['clusters'].append(cluster_info)
        
        # Add archetype mappings
        for cluster_id, archetype in clustering_result.archetype_mappings.items():
            report['archetype_mappings'][cluster_id] = {
                'archetype': archetype.value,
                'name': archetype_config.ARCHETYPES[archetype.value]['name'],
                'description': archetype_config.ARCHETYPES[archetype.value]['description']
            }
        
        return report