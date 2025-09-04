"""
Streamlit Application Entry Point
Clean, modular Streamlit application for Victoria Project
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

# Victoria imports
from victoria.config.settings import config, app_config, brand_config
from victoria.utils.logging_config import setup_logging
from victoria.scoring.trait_scorer import TraitScorer
from victoria.clustering.trait_clustering_engine import TraitClusteringEngine
from victoria.clustering.archetype_mapper import ArchetypeMapper

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

class VictoriaStreamlitApp:
    """Main Streamlit application class"""
    
    def __init__(self):
        self.trait_scorer = TraitScorer()
        self.clustering_engine = TraitClusteringEngine()
        self.archetype_mapper = ArchetypeMapper()
        self._setup_page_config()
    
    def _setup_page_config(self):
        """Setup Streamlit page configuration"""
        st.set_page_config(
            page_title="Victoria Project - Psychometric Analysis",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply custom CSS with Vertria branding
        self._apply_custom_styles()
    
    def _apply_custom_styles(self):
        """Apply Vertria brand styling"""
        st.markdown(f"""
        <style>
        .main {{
            background-color: {brand_config.COLORS['white']};
        }}
        .sidebar .sidebar-content {{
            background-color: {brand_config.COLORS['light_gray']};
        }}
        h1, h2, h3 {{
            color: {brand_config.COLORS['primary_burgundy']};
            font-family: {brand_config.FONTS['header']};
        }}
        .metric-container {{
            background-color: {brand_config.COLORS['light_gray']};
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid {brand_config.COLORS['accent_yellow']};
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Main application entry point"""
        try:
            # Sidebar navigation
            page = self._create_sidebar()
            
            # Main content area
            if page == "Analysis":
                self._show_analysis_page()
            elif page == "Individual Reports":
                self._show_individual_reports()
            elif page == "Cluster Analysis":
                self._show_cluster_analysis()
            elif page == "Archetype Insights":
                self._show_archetype_insights()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"An error occurred: {e}")
    
    def _create_sidebar(self) -> str:
        """Create sidebar navigation"""
        st.sidebar.title("🏢 Victoria Project")
        st.sidebar.markdown("### Psychometric Analysis Platform")
        
        # Navigation
        page = st.sidebar.selectbox(
            "Navigate to:",
            ["Analysis", "Individual Reports", "Cluster Analysis", "Archetype Insights"]
        )
        
        # File upload section
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Data Upload")
        
        uploaded_file = st.sidebar.file_uploader(
            "Upload Response Data",
            type=['csv'],
            help="Upload psychometric assessment responses"
        )
        
        if uploaded_file:
            # Store in session state
            st.session_state['uploaded_data'] = uploaded_file
        
        return page
    
    def _show_analysis_page(self):
        """Show main analysis dashboard"""
        st.title("📊 Psychometric Analysis Dashboard")
        
        # Check for data
        if not self._check_data_availability():
            return
        
        # Main analysis workflow
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Status", "Ready", "✅")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if st.button("🔄 Process Data", type="primary"):
                self._process_data()
        
        with col3:
            if st.button("📄 Generate Reports"):
                self._generate_reports()
    
    def _show_individual_reports(self):
        """Show individual assessment reports"""
        st.title("👤 Individual Reports")
        
        if 'processed_profiles' not in st.session_state:
            st.info("Please process data first in the Analysis page.")
            return
        
        # Individual selection
        profiles = st.session_state.get('processed_profiles', {})
        if profiles:
            person_id = st.selectbox("Select Individual:", list(profiles.keys()))
            
            if person_id:
                profile = profiles[person_id]
                self._display_individual_report(profile)
    
    def _show_cluster_analysis(self):
        """Show cluster analysis results"""
        st.title("🎯 Trait Cluster Analysis")
        
        if 'cluster_results' not in st.session_state:
            st.info("Please process data first in the Analysis page.")
            return
        
        cluster_results = st.session_state.get('cluster_results')
        if cluster_results:
            self._display_cluster_results(cluster_results)
    
    def _show_archetype_insights(self):
        """Show Vertria archetype insights"""
        st.title("🏆 Entrepreneurial Archetype Insights")
        
        if 'processed_profiles' not in st.session_state:
            st.info("Please process data first in the Analysis page.")
            return
        
        profiles = st.session_state.get('processed_profiles', {})
        self._display_archetype_dashboard(profiles)
    
    def _check_data_availability(self) -> bool:
        """Check if required data files are available"""
        try:
            traits_file = config.traits_file_path
            if not os.path.exists(traits_file):
                st.error(f"Traits file not found: {traits_file}")
                st.info("Please ensure the trait annotations file is in the correct location.")
                return False
            
            # Check for response data
            if 'uploaded_data' not in st.session_state:
                responses_file = config.responses_file_path
                if not os.path.exists(responses_file):
                    st.warning("No response data file found. Please upload data using the sidebar.")
                    return False
            
            return True
            
        except Exception as e:
            st.error(f"Error checking data availability: {e}")
            return False
    
    def _process_data(self):
        """Process the uploaded/available data"""
        try:
            with st.spinner("Processing psychometric data..."):
                # Load and process data
                traits_file = config.traits_file_path
                responses_file = config.responses_file_path
                
                # Calculate trait scores
                profiles = self.trait_scorer.calculate_trait_scores(
                    responses_file, traits_file
                )
                
                if profiles:
                    # Perform clustering
                    cluster_results = self.clustering_engine.analyze_trait_clusters(profiles)
                    
                    # Store in session state
                    st.session_state['processed_profiles'] = profiles
                    st.session_state['cluster_results'] = cluster_results
                    
                    st.success(f"✅ Successfully processed {len(profiles)} profiles!")
                    
                    # Display summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Profiles", len(profiles))
                    
                    with col2:
                        st.metric("Clusters", cluster_results.n_clusters)
                    
                    with col3:
                        st.metric("Silhouette Score", f"{cluster_results.silhouette_score:.3f}")
                    
                    with col4:
                        avg_completion = np.mean([p.completion_rate for p in profiles.values()])
                        st.metric("Avg Completion", f"{avg_completion:.1%}")
                
                else:
                    st.error("❌ No profiles could be processed. Check your data files.")
                    
        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
            logger.error(f"Data processing error: {e}")
    
    def _display_individual_report(self, profile):
        """Display individual assessment report"""
        # Profile overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Overall Score", f"{profile.overall_score:.2f}")
        
        with col2:
            st.metric("Completion Rate", f"{profile.completion_rate:.1%}")
        
        with col3:
            if profile.primary_archetype:
                st.metric("Primary Archetype", 
                         profile.primary_archetype.archetype.value.replace('_', ' ').title())
        
        # Trait breakdown
        st.markdown("### Trait Profile")
        
        if profile.traits:
            trait_data = pd.DataFrame([
                {
                    'Trait': trait.trait_name,
                    'Score': trait.score,
                    'Percentile': trait.percentile,
                    'Level': trait.level.value if trait.level else 'N/A'
                }
                for trait in profile.traits
            ])
            
            st.dataframe(trait_data, use_container_width=True)
            
            # Trait visualization
            import plotly.graph_objects as go
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=[trait.percentile for trait in profile.traits],
                theta=[trait.trait_name for trait in profile.traits],
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
                showlegend=True,
                title="Trait Profile Radar Chart"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _display_cluster_results(self, cluster_results):
        """Display clustering analysis results"""
        st.markdown(f"### Clustering Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Number of Clusters", cluster_results.n_clusters)
        with col2:
            st.metric("Silhouette Score", f"{cluster_results.silhouette_score:.3f}")
        with col3:
            st.metric("Explained Variance", f"{cluster_results.explained_variance:.1%}")
        
        # Cluster details
        st.markdown("### Cluster Details")
        
        for cluster in cluster_results.clusters:
            with st.expander(f"Cluster {cluster.cluster_id + 1}: {cluster.cluster_name}"):
                st.write(f"**Description:** {cluster.description}")
                st.write(f"**Size:** {cluster.size} individuals")
                st.write(f"**Dominant Traits:** {', '.join(cluster.traits)}")
                
                if cluster.archetype_mapping:
                    st.write(f"**Archetype Mapping:** {cluster.archetype_mapping.value.replace('_', ' ').title()}")
    
    def _display_archetype_dashboard(self, profiles):
        """Display archetype analysis dashboard"""
        # Archetype distribution
        archetype_counts = {}
        for profile in profiles.values():
            if profile.primary_archetype:
                archetype = profile.primary_archetype.archetype.value
                archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1
        
        if archetype_counts:
            st.markdown("### Archetype Distribution")
            
            # Create pie chart
            import plotly.express as px
            fig = px.pie(
                values=list(archetype_counts.values()),
                names=[name.replace('_', ' ').title() for name in archetype_counts.keys()],
                title="Distribution of Primary Archetypes"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Archetype details
            st.markdown("### Archetype Insights")
            
            from victoria.config.settings import archetype_config
            for archetype_key, count in archetype_counts.items():
                with st.expander(f"{archetype_key.replace('_', ' ').title()} ({count} individuals)"):
                    archetype_info = archetype_config.ARCHETYPES[archetype_key]
                    st.write(f"**Description:** {archetype_info['description']}")
                    st.write(f"**Core Traits:** {', '.join(archetype_info['core_traits'])}")
                    st.write(f"**Characteristics:** {', '.join(archetype_info['characteristics'])}")
    
    def _generate_reports(self):
        """Generate comprehensive reports"""
        if 'processed_profiles' not in st.session_state:
            st.error("No processed data available. Please process data first.")
            return
        
        st.info("Report generation feature will be implemented in the next phase.")

# Application entry point
def main():
    """Main application entry point"""
    app = VictoriaStreamlitApp()
    app.run()

if __name__ == "__main__":
    main()