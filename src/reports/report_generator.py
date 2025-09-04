import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
import pdfkit
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import platform

# Setup Jinja2 environment
template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "html")
if not os.path.exists(template_dir):
    print(f"Warning: Template directory not found: {template_dir}")
    template_dir = os.path.join(os.path.dirname(__file__), "templates")

env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(["html", "xml"])
)

# Configure pdfkit for text-only PDF generation (no JavaScript/visualizations)
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'no-outline': None,
    'enable-local-file-access': None,
    'disable-smart-shrinking': '',
    'print-media-type': '',
    'load-error-handling': 'ignore',
    'load-media-error-handling': 'ignore',
    # Disable JavaScript for faster, more reliable PDF generation
    'disable-javascript': '',
    'enable-internal-links': '',
    'images': '',
    # Additional PDF optimization
    'minimum-font-size': 12,
    'zoom': 1.0,
}

# Setup pdfkit configuration for Windows
pdfkit_config = None
if platform.system() == 'Windows':
    # Common installation paths for wkhtmltopdf on Windows
    possible_paths = [
        r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\wkhtmltopdf\bin\wkhtmltopdf.exe',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            pdfkit_config = pdfkit.configuration(wkhtmltopdf=path)
            break

# Add custom filters
def format_score(value, precision=1):
    """Format score to specified precision."""
    try:
        return f"{float(value):.{precision}f}"
    except (ValueError, TypeError):
        return "N/A"

def format_percentile(value):
    """Format percentile with ordinal suffix."""
    try:
        num = int(float(value))
        if 10 <= num % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
        return f"{num}{suffix}"
    except (ValueError, TypeError):
        return "N/A"

env.filters['format_score'] = format_score
env.filters['format_percentile'] = format_percentile

def generate_html_report(
    person: Any,
    cluster: Any = None,
    narratives: Dict[str, str] = None,
    visuals: Dict[str, str] = None,
    template_name: str = "comprehensive_report_template.html",
    archetype_profile: Any = None
) -> str:
    """
    Generate HTML report string.
    
    Args:
        person: PersonScore object
        cluster: ClusterResult object (optional)
        narratives: dict of narrative text (optional)
        visuals: dict of embedded HTML visualizations (optional)
        template_name: name of template file to use
        archetype_profile: ArchetypeProfile object (optional)
        
    Returns:
        HTML string
    """
    try:
        template = env.get_template(template_name)
    except Exception:
        # Fallback to basic template
        template = env.get_template("report_template.html")
    
    # Prepare template context
    context = {
        'person': person,
        'cluster': cluster,
        'narratives': narratives or {},
        'visuals': visuals or {},
        'archetype_profile': archetype_profile,
        'report_date': datetime.now().strftime("%B %d, %Y"),
        'generation_timestamp': datetime.now().isoformat()
    }
    
    html = template.render(**context)
    return html

def generate_comprehensive_report(
    person: Any,
    cluster: Any = None,
    all_person_scores: List[Any] = None,
    archetype_profile: Any = None,
    include_visuals: bool = True,
    output_format: str = "html",
    raw_data: Any = None
) -> str:
    """
    Generate a comprehensive report with enhanced narratives and insights.
    
    Args:
        person: PersonScore object
        cluster: ClusterResult object
        all_person_scores: List of all PersonScore objects for context
        archetype_profile: ArchetypeProfile object
        include_visuals: Whether to generate and include visualizations
        output_format: "html" or "pdf" - PDF format excludes visualizations
        raw_data: Raw assessment data for RaschPy processing
        
    Returns:
        HTML string for comprehensive report
    """
    # Process individual data through complete pipeline if raw_data provided
    if raw_data is not None:
        person = _process_individual_through_pipeline(person, raw_data)
    
    # Generate intelligent narratives
    narratives = generate_intelligent_narratives(person, cluster, archetype_profile)
    
    # Generate visualizations only for HTML format
    visuals = {}
    if include_visuals and output_format == "html":
        try:
            # Import visualization engine with absolute import
            import sys
            from pathlib import Path
            
            # Add the src directory to the path if not already there
            src_path = Path(__file__).parent.parent
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))
            
            from visualization.visualization_engine import PsychometricVisualizationEngine
            viz_engine = PsychometricVisualizationEngine()
            
            # Create interactive visualizations for HTML only
            try:
                visuals['Trait Profile Radar Chart'] = viz_engine.create_embedded_chart_html(person)
                visuals['Individual Trait Breakdown'] = _create_embedded_bar_chart(person)
                visuals['Strengths vs Development Areas'] = _create_strengths_development_chart(person)
            except Exception as e:
                print(f"Warning: Could not create interactive charts: {e}")
                # Enhanced fallback with better HTML-compatible visuals
                visuals['Trait Profile Summary'] = _create_fallback_visualization(person)
                
        except Exception as e:
            print(f"Warning: Could not generate visualizations: {e}")
            # Create enhanced fallback with basic HTML charts
            visuals['Trait Profile Summary'] = _create_fallback_visualization(person)
    
    # For PDF format, explicitly exclude visuals
    if output_format == "pdf":
        visuals = {}
    
    return generate_html_report(
        person=person,
        cluster=cluster,
        narratives=narratives,
        visuals=visuals,
        template_name="comprehensive_report_template.html",
        archetype_profile=archetype_profile
    )

