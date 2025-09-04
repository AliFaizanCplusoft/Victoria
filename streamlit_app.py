"""
Modular Streamlit App for Psychometric Assessment System - Updated with Comprehensive Processor
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import configuration
from config import config
BASE_DATA_PATH = config.BASE_DATA_PATH  # Keep for backwards compatibility

# Import modules
from src.data.comprehensive_processor import ComprehensiveDataProcessor
from src.scoring.scoring_engine import PsychometricScoringEngine
from src.clustering.clustering_engine import PsychometricClusteringEngine
from src.visualization.visualization_engine import PsychometricVisualizationEngine

# Try to import PDF report generator with comprehensive error handling
try:
    from src.reports.multi_format_report_generator import MultiFormatReportGenerator
    PDF_REPORTS_AVAILABLE = True
    PDF_ERROR_MESSAGE = None
except (ImportError, OSError, Exception) as e:
    # Handle all possible errors including OSError from WeasyPrint dependencies
    MultiFormatReportGenerator = None
    PDF_REPORTS_AVAILABLE = False
    PDF_ERROR_MESSAGE = f"PDF report generation is not available: {str(e)}"
    
    # Show a more user-friendly error message in Streamlit
    if "libgobject" in str(e):
        PDF_ERROR_MESSAGE = "PDF generation requires additional system libraries. HTML and CSV reports are still available."
    elif "weasyprint" in str(e).lower():
        PDF_ERROR_MESSAGE = "WeasyPrint is not properly installed. PDF generation is disabled, but other formats work."

from trait_scorer import TraitScorer
from trait_clustering import TraitClusteringEngine

# Page configuration
st.set_page_config(
    page_title="Psychometric Assessment System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E4057;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 2rem;
        font-weight: bold;
        color: #4A90E2;
        margin: 2rem 0 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4A90E2;
        margin: 1rem 0;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'rasch_results' not in st.session_state:
        st.session_state.rasch_results = None
    if 'scoring_results' not in st.session_state:
        st.session_state.scoring_results = None
    if 'clustering_results' not in st.session_state:
        st.session_state.clustering_results = None
    if 'comprehensive_processor' not in st.session_state:
        st.session_state.comprehensive_processor = ComprehensiveDataProcessor()
    if 'scoring_engine' not in st.session_state:
        st.session_state.scoring_engine = PsychometricScoringEngine()
    if 'clustering_engine' not in st.session_state:
        st.session_state.clustering_engine = PsychometricClusteringEngine()
    if 'visualization_engine' not in st.session_state:
        st.session_state.visualization_engine = PsychometricVisualizationEngine()
    if 'multi_format_generator' not in st.session_state:
        # Only initialize if available
        if PDF_REPORTS_AVAILABLE:
            st.session_state.multi_format_generator = MultiFormatReportGenerator()
        else:
            st.session_state.multi_format_generator = None
    if 'trait_scorer' not in st.session_state:
        st.session_state.trait_scorer = TraitScorer()
    if 'trait_profiles' not in st.session_state:
        st.session_state.trait_profiles = None
    if 'trait_clustering_engine' not in st.session_state:
        st.session_state.trait_clustering_engine = TraitClusteringEngine()
    if 'trait_clusters' not in st.session_state:
        st.session_state.trait_clusters = None
    if 'trait_correlation_matrix' not in st.session_state:
        st.session_state.trait_correlation_matrix = None

def load_and_process_data(data_source, assessment_source=None):
    """Load and process data using the comprehensive processor"""
    try:
        # Handle different data source types
        if hasattr(data_source, 'read'):
            # It's a file-like object (UploadedFile)
            import tempfile
            import os
            
            # Create temporary file for raw data
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(data_source.getvalue())
                raw_data_path = tmp_file.name
            
            # Set paths
            traits_file_path = config.traits_file_path
            responses_file_path = raw_data_path
            output_path = config.output_file_path
            
            try:
                # Use comprehensive processor with corrected file paths
                result = st.session_state.comprehensive_processor.process_complete_pipeline(
                    raw_data_path=raw_data_path,
                    traits_file_path=traits_file_path,
                    output_path=output_path,
                    responses_file_path=responses_file_path
                )
                
                if result.success:
                    st.session_state.raw_data = result.processed_data
                    st.session_state.processed_data = result.processed_data
                    st.session_state.rasch_results = {
                        'person_measures': result.person_abilities,
                        'item_measures': result.item_difficulties
                    }
                    
                    # Calculate trait scores from processed data
                    with st.spinner("Calculating trait scores..."):
                        st.session_state.trait_profiles = st.session_state.trait_scorer.calculate_trait_scores(
                            processed_data_path=result.output_file_path,
                            traits_file_path=traits_file_path
                        )
                        
                        # Create scoring results DataFrame for compatibility
                        if st.session_state.trait_profiles:
                            st.session_state.scoring_results = st.session_state.trait_scorer.create_scoring_dataframe(
                                st.session_state.trait_profiles
                            )
                    
                    st.success("✅ Data loaded and processed successfully!")
                    st.success("✅ Trait scores calculated successfully!")
                    st.info(f"📁 Output saved to: {result.output_file_path}")
                    
                    # Display processed output
                    if result.output_file_path and os.path.exists(result.output_file_path):
                        st.subheader("📄 Processed Output Preview")
                        
                        # Read and display the processed data
                        processed_df = pd.read_csv(result.output_file_path, sep='\t')
                        st.dataframe(processed_df.head(20))
                        
                        # Show summary statistics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Records", len(processed_df))
                        with col2:
                            st.metric("Unique Persons", processed_df['Persons'].nunique())
                        with col3:
                            st.metric("Unique Items", processed_df['Assessment_Items'].nunique())
                        with col4:
                            avg_measure = processed_df['Measure'].mean()
                            st.metric("Avg Measure", f"{avg_measure:.3f}")
                        
                        # Visualizations
                        st.subheader("📊 Data Visualizations")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Distribution of measures
                            fig_hist = px.histogram(
                                processed_df, 
                                x='Measure', 
                                title='Distribution of Measures',
                                nbins=30
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)
                        
                        with col2:
                            # Top 10 most frequent items
                            top_items = processed_df['Assessment_Items'].value_counts().head(10)
                            fig_bar = px.bar(
                                x=top_items.index,
                                y=top_items.values,
                                title='Top 10 Most Frequent Items',
                                labels={'x': 'Assessment Items', 'y': 'Frequency'}
                            )
                            fig_bar.update_xaxes(tickangle=45)
                            st.plotly_chart(fig_bar, use_container_width=True)
                        
                        # Download options
                        st.subheader("📥 Download Options")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Download as original tab-separated format
                            with open(result.output_file_path, 'r') as f:
                                tab_content = f.read()
                            
                            st.download_button(
                                label="📄 Download as TXT (Tab-separated)",
                                data=tab_content,
                                file_name="processed_data.txt",
                                mime="text/plain"
                            )
                        
                        with col2:
                            # Download as CSV
                            csv_content = processed_df.to_csv(index=False)
                            
                            st.download_button(
                                label="📊 Download as CSV",
                                data=csv_content,
                                file_name="processed_data.csv",
                                mime="text/csv"
                            )
                    
                    # Show processing log
                    with st.expander("Processing Log"):
                        for log_entry in result.processing_log:
                            st.info(log_entry)
                    
                    return True
                else:
                    st.error("❌ Data processing failed")
                    if result.errors:
                        for error in result.errors:
                            st.error(f"• {error}")
                    return False
                    
            finally:
                # Clean up temporary file
                if os.path.exists(raw_data_path):
                    os.unlink(raw_data_path)
        else:
            # It's a file path string (could be sample data or any data file)
            traits_file_path = config.traits_file_path
            output_path = config.output_file_path
            
            # Use comprehensive processor - the uploaded/selected data is the raw_data_path
            # Don't use the hardcoded responses_file_path, use the actual data source
            result = st.session_state.comprehensive_processor.process_complete_pipeline(
                raw_data_path=data_source,
                traits_file_path=traits_file_path,
                output_path=output_path,
                responses_file_path=data_source  # Use the actual data source, not hardcoded file
            )
            
            if result.success:
                st.session_state.raw_data = result.processed_data
                st.session_state.processed_data = result.processed_data
                st.session_state.rasch_results = {
                    'person_measures': result.person_abilities,
                    'item_measures': result.item_difficulties
                }
                
                # Calculate trait scores from processed data
                with st.spinner("Calculating trait scores..."):
                    st.session_state.trait_profiles = st.session_state.trait_scorer.calculate_trait_scores(
                        processed_data_path=result.output_file_path,
                        traits_file_path=traits_file_path
                    )
                    
                    # Create scoring results DataFrame for compatibility
                    if st.session_state.trait_profiles:
                        st.session_state.scoring_results = st.session_state.trait_scorer.create_scoring_dataframe(
                            st.session_state.trait_profiles
                        )
                
                st.success("✅ Data loaded and processed successfully!")
                st.success("✅ Trait scores calculated successfully!")
                st.info(f"📁 Output saved to: {result.output_file_path}")
                
                # Display processed output
                if result.output_file_path and os.path.exists(result.output_file_path):
                    st.subheader("📄 Processed Output Preview")
                    
                    # Read and display the processed data
                    processed_df = pd.read_csv(result.output_file_path, sep='\t')
                    st.dataframe(processed_df.head(20))
                    
                    # Show summary statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Records", len(processed_df))
                    with col2:
                        st.metric("Unique Persons", processed_df['Persons'].nunique())
                    with col3:
                        st.metric("Unique Items", processed_df['Assessment_Items'].nunique())
                    with col4:
                        avg_measure = processed_df['Measure'].mean()
                        st.metric("Avg Measure", f"{avg_measure:.3f}")
                    
                    # Visualizations
                    st.subheader("📊 Data Visualizations")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Distribution of measures
                        fig_hist = px.histogram(
                            processed_df, 
                            x='Measure', 
                            title='Distribution of Measures',
                            nbins=30
                        )
                        st.plotly_chart(fig_hist, use_container_width=True)
                    
                    with col2:
                        # Top 10 most frequent items
                        top_items = processed_df['Assessment_Items'].value_counts().head(10)
                        fig_bar = px.bar(
                            x=top_items.index,
                            y=top_items.values,
                            title='Top 10 Most Frequent Items',
                            labels={'x': 'Assessment Items', 'y': 'Frequency'}
                        )
                        fig_bar.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # Download options
                    st.subheader("📥 Download Options")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Download as original tab-separated format
                        with open(result.output_file_path, 'r') as f:
                            tab_content = f.read()
                        
                        st.download_button(
                            label="📄 Download as TXT (Tab-separated)",
                            data=tab_content,
                            file_name="processed_data.txt",
                            mime="text/plain"
                        )
                    
                    with col2:
                        # Download as CSV
                        csv_content = processed_df.to_csv(index=False)
                        
                        st.download_button(
                            label="📊 Download as CSV",
                            data=csv_content,
                            file_name="processed_data.csv",
                            mime="text/csv"
                        )
                
                # Show processing log
                with st.expander("Processing Log"):
                    for log_entry in result.processing_log:
                        st.info(log_entry)
                
                return True
            else:
                st.error("❌ Data processing failed")
                if result.errors:
                    for error in result.errors:
                        st.error(f"• {error}")
                return False
                
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return False

def sidebar_navigation():
    """Create sidebar navigation"""
    st.sidebar.title("🧠 Navigation")
    
    # Show PDF status in sidebar
    if not PDF_REPORTS_AVAILABLE:
        st.sidebar.warning(f"⚠️ {PDF_ERROR_MESSAGE}")
    
    pages = {
        "📊 Data Upload": "data_upload",
        "🔍 Data Overview": "data_overview",
        "📈 Rasch Analysis": "rasch_analysis",
        "📊 Trait Scores": "scoring_results",
        "🎯 Trait Clustering": "clustering",
        "👤 Individual Analysis": "individual_analysis",
        "📋 Group Analysis": "group_analysis",
        "📄 Reports": "reports"
    }
    
    selected_page = st.sidebar.selectbox(
        "Select Page",
        list(pages.keys())
    )
    
    return pages[selected_page]

def data_upload_page():
    """Data upload and ingestion page"""
    st.markdown('<div class="main-header">📊 Data Upload & Ingestion</div>', unsafe_allow_html=True)
    
    # Show PDF status if there are issues
    if not PDF_REPORTS_AVAILABLE:
        st.info(f"ℹ️ {PDF_ERROR_MESSAGE}")
    
    # Upload options
    st.subheader("📁 Data Source")
    
    upload_option = st.radio(
        "Choose data source:",
        ["Upload Files", "Use Sample Data"],
        horizontal=True
    )
    
    if upload_option == "Use Sample Data":
        st.info("Select a CSV file from your project directory to use as sample data")
        
        # Find available CSV files in the project directory
        import glob
        csv_files = glob.glob(os.path.join(config.BASE_DATA_PATH, "*.csv"))
        csv_files = [f for f in csv_files if os.path.exists(f)]
        
        if csv_files:
            # Let user select which CSV file to use
            file_options = [os.path.basename(f) for f in csv_files]
            default_index = 0
            
            # Try to find the configured default file
            default_filename = os.path.basename(config.responses_file_path)
            if default_filename in file_options:
                default_index = file_options.index(default_filename)
            
            selected_file = st.selectbox(
                "Select CSV file:",
                file_options,
                index=default_index
            )
            
            selected_path = os.path.join(config.BASE_DATA_PATH, selected_file)
            
            # Show file info
            if os.path.exists(selected_path):
                file_size = os.path.getsize(selected_path)
                st.write(f"📄 File: `{selected_file}` ({file_size:,} bytes)")
                
                # Show preview of the data
                try:
                    preview_df = pd.read_csv(selected_path, nrows=3)
                    st.write(f"📊 Preview - {len(preview_df.columns)} columns, showing first 3 rows:")
                    st.dataframe(preview_df)
                except Exception as e:
                    st.warning(f"Could not preview file: {e}")
            
            if st.button("Load Selected Data"):
                if os.path.exists(selected_path):
                    load_and_process_data(selected_path)
                else:
                    st.error("❌ Selected file not found.")
        else:
            st.warning("❌ No CSV files found in the project directory.")
            st.info("Please add CSV files to the project directory, or use the 'Upload Files' option.")
    else:
        uploaded_file = st.file_uploader("Upload response data CSV", type=['csv'])
        
        if uploaded_file is not None:
            if st.button("Process Data"):
                load_and_process_data(uploaded_file)
    
    # Data status
    if st.session_state.raw_data is not None:
        st.success("✅ Data loaded successfully!")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", len(st.session_state.raw_data))
        with col2:
            st.metric("Columns", len(st.session_state.raw_data.columns))
        with col3:
            st.metric("Missing Values", st.session_state.raw_data.isnull().sum().sum())

def data_overview_page():
    """Data overview and exploration page"""
    st.markdown('<div class="main-header">🔍 Data Overview</div>', unsafe_allow_html=True)
    
    if st.session_state.raw_data is None:
        st.warning("⚠️ Please upload data first.")
        return
    
    # Data summary
    st.subheader("📊 Data Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Responses", len(st.session_state.raw_data))
    with col2:
        st.metric("Total Items", len(st.session_state.raw_data.columns))
    with col3:
        st.metric("Missing Values", st.session_state.raw_data.isnull().sum().sum())
    with col4:
        st.metric("Completion Rate", f"{(1 - st.session_state.raw_data.isnull().sum().sum() / st.session_state.raw_data.size) * 100:.1f}%")
    
    # Data preview
    st.subheader("🔍 Data Preview")
    st.dataframe(st.session_state.raw_data.head(10))
    
    # Processed output section
    output_file = config.output_file_path
    if os.path.exists(output_file):
        st.subheader("📄 Processed Output")
        st.info(f"✅ Processed data saved to: {output_file}")
        
        # Read and display processed data
        try:
            processed_df = pd.read_csv(output_file, sep='\t')
            
            # Show preview
            st.subheader("🔍 Processed Data Preview")
            st.dataframe(processed_df.head(20))
            
            # Show summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(processed_df))
            with col2:
                st.metric("Unique Persons", processed_df['Persons'].nunique())
            with col3:
                st.metric("Unique Items", processed_df['Assessment_Items'].nunique())
            with col4:
                avg_measure = processed_df['Measure'].mean()
                st.metric("Avg Measure", f"{avg_measure:.3f}")
            
            # Visualizations
            st.subheader("📊 Data Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution of measures
                fig_hist = px.histogram(
                    processed_df, 
                    x='Measure', 
                    title='Distribution of Measures',
                    nbins=30
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Top 10 most frequent items
                top_items = processed_df['Assessment_Items'].value_counts().head(10)
                fig_bar = px.bar(
                    x=top_items.index,
                    y=top_items.values,
                    title='Top 10 Most Frequent Items',
                    labels={'x': 'Assessment Items', 'y': 'Frequency'}
                )
                fig_bar.update_xaxes(tickangle=45)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Download options
            st.subheader("📥 Download Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download as original tab-separated format
                with open(output_file, 'r') as f:
                    tab_content = f.read()
                
                st.download_button(
                    label="📄 Download as TXT (Tab-separated)",
                    data=tab_content,
                    file_name="processed_data.txt",
                    mime="text/plain"
                )
            
            with col2:
                # Download as CSV
                csv_content = processed_df.to_csv(index=False)
                
                st.download_button(
                    label="📊 Download as CSV",
                    data=csv_content,
                    file_name="processed_data.csv",
                    mime="text/csv"
                )
        
        except Exception as e:
            st.error(f"❌ Error reading processed output: {str(e)}")
            
            # Fallback download option
            with open(output_file, 'r') as f:
                processed_content = f.read()
            
            st.download_button(
                label="Download Processed Data (TXT)",
                data=processed_content,
                file_name="processed_data.txt",
                mime="text/plain"
            )

def rasch_analysis_page():
    """Rasch analysis page"""
    st.markdown('<div class="main-header">📈 Rasch Analysis</div>', unsafe_allow_html=True)
    
    if st.session_state.processed_data is None:
        st.warning("⚠️ Please process data first.")
        return
    
    # Display results
    if st.session_state.rasch_results is not None:
        st.subheader("📊 Rasch Analysis Results")
        
        # Person measures
        if st.session_state.rasch_results.get('person_measures') is not None:
            st.subheader("👤 Person Measures")
            st.dataframe(st.session_state.rasch_results['person_measures'])
        
        # Item measures
        if st.session_state.rasch_results.get('item_measures') is not None:
            st.subheader("📋 Item Measures")
            st.dataframe(st.session_state.rasch_results['item_measures'])
    else:
        st.info("Rasch analysis results will appear here after data processing.")

def scoring_results_page():
    """Scoring results page - now shows trait scores calculated from processed data"""
    st.markdown('<div class="main-header">📊 Trait Scores</div>', unsafe_allow_html=True)
    
    if st.session_state.scoring_results is None:
        st.warning("⚠️ Please process data first to generate trait scores.")
        return
    
    # Display results
    st.subheader("📊 Trait Scores Overview")
    
    # Score summary
    if isinstance(st.session_state.scoring_results, pd.DataFrame):
        st.dataframe(st.session_state.scoring_results)
        
        # Show trait score statistics
        st.subheader("📈 Trait Score Statistics")
        
        # Filter only numeric trait columns for visualization
        trait_cols = [col for col in st.session_state.scoring_results.columns 
                     if col not in ['overall_score', 'overall_percentile', 'completion_rate']]
        
        if len(trait_cols) > 0:
            try:
                # Create box plot with trait columns
                fig = px.box(st.session_state.scoring_results[trait_cols])
                fig.update_layout(
                    title="Trait Score Distributions",
                    xaxis_title="Traits",
                    yaxis_title="Scores (0.0 - 1.0)",
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary statistics
                st.subheader("📊 Summary Statistics")
                st.dataframe(st.session_state.scoring_results[trait_cols].describe())
                
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
                # Fallback: show basic statistics
                st.subheader("📊 Summary Statistics")
                st.dataframe(st.session_state.scoring_results.describe())
        else:
            st.warning("No trait columns found for visualization")
    
    # Show trait profiles information if available
    if st.session_state.trait_profiles:
        st.subheader("📋 Trait Profiles Summary")
        
        # Create summary of all profiles
        profile_summary = []
        for person_id, profile in st.session_state.trait_profiles.items():
            profile_summary.append({
                'Person ID': person_id,
                'Overall Score': f"{profile.overall_score:.3f}",
                'Completion Rate': f"{profile.completion_rate:.1%}",
                'Traits Count': len(profile.traits),
                'Top Trait': max(profile.traits, key=lambda x: x.score).trait_name if profile.traits else 'N/A',
                'Top Score': f"{max(profile.traits, key=lambda x: x.score).score:.3f}" if profile.traits else 'N/A'
            })
        
        summary_df = pd.DataFrame(profile_summary)
        st.dataframe(summary_df, use_container_width=True)

def clustering_page():
    """Trait clustering analysis page"""
    st.markdown('<div class="main-header">🎯 Trait Clustering Analysis</div>', unsafe_allow_html=True)
    
    if st.session_state.processed_data is None:
        st.warning("⚠️ Please process data first.")
        return
    
    st.info("🔍 **Trait Clustering** analyzes how traits correlate with each other across all individuals. Traits that tend to co-occur (high correlation) will cluster together.")
    
    # Clustering parameters
    st.subheader("⚙️ Clustering Parameters")
    n_clusters = st.slider("Number of Trait Clusters", 2, 10, 5)
    
    if st.button("Run Trait Clustering"):
        with st.spinner("Analyzing trait correlations and clustering..."):
            try:
                # Calculate trait correlation matrix
                traits_file_path = config.traits_file_path
                processed_data_path = config.output_file_path
                
                corr_matrix, trait_data = st.session_state.trait_clustering_engine.calculate_trait_correlation_matrix(
                    processed_data_path=processed_data_path,
                    traits_file_path=traits_file_path
                )
                
                if not corr_matrix.empty:
                    st.session_state.trait_correlation_matrix = corr_matrix
                    
                    # Cluster traits
                    clusters = st.session_state.trait_clustering_engine.cluster_traits(
                        corr_matrix, n_clusters=n_clusters
                    )
                    
                    st.session_state.trait_clusters = clusters
                    st.success("✅ Trait clustering completed!")
                else:
                    st.error("❌ Failed to calculate trait correlations")
                    
            except Exception as e:
                st.error(f"❌ Error running trait clustering: {str(e)}")
    
    # Display results
    if st.session_state.trait_clusters is not None and st.session_state.trait_correlation_matrix is not None:
        st.subheader("🎯 Trait Clustering Results")
        
        # Show cluster summary
        st.subheader("📊 Cluster Summary")
        summary_df = st.session_state.trait_clustering_engine.create_cluster_summary(
            st.session_state.trait_clusters
        )
        st.dataframe(summary_df, use_container_width=True)
        
        # Show detailed cluster information
        st.subheader("🔍 Detailed Cluster Analysis")
        
        for cluster in st.session_state.trait_clusters:
            with st.expander(f"🎯 {cluster.cluster_name} (Size: {cluster.size})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Traits in this cluster:**")
                    for trait in cluster.traits:
                        trait_name = st.session_state.trait_clustering_engine.trait_mapping.get(trait, trait)
                        st.write(f"• {trait_name} ({trait})")
                
                with col2:
                    st.write("**Cluster Description:**")
                    st.info(cluster.description)
                    
                    st.write("**Interpretation:**")
                    if cluster.cluster_id == 0:
                        st.write("These traits represent innovation and risk-taking behaviors.")
                    elif cluster.cluster_id == 1:
                        st.write("These traits represent leadership and execution capabilities.")
                    elif cluster.cluster_id == 2:
                        st.write("These traits represent resilience and adaptability.")
                    elif cluster.cluster_id == 3:
                        st.write("These traits represent analytical and strategic thinking.")
                    else:
                        st.write("These traits represent collaborative and social behaviors.")
        
        # Show correlation heatmap
        st.subheader("🔥 Trait Correlation Heatmap")
        
        try:
            # Create correlation heatmap
            fig = go.Figure(data=go.Heatmap(
                z=st.session_state.trait_correlation_matrix.values,
                x=[st.session_state.trait_clustering_engine.trait_mapping.get(t, t) 
                   for t in st.session_state.trait_correlation_matrix.columns],
                y=[st.session_state.trait_clustering_engine.trait_mapping.get(t, t) 
                   for t in st.session_state.trait_correlation_matrix.index],
                colorscale='RdBu',
                zmid=0,
                text=st.session_state.trait_correlation_matrix.values.round(2),
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="Correlation")
            ))
            
            fig.update_layout(
                title="Trait Correlation Matrix",
                xaxis_title="Traits",
                yaxis_title="Traits",
                height=600,
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating correlation heatmap: {str(e)}")
        
        # Show cluster visualization
        st.subheader("📈 Trait Cluster Visualization")
        
        try:
            # Create cluster visualization
            viz_fig = st.session_state.trait_clustering_engine.visualize_trait_clusters(
                st.session_state.trait_correlation_matrix,
                st.session_state.trait_clusters
            )
            
            st.plotly_chart(viz_fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating cluster visualization: {str(e)}")
        
        # Show strongest correlations
        st.subheader("💪 Strongest Trait Correlations")
        
        try:
            # Find strongest correlations
            corr_matrix = st.session_state.trait_correlation_matrix
            strong_correlations = []
            
            for i in range(len(corr_matrix)):
                for j in range(i+1, len(corr_matrix)):
                    corr = corr_matrix.iloc[i, j]
                    if abs(corr) > 0.5:  # Strong correlation threshold
                        trait1_name = st.session_state.trait_clustering_engine.trait_mapping.get(
                            corr_matrix.index[i], corr_matrix.index[i]
                        )
                        trait2_name = st.session_state.trait_clustering_engine.trait_mapping.get(
                            corr_matrix.index[j], corr_matrix.index[j]
                        )
                        
                        strong_correlations.append({
                            'Trait 1': trait1_name,
                            'Trait 2': trait2_name,
                            'Correlation': f"{corr:.3f}",
                            'Strength': 'Very Strong' if abs(corr) > 0.7 else 'Strong',
                            'Direction': 'Positive' if corr > 0 else 'Negative'
                        })
            
            if strong_correlations:
                # Sort by absolute correlation
                strong_correlations.sort(key=lambda x: abs(float(x['Correlation'])), reverse=True)
                
                corr_df = pd.DataFrame(strong_correlations)
                st.dataframe(corr_df, use_container_width=True)
                
                st.info(f"📊 Found {len(strong_correlations)} strong correlations (|r| > 0.5)")
            else:
                st.info("No strong correlations found (threshold: |r| > 0.5)")
                
        except Exception as e:
            st.error(f"Error analyzing correlations: {str(e)}")
    
    elif st.session_state.trait_correlation_matrix is not None:
        st.info("Trait correlation matrix calculated. Run clustering to see results.")
    else:
        st.info("Click 'Run Trait Clustering' to analyze how traits correlate with each other.")

def individual_analysis_page():
    """Individual person analysis page"""
    st.markdown('<div class="main-header">👤 Individual Analysis</div>', unsafe_allow_html=True)
    
    if st.session_state.scoring_results is None:
        st.warning("⚠️ Please process data first to generate trait scores.")
        return
    
    # Person selection
    st.subheader("🔍 Select Person")
    person_ids = st.session_state.scoring_results.index.tolist()
    selected_person = st.selectbox("Select Person ID", person_ids)
    
    if selected_person is not None:
        person_data = st.session_state.scoring_results.loc[selected_person]
        
        # Assessment Overview
        st.subheader("📊 Assessment Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_score = person_data.get('overall_score', person_data.mean())
            if overall_score is not None:
                st.metric("Overall Score", f"{overall_score:.1f}")
            else:
                st.metric("Overall Score", "N/A")
        
        with col2:
            # Count non-null traits
            trait_count = len([col for col in person_data.index if col not in ['overall_score', 'overall_percentile', 'completion_rate']])
            st.metric("Traits Assessed", trait_count)
        
        with col3:
            completion_rate = person_data.get('completion_rate', 0.95)
            if completion_rate is not None:
                st.metric("Completion Rate", f"{completion_rate*100:.1f}%")
            else:
                st.metric("Completion Rate", "95.0%")
        
        with col4:
            overall_percentile = person_data.get('overall_percentile', 50)
            if overall_percentile is not None:
                st.metric("Overall Percentile", f"{overall_percentile:.0f}th")
            else:
                st.metric("Overall Percentile", "50th")
        
        # Trait Profile Radar Chart
        st.subheader("📈 Trait Profile Radar Chart")
        try:
            # Get trait scores (exclude metadata columns)
            trait_cols = [col for col in person_data.index if col not in ['overall_score', 'overall_percentile', 'completion_rate']]
            trait_scores = person_data[trait_cols]
            
            # Filter out null values and scale scores to 0-100 for better visualization
            trait_scores_clean = trait_scores.dropna()
            if len(trait_scores_clean) == 0:
                st.warning("No valid trait scores available for radar chart")
                return
            
            scaled_scores = (trait_scores_clean * 100).fillna(0)
            
            # Create closed loop for radar chart
            clean_trait_cols = trait_scores_clean.index.tolist()
            theta_values = clean_trait_cols + [clean_trait_cols[0]]
            r_values = scaled_scores.tolist() + [scaled_scores.iloc[0]]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=r_values,
                theta=theta_values,
                fill='toself',
                name='Your Profile',
                line=dict(color='rgba(102, 126, 234, 0.8)', width=3),
                fillcolor='rgba(102, 126, 234, 0.3)',
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        tickmode='linear',
                        tick0=0,
                        dtick=20
                    )
                ),
                title=f"Trait Profile: {selected_person}",
                showlegend=False,
                height=400,
                margin=dict(l=20, r=20, t=60, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error creating radar chart: {str(e)}")
        
        # Individual Trait Breakdown
        st.subheader("📊 Individual Trait Breakdown")
        try:
            # Get trait scores and create color mapping
            trait_cols = [col for col in person_data.index if col not in ['overall_score', 'overall_percentile', 'completion_rate']]
            trait_scores = person_data[trait_cols]
            
            # Filter out null values
            trait_scores_clean = trait_scores.dropna()
            if len(trait_scores_clean) == 0:
                st.warning("No valid trait scores available for bar chart")
                return
            
            # Create color mapping based on score levels
            colors = []
            for score in trait_scores_clean:
                if pd.isna(score):
                    colors.append('rgba(128, 128, 128, 0.8)')  # Gray for null
                elif score >= 0.7:
                    colors.append('rgba(40, 167, 69, 0.8)')  # Green for high
                elif score >= 0.5:
                    colors.append('rgba(255, 193, 7, 0.8)')  # Yellow for medium
                else:
                    colors.append('rgba(220, 53, 69, 0.8)')  # Red for low
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=trait_scores_clean.index,
                y=trait_scores_clean.values,
                marker=dict(
                    color=colors,
                    line=dict(color='rgba(0,0,0,0.3)', width=1)
                ),
                text=[f'{score:.2f}' for score in trait_scores_clean.values],
                textfont=dict(color='white', size=11),
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Score: %{y:.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"Individual Trait Scores - {selected_person}",
                xaxis_title="Traits",
                yaxis_title="Score (0.0 - 1.0)",
                xaxis=dict(tickangle=-45),
                yaxis=dict(range=[0, 1], tickformat='.2f'),
                height=500,
                margin=dict(l=50, r=50, t=80, b=150),
                plot_bgcolor='rgba(255,255,255,0.9)',
                paper_bgcolor='white',
                showlegend=False
            )
            
            # Add benchmark line
            fig.add_hline(y=0.5, line_dash="dash", line_color="gray", 
                         annotation_text="Average Benchmark", 
                         annotation_position="top right")
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error creating trait breakdown: {str(e)}")
        
        # Strengths vs Development Areas
        st.subheader("💪 Strengths vs Development Areas")
        try:
            trait_cols = [col for col in person_data.index if col not in ['overall_score', 'overall_percentile', 'completion_rate']]
            trait_scores = person_data[trait_cols].dropna().sort_values(ascending=False)
            
            if len(trait_scores) == 0:
                st.warning("No valid trait scores available for strengths/development analysis")
                return
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=("Top 5 Strengths", "Key Development Areas"),
                horizontal_spacing=0.1
            )
            
            # Top strengths (max 5)
            top_n = min(5, len(trait_scores))
            top_traits = trait_scores.head(top_n)
            fig.add_trace(
                go.Bar(
                    x=top_traits.values,
                    y=top_traits.index,
                    orientation='h',
                    marker_color='rgba(40, 167, 69, 0.8)',
                    text=[f'{score:.2f}' for score in top_traits.values],
                    textposition='auto',
                    hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>',
                    name='Strengths'
                ),
                row=1, col=1
            )
            
            # Bottom development areas (max 5)
            bottom_n = min(5, len(trait_scores))
            bottom_traits = trait_scores.tail(bottom_n)
            fig.add_trace(
                go.Bar(
                    x=bottom_traits.values,
                    y=bottom_traits.index,
                    orientation='h',
                    marker_color='rgba(255, 193, 7, 0.8)',
                    text=[f'{score:.2f}' for score in bottom_traits.values],
                    textposition='auto',
                    hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>',
                    name='Development Areas'
                ),
                row=1, col=2
            )
            
            fig.update_layout(
                title=f"Strengths vs Development Profile - {selected_person}",
                showlegend=False,
                height=400,
                margin=dict(l=120, r=50, t=80, b=50)
            )
            
            fig.update_xaxes(title_text="Score", range=[0, 1])
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error creating strengths/development chart: {str(e)}")
        
        # Detailed Scores Table
        st.subheader("📋 Complete Score Breakdown")
        try:
            # Create a detailed table
            trait_cols = [col for col in person_data.index if col not in ['overall_score', 'overall_percentile', 'completion_rate']]
            
            table_data = []
            for trait in trait_cols:
                score = person_data[trait]
                
                # Handle null scores
                if score is None or pd.isna(score):
                    table_data.append({
                        'Trait': trait,
                        'Score': "N/A",
                        'Level': "⚪ N/A",
                        'Percentile': "N/A"
                    })
                    continue
                
                # Determine interpretation
                if score >= 0.7:
                    interpretation = "High"
                    color = "🟢"
                elif score >= 0.5:
                    interpretation = "Moderate"
                    color = "🟡"
                else:
                    interpretation = "Developing"
                    color = "🔴"
                
                table_data.append({
                    'Trait': trait,
                    'Score': f"{score:.2f}",
                    'Level': f"{color} {interpretation}",
                    'Percentile': f"{score * 100:.0f}th"
                })
            
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error creating scores table: {str(e)}")
        
        # Personalized Insights
        st.subheader("💡 Personalized Insights")
        try:
            trait_cols = [col for col in person_data.index if col not in ['overall_score', 'overall_percentile', 'completion_rate']]
            trait_scores = person_data[trait_cols]
            
            # Overall assessment
            overall_score = person_data.get('overall_score', trait_scores.mean())
            if overall_score is not None:
                score_range = 'strong' if overall_score >= 0.7 else 'moderate' if overall_score >= 0.5 else 'developing'
                st.info(f"**Overall Assessment:** {selected_person} shows solid potential with an overall score of {overall_score:.1f}. This individual ranks in the {score_range} range.")
            else:
                st.info(f"**Overall Assessment:** {selected_person} shows assessment results based on individual trait analysis.")
            
            # Key strengths
            strengths_n = min(3, len(trait_scores))
            if strengths_n > 0:
                strengths = trait_scores.nlargest(strengths_n)
                strengths_text = ", ".join(strengths.index)
                st.success(f"**Key Strengths:** The assessment reveals particular strength in {strengths_text}. These capabilities suggest natural aptitude for leadership and organizational development.")
            
            # Development opportunities
            development_n = min(2, len(trait_scores))
            if development_n > 0:
                development_areas = trait_scores.nsmallest(development_n)
                development_text = " and ".join(development_areas.index)
                st.warning(f"**Development Opportunities:** Areas with the greatest potential for growth include {development_text}. Focused development in these areas could significantly enhance overall effectiveness.")
            
        except Exception as e:
            st.error(f"❌ Error generating insights: {str(e)}")
        
        # Detailed Trait Information (if available)
        if st.session_state.trait_profiles and selected_person in st.session_state.trait_profiles:
            st.subheader("📋 Detailed Trait Information")
            
            profile = st.session_state.trait_profiles[selected_person]
            
            # Create expandable sections for each trait
            for trait in profile.traits:
                with st.expander(f"🔍 {trait.trait_name} - Score: {trait.score:.2f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Raw Score", f"{trait.score:.3f}")
                        st.metric("Percentile", f"{trait.percentile:.0f}th")
                    
                    with col2:
                        st.metric("Items Count", trait.items_count)
                        st.info(trait.description)
                    
                    # Show trait level
                    if trait.score >= 0.7:
                        st.success("🟢 **High Level** - This is a significant strength")
                    elif trait.score >= 0.5:
                        st.info("🟡 **Moderate Level** - Room for development")
                    else:
                        st.warning("🔴 **Developing Level** - Priority area for growth")
        
        # Raw Data Preview
        with st.expander("📊 Raw Trait Data Preview"):
            if st.session_state.trait_profiles and selected_person in st.session_state.trait_profiles:
                profile = st.session_state.trait_profiles[selected_person]
                
                # Create a summary table
                trait_data = []
                for trait in profile.traits:
                    trait_data.append({
                        'Trait': trait.trait_name,
                        'Score': f"{trait.score:.3f}",
                        'Percentile': f"{trait.percentile:.1f}th",
                        'Items': trait.items_count,
                        'Description': trait.description
                    })
                
                trait_df = pd.DataFrame(trait_data)
                st.dataframe(trait_df, use_container_width=True)
                
                # Show overall metrics
                st.subheader("📊 Overall Metrics")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Overall Score", f"{profile.overall_score:.3f}")
                    st.metric("Total Traits", len(profile.traits))
                
                with col2:
                    st.metric("Completion Rate", f"{profile.completion_rate:.1%}")
                    st.metric("Person ID", profile.person_id)
            else:
                st.info("Detailed trait profiles not available. Please process data first.")

def group_analysis_page():
    """Group analysis page"""
    st.markdown('<div class="main-header">📋 Group Analysis</div>', unsafe_allow_html=True)
    
    if st.session_state.scoring_results is None:
        st.warning("⚠️ Please generate scores first.")
        return
    
    # Group statistics
    st.subheader("📊 Group Statistics")
    
    # Summary statistics
    summary_stats = st.session_state.scoring_results.describe()
    st.dataframe(summary_stats)
    
    # Correlation matrix
    st.subheader("🔗 Trait Correlations")
    corr_matrix = st.session_state.scoring_results.corr()
    fig = px.imshow(corr_matrix, text_auto=True, aspect="auto")
    st.plotly_chart(fig, use_container_width=True)

def reports_page():
    """Reports generation page"""
    st.markdown('<div class="main-header">📄 Reports</div>', unsafe_allow_html=True)
    
    if st.session_state.processed_data is None:
        st.warning("⚠️ Please process data first.")
        return
    
    # Show PDF availability status
    if not PDF_REPORTS_AVAILABLE:
        st.warning(f"⚠️ {PDF_ERROR_MESSAGE}")
        st.info("📋 Available formats: HTML, CSV, TXT")
    else:
        st.success("✅ All report formats available including PDF")
    
    # Report options
    st.subheader("📋 Report Options")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Individual Report", "Group Report", "Comprehensive Report"]
    )
    
    # Filter output formats based on availability
    available_formats = ["HTML", "CSV", "TXT"]
    if PDF_REPORTS_AVAILABLE:
        available_formats.insert(0, "PDF")
    
    output_format = st.selectbox(
        "Select Output Format",
        available_formats
    )
    
    if st.button("Generate Report"):
        with st.spinner("Generating report..."):
            try:
                if output_format == "PDF" and not PDF_REPORTS_AVAILABLE:
                    st.error("❌ PDF generation is not available. Please select another format.")
                    return
                
                if PDF_REPORTS_AVAILABLE and st.session_state.multi_format_generator:
                    st.info("Report generation with full PDF support will be implemented here.")
                else:
                    st.info(f"Report generation for {output_format} format will be implemented here.")
                    
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
    
    # Show processed output file
    output_file = config.output_file_path
    if os.path.exists(output_file):
        st.subheader("📄 Current Processed Output")
        st.info(f"✅ Processed data available at: {output_file}")
        
        # Show download button
        with open(output_file, 'r') as f:
            processed_content = f.read()
        
        st.download_button(
            label="Download Processed Data",
            data=processed_content,
            file_name="processed_data.txt",
            mime="text/plain"
        )

def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🧠 Psychometric Assessment System</div>', unsafe_allow_html=True)
    
    # Navigation
    selected_page = sidebar_navigation()
    
    # Page routing
    if selected_page == "data_upload":
        data_upload_page()
    elif selected_page == "data_overview":
        data_overview_page()
    elif selected_page == "rasch_analysis":
        rasch_analysis_page()
    elif selected_page == "scoring_results":
        scoring_results_page()
    elif selected_page == "clustering":
        clustering_page()
    elif selected_page == "individual_analysis":
        individual_analysis_page()
    elif selected_page == "group_analysis":
        group_analysis_page()
    elif selected_page == "reports":
        reports_page()

if __name__ == "__main__":
    main()