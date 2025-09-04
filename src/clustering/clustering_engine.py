"""
Psychometric Clustering Engine for Victoria Project
Handles clustering of assessment participants into personality archetypes
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.decomposition import PCA
import warnings

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)

@dataclass
class ClusterInfo:
    """Information about a personality archetype cluster."""
    cluster_id: int
    archetype_name: str
    size: int
    center: np.ndarray
    members: List[str] = field(default_factory=list)
    characteristics: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

class PsychometricClusteringEngine:
    """
    Clustering engine for psychometric assessment data.
    
    Creates personality archetypes by clustering participants based on their
    psychometric scores across different constructs.
    """
    
    # Default archetype names for different cluster counts
    ARCHETYPE_NAMES = {
        2: ["Analytical", "Intuitive"],
        3: ["Analytical", "Balanced", "Intuitive"],
        4: ["Analytical", "Practical", "Creative", "Intuitive"],
        5: ["Analytical", "Practical", "Balanced", "Creative", "Intuitive"],
        6: ["Analytical", "Methodical", "Practical", "Creative", "Visionary", "Intuitive"],
        7: ["Analytical", "Methodical", "Practical", "Balanced", "Creative", "Visionary", "Intuitive"],
        8: ["Analytical", "Methodical", "Practical", "Systematic", "Balanced", "Creative", "Visionary", "Intuitive"]
    }
    
    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        """
        Initialize the clustering engine.
        
        Args:
            n_clusters: Number of clusters to create
            random_state: Random state for reproducibility
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans = None
        self.pca = None
        self.cluster_info = []
        
        logger.info(f"PsychometricClusteringEngine initialized with {n_clusters} clusters")
    
    def cluster_persons(self, person_scores: List[Any]) -> List[ClusterInfo]:
        """
        Cluster participants based on their psychometric scores.
        
        Args:
            person_scores: List of PersonScore objects with scoring results
            
        Returns:
            List of ClusterInfo objects representing the personality archetypes
        """
        logger.info(f"Clustering {len(person_scores)} participants into {self.n_clusters} archetypes")
        
        if len(person_scores) < self.n_clusters:
            logger.warning(f"Number of participants ({len(person_scores)}) is less than clusters ({self.n_clusters})")
            self.n_clusters = max(1, len(person_scores))
        
        # Extract features for clustering
        features, person_ids = self._extract_features(person_scores)
        
        if features.size == 0:
            logger.error("No features extracted for clustering")
            return []
        
        # Standardize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Perform clustering
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10
        )
        
        cluster_labels = self.kmeans.fit_predict(features_scaled)
        
        # Create cluster information
        self.cluster_info = self._create_cluster_info(
            features_scaled, cluster_labels, person_ids, person_scores
        )
        
        # Calculate clustering metrics
        if len(set(cluster_labels)) > 1:
            silhouette = silhouette_score(features_scaled, cluster_labels)
            calinski = calinski_harabasz_score(features_scaled, cluster_labels)
            logger.info(f"Clustering metrics - Silhouette: {silhouette:.3f}, Calinski-Harabasz: {calinski:.3f}")
        
        logger.info(f"Clustering completed - {len(self.cluster_info)} archetypes created")
        return self.cluster_info
    
    def _extract_features(self, person_scores: List[Any]) -> Tuple[np.ndarray, List[str]]:
        """Extract numerical features from person scores for clustering."""
        features = []
        person_ids = []
        
        for person in person_scores:
            person_ids.append(person.person_id)
            
            # Extract construct scores
            construct_scores = []
            
            # Try different attribute names for construct scores
            if hasattr(person, 'construct_scores') and person.construct_scores:
                # Handle case where construct_scores is a list of ConstructScore objects
                if isinstance(person.construct_scores, list):
                    for construct_score in person.construct_scores:
                        if hasattr(construct_score, 'score') and isinstance(construct_score.score, (int, float)):
                            construct_scores.append(construct_score.score)
                        elif hasattr(construct_score, 'value') and isinstance(construct_score.value, (int, float)):
                            construct_scores.append(construct_score.value)
                # Handle case where construct_scores is a dictionary
                elif isinstance(person.construct_scores, dict):
                    for construct, score in person.construct_scores.items():
                        if isinstance(score, (int, float)):
                            construct_scores.append(score)
            
            elif hasattr(person, 'scores') and person.scores:
                for score in person.scores.values():
                    if isinstance(score, (int, float)):
                        construct_scores.append(score)
            
            elif hasattr(person, 'overall_score') and person.overall_score is not None:
                construct_scores.append(person.overall_score)
            
            # If we have construct scores, use them
            if construct_scores:
                features.append(construct_scores)
            else:
                # Fallback: create dummy features
                logger.warning(f"No construct scores found for {person.person_id}, using dummy features")
                features.append([0.0] * 5)  # 5 dummy features
        
        if not features:
            logger.error("No features could be extracted from person scores")
            return np.array([]), []
        
        # Convert to numpy array and handle different feature lengths
        max_features = max(len(f) for f in features)
        normalized_features = []
        
        for feature_vector in features:
            if len(feature_vector) < max_features:
                # Pad with zeros
                padded = feature_vector + [0.0] * (max_features - len(feature_vector))
                normalized_features.append(padded)
            else:
                normalized_features.append(feature_vector[:max_features])
        
        return np.array(normalized_features), person_ids
    
    def _create_cluster_info(self, features: np.ndarray, labels: np.ndarray, 
                           person_ids: List[str], person_scores: List[Any]) -> List[ClusterInfo]:
        """Create detailed information about each cluster."""
        clusters = []
        archetype_names = self.ARCHETYPE_NAMES.get(self.n_clusters, 
                                                  [f"Archetype_{i+1}" for i in range(self.n_clusters)])
        
        for cluster_id in range(self.n_clusters):
            cluster_mask = labels == cluster_id
            cluster_members = [person_ids[i] for i in range(len(person_ids)) if cluster_mask[i]]
            cluster_features = features[cluster_mask]
            
            # Calculate cluster characteristics
            if len(cluster_features) > 0:
                cluster_center = np.mean(cluster_features, axis=0)
                characteristics = self._analyze_cluster_characteristics(
                    cluster_features, cluster_members, person_scores
                )
            else:
                cluster_center = np.zeros(features.shape[1])
                characteristics = {}
            
            cluster_info = ClusterInfo(
                cluster_id=cluster_id,
                archetype_name=archetype_names[cluster_id] if cluster_id < len(archetype_names) else f"Archetype_{cluster_id+1}",
                size=len(cluster_members),
                center=cluster_center,
                members=cluster_members,
                characteristics=characteristics,
                description=self._generate_cluster_description(archetype_names[cluster_id] if cluster_id < len(archetype_names) else f"Archetype_{cluster_id+1}", characteristics)
            )
            
            clusters.append(cluster_info)
        
        return clusters
    
    def _analyze_cluster_characteristics(self, cluster_features: np.ndarray, 
                                       cluster_members: List[str], 
                                       person_scores: List[Any]) -> Dict[str, Any]:
        """Analyze the characteristics of a cluster."""
        characteristics = {
            'mean_scores': np.mean(cluster_features, axis=0).tolist(),
            'std_scores': np.std(cluster_features, axis=0).tolist(),
            'size': len(cluster_members)
        }
        
        # Add percentile information
        if len(cluster_features) > 0:
            characteristics['percentiles'] = {
                '25th': np.percentile(cluster_features, 25, axis=0).tolist(),
                '50th': np.percentile(cluster_features, 50, axis=0).tolist(),
                '75th': np.percentile(cluster_features, 75, axis=0).tolist()
            }
        
        return characteristics
    
    def _generate_cluster_description(self, archetype_name: str, characteristics: Dict[str, Any]) -> str:
        """Generate a description for the cluster archetype."""
        descriptions = {
            'Analytical': "Individuals who prefer logical, systematic approaches to problem-solving with strong attention to detail.",
            'Practical': "People who focus on concrete, actionable solutions and prefer hands-on approaches.",
            'Creative': "Innovative thinkers who value originality and enjoy exploring new ideas and possibilities.",
            'Intuitive': "Individuals who rely on instinct and pattern recognition, often seeing the big picture.",
            'Balanced': "Well-rounded individuals who demonstrate moderate levels across multiple dimensions.",
            'Methodical': "Systematic individuals who prefer structured, step-by-step approaches to tasks.",
            'Visionary': "Forward-thinking individuals who focus on future possibilities and strategic thinking.",
            'Systematic': "Individuals who prefer organized, methodical approaches with clear processes."
        }
        
        return descriptions.get(archetype_name, f"Unique personality archetype with distinct characteristics.")
    
    def optimize_clusters(self, person_scores: List[Any], max_clusters: int = 10) -> int:
        """
        Optimize the number of clusters using silhouette analysis.
        
        Args:
            person_scores: List of PersonScore objects
            max_clusters: Maximum number of clusters to test
            
        Returns:
            Optimal number of clusters
        """
        logger.info(f"Optimizing cluster count up to {max_clusters}")
        
        features, _ = self._extract_features(person_scores)
        
        if features.size == 0:
            logger.error("No features available for cluster optimization")
            return 3
        
        features_scaled = self.scaler.fit_transform(features)
        
        # Test different cluster counts
        silhouette_scores = []
        cluster_range = range(2, min(max_clusters + 1, len(person_scores)))
        
        for n_clusters in cluster_range:
            kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            if len(set(cluster_labels)) > 1:
                silhouette = silhouette_score(features_scaled, cluster_labels)
                silhouette_scores.append(silhouette)
            else:
                silhouette_scores.append(0)
        
        if silhouette_scores:
            optimal_idx = np.argmax(silhouette_scores)
            optimal_clusters = list(cluster_range)[optimal_idx]
            logger.info(f"Optimal clusters: {optimal_clusters} (silhouette: {silhouette_scores[optimal_idx]:.3f})")
            return optimal_clusters
        
        logger.warning("Could not optimize cluster count, using default of 3")
        return 3
    
    def predict_cluster(self, person_scores: List[Any]) -> List[int]:
        """
        Predict cluster assignments for new participants.
        
        Args:
            person_scores: List of PersonScore objects
            
        Returns:
            List of cluster assignments
        """
        if self.kmeans is None:
            raise ValueError("Model must be trained before prediction")
        
        features, _ = self._extract_features(person_scores)
        features_scaled = self.scaler.transform(features)
        
        return self.kmeans.predict(features_scaled)
    
    def get_cluster_summary(self) -> Dict[str, Any]:
        """Get a summary of the clustering results."""
        if not self.cluster_info:
            return {}
        
        summary = {
            'total_clusters': len(self.cluster_info),
            'total_participants': sum(cluster.size for cluster in self.cluster_info),
            'cluster_sizes': {cluster.archetype_name: cluster.size for cluster in self.cluster_info},
            'cluster_percentages': {}
        }
        
        total_participants = summary['total_participants']
        if total_participants > 0:
            summary['cluster_percentages'] = {
                cluster.archetype_name: (cluster.size / total_participants) * 100
                for cluster in self.cluster_info
            }
        
        return summary