def _process_individual_through_pipeline(person: Any, raw_data: Any) -> Any:
    """
    Process individual data through the complete RaschPy + Scoring Engine pipeline.
    
    Args:
        person: PersonScore object (potentially with incomplete data)
        raw_data: Raw assessment data for this individual
        
    Returns:
        Updated PersonScore object with properly processed data
    """
    try:
        # Import pipeline components
        import sys
        from pathlib import Path
        
        # Add src directory to path
        src_path = Path(__file__).parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        from data.rasch_analysis import RaschAnalyzer
        from scoring.scoring_engine import PsychometricScoringEngine
        
        # Initialize components
        rasch_analyzer = RaschAnalyzer()
        scoring_engine = PsychometricScoringEngine()
        
        # Process individual data through RaschPy
        rasch_results = rasch_analyzer.analyze_person_data(person.person_id, raw_data)
        
        if rasch_results.success and rasch_results.transformed_data is not None:
            # Process through scoring engine
            individual_scores = scoring_engine.calculate_individual_scores(
                person.person_id, 
                rasch_results.transformed_data
            )
            
            # Update person object with processed scores
            if individual_scores:
                # Update overall scores
                person.overall_score = individual_scores.get('overall_score', person.overall_score)
                person.overall_percentile = individual_scores.get('overall_percentile', person.overall_percentile)
                
                # Update construct scores
                construct_scores_dict = individual_scores.get('construct_scores', {})
                for construct_score in person.construct_scores:
                    construct_key = construct_score.construct_id
                    if construct_key in construct_scores_dict:
                        construct_data = construct_scores_dict[construct_key]
                        construct_score.score = construct_data.get('score', construct_score.score)
                        construct_score.percentile = construct_data.get('percentile', construct_score.percentile)
                
                print(f"Successfully processed {person.person_id} through RaschPy pipeline")
        else:
            print(f"RaschPy processing failed for {person.person_id}: {rasch_results.errors}")
        
        return person
        
    except Exception as e:
        print(f"Warning: Could not process individual data through pipeline: {e}")
        # Return original person object if processing fails
        return person

def generate_intelligent_narratives(
    person: Any, 
    cluster: Any = None, 
    archetype_profile: Any = None
) -> Dict[str, str]:
    """
    Generate intelligent, personalized narratives based on assessment results.
    
    Args:
        person: PersonScore object
        cluster: ClusterResult object
        archetype_profile: ArchetypeProfile object
        
    Returns:
        Dictionary of narrative sections
    """
    narratives = {}
    
    # Overall assessment narrative
    overall_score = getattr(person, 'overall_score', 50)
    if overall_score >= 70:
        performance_level = "exceptional"
        performance_desc = "demonstrates strong entrepreneurial capabilities across multiple dimensions"
    elif overall_score >= 60:
        performance_level = "strong"
        performance_desc = "shows solid entrepreneurial potential with several areas of strength"
    elif overall_score >= 50:
        performance_level = "moderate"
        performance_desc = "exhibits developing entrepreneurial traits with opportunities for growth"
    else:
        performance_level = "emerging"
        performance_desc = "is in the early stages of entrepreneurial development"
    
    narratives["Overall Assessment"] = (
        f"Based on this comprehensive psychometric assessment, {person.person_id} "
        f"{performance_desc}. With an overall score of {overall_score:.1f}, this individual "
        f"ranks in the {performance_level} range for entrepreneurial readiness."
    )
    
    # Construct-specific insights
    if hasattr(person, 'construct_scores') and person.construct_scores:
        # Find top 3 strengths
        sorted_constructs = sorted(person.construct_scores, key=lambda x: x.score, reverse=True)
        top_strengths = sorted_constructs[:3]
        
        strengths_text = ", ".join([c.construct_name for c in top_strengths])
        narratives["Key Strengths"] = (
            f"The assessment reveals particular strength in {strengths_text}. "
            f"These capabilities suggest a natural aptitude for {_get_strength_implications(top_strengths)}."
        )
        
        # Development areas (bottom 2-3 scores)
        development_areas = sorted_constructs[-2:]
        if len(development_areas) >= 2:
            dev_text = " and ".join([c.construct_name for c in development_areas])
            narratives["Development Opportunities"] = (
                f"Areas with the greatest potential for growth include {dev_text}. "
                f"Focused development in these areas could significantly enhance overall entrepreneurial effectiveness."
            )
    
    # Archetype-specific narrative
    if cluster and hasattr(cluster, 'archetype_name'):
        narratives["Archetype Insights"] = (
            f"As a {cluster.archetype_name}, {person.person_id} is likely to excel in "
            f"environments that value {_get_archetype_context(cluster.archetype_name)}. "
            f"This profile suggests natural alignment with roles and opportunities that "
            f"leverage these inherent strengths."
        )
    
    # Cluster context
    if cluster and hasattr(cluster, 'size'):
        narratives["Peer Context"] = (
            f"This assessment places {person.person_id} among {cluster.size} individuals "
            f"who share similar entrepreneurial characteristics. This peer group provides "
            f"valuable context for understanding behavioral patterns and potential collaboration opportunities."
        )
    
    return narratives

def _get_strength_implications(top_constructs: List[Any]) -> str:
    """Get implications text based on top construct scores."""
    construct_names = [c.construct_name.lower() for c in top_constructs]
    
    if any('innovation' in name for name in construct_names):
        return "creative problem-solving and breakthrough thinking"
    elif any('leadership' in name for name in construct_names):
        return "team building and organizational development"
    elif any('risk' in name for name in construct_names):
        return "opportunity identification and calculated decision-making"
    elif any('resilience' in name or 'grit' in name for name in construct_names):
        return "persistence through challenges and long-term goal achievement"
    else:
        return "strategic thinking and systematic approach to business challenges"

def _get_archetype_context(archetype_name: str) -> str:
    """Get context description for archetype."""
    archetype_lower = archetype_name.lower()
    
    if 'visionary' in archetype_lower or 'innovator' in archetype_lower:
        return "creative innovation and future-focused thinking"
    elif 'leader' in archetype_lower or 'strategic' in archetype_lower:
        return "team leadership and strategic planning"
    elif 'executor' in archetype_lower or 'resilient' in archetype_lower:
        return "results delivery and systematic execution"
    elif 'collaborator' in archetype_lower or 'adaptive' in archetype_lower:
        return "relationship building and change management"
    elif 'analytical' in archetype_lower or 'problem solver' in archetype_lower:
        return "data-driven analysis and methodical problem-solving"
    else:
        return "balanced approach to entrepreneurial challenges"

def html_to_pdf(html_content: str, output_path: str, 
                css_string: str = None, base_url: str = None) -> bool:
    """
    Convert HTML string to PDF using pdfkit without visualization components.
    
    Args:
        html_content: HTML string
        output_path: Path to save PDF
        css_string: Additional CSS to apply (will be embedded in HTML)
        base_url: Base URL for resolving relative paths (not used in pdfkit)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Add PDF-specific CSS for better text and table rendering
        pdf_css = """
        <style type="text/css">
        /* PDF-specific body styling */
        body {
            font-family: 'Arial', 'DejaVu Sans', sans-serif;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        /* Ensure good page breaks */
        .section {
            page-break-inside: avoid;
            margin-bottom: 30px;
        }
        
        .archetype-section {
            page-break-inside: avoid;
        }
        
        .two-column {
            page-break-inside: avoid;
        }
        
        /* Table styling for PDF */
        table {
            page-break-inside: avoid;
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        
        /* Header and footer adjustments */
        .header {
            margin-bottom: 30px;
        }
        
        .footer {
            margin-top: 30px;
            page-break-before: avoid;
        }
        
        /* Improve readability */
        h1, h2, h3 {
            color: #2c3e50;
            page-break-after: avoid;
        }
        
        h1 {
            font-size: 24px;
            margin-bottom: 20px;
        }
        
        h2 {
            font-size: 18px;
            margin-bottom: 15px;
        }
        
        h3 {
            font-size: 16px;
            margin-bottom: 10px;
        }
        
        p {
            text-align: justify;
            margin-bottom: 10px;
        }
        
        /* Grid layouts for PDF */
        .traits-grid {
            display: block;
        }
        
        .trait-card {
            display: inline-block;
            width: 48%;
            margin: 1%;
            vertical-align: top;
            page-break-inside: avoid;
            border: 1px solid #ddd;
            padding: 10px;
            box-sizing: border-box;
        }
        
        .participant-info {
            display: block;
        }
        
        .info-card {
            display: inline-block;
            width: 23%;
            margin: 1%;
            vertical-align: top;
            border: 1px solid #ddd;
            padding: 10px;
            box-sizing: border-box;
        }
        
        /* Score styling */
        .score {
            font-weight: bold;
            color: #2c3e50;
        }
        
        /* Progress bars for PDF */
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background-color: #3498db;
            transition: none;
        }
        
        /* Hide any leftover chart containers */
        .plotly-graph-div, .chart-container, .visualization {
            display: none !important;
        }
        </style>
        """
        
        # If CSS string is provided, embed it in the HTML
        if css_string:
            # Find the </head> tag and insert CSS before it
            if '</head>' in html_content:
                css_tag = f'<style type="text/css">{css_string}</style>'
                html_content = html_content.replace('</head>', f'{css_tag}</head>')
            else:
                # If no head tag, prepend CSS
                css_tag = f'<style type="text/css">{css_string}</style>'
                html_content = css_tag + html_content
        
        # Add PDF-specific enhancements
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', f'{pdf_css}</head>')
        else:
            html_content = pdf_css + html_content
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate PDF using pdfkit with simplified options (no JavaScript)
        simplified_pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'disable-smart-shrinking': '',
            'print-media-type': '',
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
            'minimum-font-size': 12,
            'zoom': 1.0,
            'disable-javascript': '',  # Explicitly disable JavaScript
            'images': '',
            'enable-internal-links': '',
        }
        
        pdfkit.from_string(
            html_content, 
            output_path, 
            options=simplified_pdf_options,
            configuration=pdfkit_config
        )
        
        return True
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

def generate_batch_reports(
    person_scores: List[Any],
    cluster_results: List[Any] = None,
    output_directory: str = "output/reports",
    format: str = "both"  # "html", "pdf", or "both"
) -> Dict[str, List[str]]:
    """
    Generate reports for multiple persons in batch.
    
    Args:
        person_scores: List of PersonScore objects
        cluster_results: List of ClusterResult objects
        output_directory: Directory to save reports
        format: Output format(s)
        
    Returns:
        Dictionary with lists of generated file paths
    """
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = {"html": [], "pdf": []}
    
    for person in person_scores:
        # Find person's cluster
        person_cluster = None
        if cluster_results:
            for cluster in cluster_results:
                if hasattr(cluster, 'person_ids') and person.person_id in cluster.person_ids:
                    person_cluster = cluster
                    break
        
        # Generate format-specific reports
        if format in ["html", "both"]:
            # Generate HTML report with interactive visualizations
            html_content = generate_comprehensive_report(
                person=person,
                cluster=person_cluster,
                all_person_scores=person_scores,
                output_format="html"
            )
            html_path = output_dir / f"report_{person.person_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            generated_files["html"].append(str(html_path))
        
        # Save PDF if requested
        if format in ["pdf", "both"]:
            # Generate PDF report with static visualizations
            pdf_html_content = generate_comprehensive_report(
                person=person,
                cluster=person_cluster,
                all_person_scores=person_scores,
                output_format="pdf"
            )
            pdf_path = output_dir / f"report_{person.person_id}.pdf"
            if html_to_pdf(pdf_html_content, str(pdf_path)):
                generated_files["pdf"].append(str(pdf_path))
    
    return generated_files

def test_pdfkit_installation() -> bool:
    """Test if pdfkit is properly installed and configured"""
    try:
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { color: #333; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>PDF Generation Test</h1>
                <p>This is a test of the pdfkit installation.</p>
            </div>
        </body>
        </html>
        """
        
        test_path = "test_output.pdf"
        
        # Test PDF generation
        success = html_to_pdf(test_html, test_path)
        
        if success and os.path.exists(test_path):
            os.remove(test_path)  # Clean up
            print("✅ pdfkit installation test successful")
            return True
        else:
            print("❌ pdfkit test failed - no output file created")
            return False
            
    except Exception as e:
        print(f"❌ pdfkit installation test failed: {str(e)}")
        return False

def _create_embedded_bar_chart(person: Any) -> str:
    """Create embedded HTML bar chart for individual traits."""
    try:
        import plotly.graph_objects as go
        
        if not hasattr(person, 'construct_scores') or not person.construct_scores:
            return "<p>No trait data available for visualization.</p>"
        
        constructs = []
        scores = []
        colors = []
        
        for construct in person.construct_scores:
            constructs.append(construct.construct_name)
            score = float(construct.score)
            scores.append(score)
            
            # Color coding based on score
            if score >= 0.7:
                colors.append('rgba(40, 167, 69, 0.8)')  # Green
            elif score >= 0.5:
                colors.append('rgba(255, 193, 7, 0.8)')  # Yellow
            else:
                colors.append('rgba(220, 53, 69, 0.8)')  # Red
        
        fig = go.Figure(data=[
            go.Bar(
                x=constructs,
                y=scores,
                marker=dict(color=colors, line=dict(color='rgba(0,0,0,0.3)', width=1)),
                text=[f'{score:.2f}' for score in scores],
                textposition='auto',
                textfont=dict(size=11, color='white'),
                hovertemplate='<b>%{x}</b><br>Score: %{y:.2f}<extra></extra>'
            )
        ])
        
        # Dynamic range calculation for RaschPy data
        min_score = min(scores) * 0.9  # Add 10% padding below
        max_score = max(scores) * 1.1  # Add 10% padding above
        
        fig.update_layout(
            title=f"Individual Trait Scores - {person.person_id}",
            xaxis_title="Traits",
            yaxis_title="RaschPy Score (Logits)",
            xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
            yaxis=dict(range=[min_score, max_score], tickformat='.2f'),
            height=500,
            margin=dict(l=50, r=50, t=80, b=150),
            plot_bgcolor='rgba(255,255,255,0.9)',
            paper_bgcolor='white',
            showlegend=False
        )
        
        # Add benchmark line at average score
        avg_score = sum(scores) / len(scores)
        fig.add_hline(y=avg_score, line_dash="dash", line_color="gray", 
                     annotation_text=f"Average ({avg_score:.2f})", annotation_position="top right")
        
        return fig.to_html(include_plotlyjs='cdn', div_id=f"bar_chart_{person.person_id}")
        
    except Exception as e:
        return f"<p>Error generating bar chart: {str(e)}</p>"

def _create_strengths_development_chart(person: Any) -> str:
    """Create embedded HTML chart showing strengths vs development areas."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        if not hasattr(person, 'construct_scores') or not person.construct_scores:
            return "<p>No trait data available for comparison.</p>"
        
        # Sort constructs by score
        sorted_constructs = sorted(person.construct_scores, key=lambda x: x.score, reverse=True)
        
        # Get top 5 and bottom 5
        strengths = sorted_constructs[:5]
        development_areas = sorted_constructs[-5:]
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['Top 5 Strengths', 'Key Development Areas'],
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Strengths (horizontal bars)
        fig.add_trace(
            go.Bar(
                y=[c.construct_name for c in strengths],
                x=[c.score for c in strengths],
                orientation='h',
                marker_color='rgba(40, 167, 69, 0.8)',
                text=[f'{c.score:.2f}' for c in strengths],
                textposition='auto',
                name='Strengths',
                hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Development areas (horizontal bars)
        fig.add_trace(
            go.Bar(
                y=[c.construct_name for c in development_areas],
                x=[c.score for c in development_areas],
                orientation='h',
                marker_color='rgba(255, 193, 7, 0.8)',
                text=[f'{c.score:.2f}' for c in development_areas],
                textposition='auto',
                name='Development Areas',
                hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title=f"Strengths vs Development Profile - {person.person_id}",
            showlegend=False,
            height=400,
            margin=dict(l=120, r=50, t=80, b=50)
        )
        
        # Dynamic range calculation for both sides
        all_scores = [c.score for c in strengths] + [c.score for c in development_areas]
        min_score = min(all_scores) * 0.9
        max_score = max(all_scores) * 1.1
        
        # Update x-axes with dynamic range
        fig.update_xaxes(title_text="RaschPy Score (Logits)", range=[min_score, max_score], row=1, col=1)
        fig.update_xaxes(title_text="RaschPy Score (Logits)", range=[min_score, max_score], row=1, col=2)
        
        return fig.to_html(include_plotlyjs='cdn', div_id=f"strengths_dev_{person.person_id}")
        
    except Exception as e:
        return f"<p>Error generating strengths/development chart: {str(e)}</p>"

def _create_fallback_visualization(person: Any) -> str:
    """Create a fallback HTML visualization when Plotly is not available."""
    try:
        if not hasattr(person, 'construct_scores') or not person.construct_scores:
            return f"<p>Overall Score: {getattr(person, 'overall_score', 'N/A'):.3f}</p>"
        
        # Sort constructs by score
        sorted_constructs = sorted(person.construct_scores, key=lambda x: x.score, reverse=True)
        
        html = f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #667eea;">
            <h4 style="color: #2c3e50; margin-bottom: 15px;">📊 Trait Profile Summary</h4>
            <p style="margin-bottom: 15px;"><strong>Overall Score:</strong> {getattr(person, 'overall_score', 'N/A'):.3f}</p>
            
            <div style="margin-bottom: 20px;">
                <h5 style="color: #28a745; margin-bottom: 10px;">🎯 Top 5 Strengths:</h5>
                <ul style="margin-left: 20px;">
        """
        
        for construct in sorted_constructs[:5]:
            html += f"<li><strong>{construct.construct_name}:</strong> {construct.score:.2f}</li>"
        
        html += """
                </ul>
            </div>
            
            <div>
                <h5 style="color: #ffc107; margin-bottom: 10px;">📈 Development Areas:</h5>
                <ul style="margin-left: 20px;">
        """
        
        for construct in sorted_constructs[-3:]:
            html += f"<li><strong>{construct.construct_name}:</strong> {construct.score:.2f}</li>"
        
        html += """
                </ul>
            </div>
            
            <div style="margin-top: 15px; padding: 10px; background: rgba(102, 126, 234, 0.1); border-radius: 5px;">
                <small>💡 <strong>Note:</strong> Enhanced interactive visualizations are available when Plotly dependencies are installed.</small>
            </div>
        </div>
        """
        
        return html
        
    except Exception as e:
        return f"<p>Profile summary unavailable. Overall Score: {getattr(person, 'overall_score', 'N/A')}</p>"

def _create_pdf_compatible_visualization(person: Any) -> str:
    """Create PDF-compatible visualization using CSS and HTML only."""
    try:
        if not hasattr(person, 'construct_scores') or not person.construct_scores:
            return f"<p>Overall Score: {getattr(person, 'overall_score', 'N/A'):.3f}</p>"
        
        # Sort constructs by score
        sorted_constructs = sorted(person.construct_scores, key=lambda x: x.score, reverse=True)
        
        # Create CSS-based radar chart representation
        html = f"""
        <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h4 style="color: #2c3e50; text-align: center; margin-bottom: 25px; font-size: 1.3em;">📊 Entrepreneurial Trait Profile</h4>
            
            <!-- Circular Progress Visualization -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 25px;">
        """
        
        for i, construct in enumerate(sorted_constructs[:8]):  # Top 8 for better layout
            percentage = int(construct.score * 100)
            
            # Color based on score
            if construct.score >= 0.7:
                color = "#28a745"
                bg_color = "rgba(40, 167, 69, 0.1)"
            elif construct.score >= 0.5:
                color = "#ffc107"
                bg_color = "rgba(255, 193, 7, 0.1)"
            else:
                color = "#dc3545"
                bg_color = "rgba(220, 53, 69, 0.1)"
            
            html += f"""
                <div style="text-align: center; padding: 15px; background: {bg_color}; border-radius: 10px; border: 2px solid {color};">
                    <div style="font-size: 2em; font-weight: bold; color: {color}; margin-bottom: 5px;">{construct.score:.2f}</div>
                    <div style="font-size: 0.9em; font-weight: bold; color: #2c3e50; margin-bottom: 8px;">{construct.construct_name}</div>
                    <div style="background: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="background: {color}; height: 8px; width: {percentage}%; border-radius: 4px;"></div>
                    </div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 3px;">{percentage}%</div>
                </div>
            """
        
        html += """
            </div>
            
            <!-- Performance Summary Table -->
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.9em;">
                <thead>
                    <tr style="background: #667eea; color: white;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Trait</th>
                        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Score</th>
                        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Performance</th>
                        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Visual</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for construct in sorted_constructs:
            percentage = int(construct.score * 100)
            
            if construct.score >= 0.7:
                performance = "High"
                perf_color = "#28a745"
                bar_color = "#28a745"
            elif construct.score >= 0.5:
                performance = "Moderate"
                perf_color = "#ffc107"
                bar_color = "#ffc107"
            else:
                performance = "Developing"
                perf_color = "#dc3545"
                bar_color = "#dc3545"
            
            html += f"""
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px; font-weight: bold;">{construct.construct_name}</td>
                    <td style="padding: 10px; text-align: center; font-weight: bold; color: {perf_color};">{construct.score:.2f}</td>
                    <td style="padding: 10px; text-align: center;">
                        <span style="color: {perf_color}; font-weight: bold;">{performance}</span>
                    </td>
                    <td style="padding: 10px; text-align: center;">
                        <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden; margin: 0 10px;">
                            <div style="background: {bar_color}; height: 12px; width: {percentage}%; border-radius: 6px;"></div>
                        </div>
                    </td>
                </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            
            <!-- Summary Statistics -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; text-align: center;">
                    <div style="font-size: 1.5em; font-weight: bold; color: #28a745;">{len([c for c in person.construct_scores if c.score >= 0.7])}</div>
                    <div style="font-size: 0.9em; color: #666;">High Performance</div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; text-align: center;">
                    <div style="font-size: 1.5em; font-weight: bold; color: #ffc107;">{len([c for c in person.construct_scores if 0.5 <= c.score < 0.7])}</div>
                    <div style="font-size: 0.9em; color: #666;">Moderate Performance</div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545; text-align: center;">
                    <div style="font-size: 1.5em; font-weight: bold; color: #dc3545;">{len([c for c in person.construct_scores if c.score < 0.5])}</div>
                    <div style="font-size: 0.9em; color: #666;">Development Areas</div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; text-align: center;">
                    <div style="font-size: 1.5em; font-weight: bold; color: #667eea;">{getattr(person, 'overall_score', 0):.2f}</div>
                    <div style="font-size: 0.9em; color: #666;">Overall Score</div>
                </div>
            </div>
        </div>
        """
        
        return html
        
    except Exception as e:
        return f"<p>PDF visualization unavailable. Overall Score: {getattr(person, 'overall_score', 'N/A')}</p>"

def _create_pdf_strengths_chart(person: Any) -> str:
    """Create PDF-compatible strengths vs development visualization."""
    try:
        if not hasattr(person, 'construct_scores') or not person.construct_scores:
            return "<p>No trait data available for analysis.</p>"
        
        # Sort constructs by score
        sorted_constructs = sorted(person.construct_scores, key=lambda x: x.score, reverse=True)
        
        # Get top 5 and bottom 5
        strengths = sorted_constructs[:5]
        development_areas = sorted_constructs[-5:]
        
        html = f"""
        <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h4 style="color: #2c3e50; text-align: center; margin-bottom: 25px; font-size: 1.3em;">⚖️ Strengths vs Development Analysis</h4>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                <!-- Strengths Column -->
                <div style="background: rgba(40, 167, 69, 0.05); padding: 20px; border-radius: 10px; border: 2px solid #28a745;">
                    <h5 style="color: #28a745; text-align: center; margin-bottom: 20px; font-size: 1.2em;">🎯 Top 5 Strengths</h5>
        """
        
        for i, construct in enumerate(strengths):
            percentage = int(construct.score * 100)
            html += f"""
                <div style="margin-bottom: 15px; padding: 12px; background: white; border-radius: 8px; border-left: 4px solid #28a745;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: bold; color: #2c3e50;">{i+1}. {construct.construct_name}</span>
                        <span style="font-weight: bold; color: #28a745; font-size: 1.1em;">{construct.score:.2f}</span>
                    </div>
                    <div style="background: #e9ecef; height: 10px; border-radius: 5px; overflow: hidden;">
                        <div style="background: #28a745; height: 10px; width: {percentage}%; border-radius: 5px;"></div>
                    </div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 3px; text-align: right;">{percentage}%</div>
                </div>
            """
        
        html += """
                </div>
                
                <!-- Development Areas Column -->
                <div style="background: rgba(255, 193, 7, 0.05); padding: 20px; border-radius: 10px; border: 2px solid #ffc107;">
                    <h5 style="color: #fd7e14; text-align: center; margin-bottom: 20px; font-size: 1.2em;">📈 Key Development Areas</h5>
        """
        
        for i, construct in enumerate(development_areas):
            percentage = int(construct.score * 100)
            html += f"""
                <div style="margin-bottom: 15px; padding: 12px; background: white; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: bold; color: #2c3e50;">{i+1}. {construct.construct_name}</span>
                        <span style="font-weight: bold; color: #fd7e14; font-size: 1.1em;">{construct.score:.2f}</span>
                    </div>
                    <div style="background: #e9ecef; height: 10px; border-radius: 5px; overflow: hidden;">
                        <div style="background: #ffc107; height: 10px; width: {percentage}%; border-radius: 5px;"></div>
                    </div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 3px; text-align: right;">{percentage}%</div>
                </div>
            """
        
        html += """
                </div>
            </div>
            
            <!-- Action Items -->
            <div style="margin-top: 25px; padding: 20px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #667eea;">
                <h5 style="color: #667eea; margin-bottom: 15px;">💡 Recommended Action Items</h5>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h6 style="color: #28a745; margin-bottom: 10px;">Leverage Strengths:</h6>
                        <ul style="margin-left: 20px; color: #2c3e50;">
                            <li>Build on high accountability and resilience</li>
                            <li>Take leadership roles that utilize these traits</li>
                            <li>Mentor others in your strong areas</li>
                        </ul>
                    </div>
                    <div>
                        <h6 style="color: #fd7e14; margin-bottom: 10px;">Develop Areas:</h6>
                        <ul style="margin-left: 20px; color: #2c3e50;">
                            <li>Practice calculated risk-taking in small steps</li>
                            <li>Seek conflict resolution training</li>
                            <li>Join creative problem-solving workshops</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """
        
        return html
        
    except Exception as e:
        return f"<p>Strengths analysis unavailable: {str(e)}</p>"

if __name__ == "__main__":
    # Test the installation
    print("Testing pdfkit installation...")
    test_pdfkit_installation()