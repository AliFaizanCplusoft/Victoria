"""
LLM-Powered HTML Report Generator
Generates personalized HTML reports using OpenAI API with Vertria branding and visualizations
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import base64
import io
import pandas as pd

from victoria.core.models import PersonTraitProfile, ReportData
from victoria.config.settings import app_config, brand_config, archetype_config
from victoria.utils.visualization_helpers import VisualizationHelper

logger = logging.getLogger(__name__)

class LLMReportGenerator:
    """
    Generates comprehensive HTML reports using LLM for personalized insights
    Includes Vertria branding and interactive visualizations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.viz_helper = VisualizationHelper()
        
        # OpenAI configuration
        self.openai_api_key = app_config.OPENAI_API_KEY
        self.model = app_config.OPENAI_MODEL
        self.max_tokens = app_config.OPENAI_MAX_TOKENS
        self.temperature = app_config.OPENAI_TEMPERATURE
        
        if not self.openai_api_key:
            self.logger.warning("OpenAI API key not configured. LLM features disabled.")
            self.llm_enabled = False
        else:
            self.llm_enabled = True
    
    def generate_comprehensive_report(self, profile: PersonTraitProfile, 
                                    report_id: str = None) -> str:
        """
        Generate a comprehensive HTML report for an individual profile
        """
        self.logger.info(f"Generating comprehensive report for {profile.person_id}")
        
        # Prepare report data
        report_data = ReportData(
            profile=profile,
            metadata={
                'report_id': report_id or f"report_{profile.person_id}",
                'generation_timestamp': pd.Timestamp.now().isoformat(),
                'report_type': 'comprehensive_individual'
            }
        )
        
        # Generate visualizations
        visualizations = self._create_visualizations(profile)
        report_data.visualizations = visualizations
        
        # Generate LLM content
        llm_content = self._generate_llm_insights(profile) if self.llm_enabled else self._generate_fallback_content(profile)
        
        # Create HTML report
        html_content = self._generate_html_report(report_data, llm_content)
        
        return html_content
    
    def _create_visualizations(self, profile: PersonTraitProfile) -> Dict[str, str]:
        """Create visualizations and return them as base64 encoded images/HTML"""
        visualizations = {}
        
        try:
            # 1. Trait Radar Chart
            trait_data = {trait.trait_name: trait.percentile for trait in profile.traits}
            radar_fig = self.viz_helper.create_trait_radar_chart(
                trait_data, 
                title=f"Trait Profile - {profile.person_id}"
            )
            visualizations['radar_chart'] = radar_fig.to_html(include_plotlyjs='cdn')
            
            # 2. Archetype Distribution (if applicable)
            if profile.primary_archetype and profile.secondary_archetypes:
                archetype_data = {profile.primary_archetype.archetype.value: profile.primary_archetype.score}
                for arch in profile.secondary_archetypes:
                    archetype_data[arch.archetype.value] = arch.score
                
                arch_fig = self.viz_helper.create_archetype_distribution(archetype_data)
                visualizations['archetype_chart'] = arch_fig.to_html(include_plotlyjs='cdn')
            
            # 3. Trait Level Bars (Custom visualization)
            trait_levels_html = self._create_trait_level_bars(profile)
            visualizations['trait_levels'] = trait_levels_html
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")
            visualizations['error'] = f"Visualization generation failed: {e}"
        
        return visualizations
    
    def _create_trait_level_bars(self, profile: PersonTraitProfile) -> str:
        """Create custom trait level bar visualization"""
        html = '<div class="trait-bars">'
        
        for trait in profile.traits:
            level_color = self._get_level_color(trait.percentile)
            width_percent = trait.percentile
            
            html += f'''
            <div class="trait-bar-container">
                <div class="trait-label">{trait.trait_name}</div>
                <div class="trait-bar-track">
                    <div class="trait-bar-fill" style="width: {width_percent}%; background-color: {level_color};">
                        <span class="trait-score">{trait.percentile:.0f}%</span>
                    </div>
                </div>
                <div class="trait-level">{trait.level.value.title() if trait.level else 'N/A'}</div>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _get_level_color(self, percentile: float) -> str:
        """Get color based on trait percentile"""
        if percentile >= 75:
            return brand_config.COLORS['accent_yellow']
        elif percentile >= 50:
            return brand_config.COLORS['primary_burgundy']
        elif percentile >= 25:
            return brand_config.COLORS['dark_blue']
        else:
            return brand_config.COLORS['deep_burgundy']
    
    def _generate_llm_insights(self, profile: PersonTraitProfile) -> Dict[str, str]:
        """Generate personalized insights using OpenAI API"""
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            # Prepare profile data for LLM
            profile_summary = self._prepare_profile_for_llm(profile)
            
            insights = {}
            
            # Generate Executive Summary
            executive_prompt = f"""
            Based on this psychometric profile, write a professional executive summary (2-3 paragraphs) for an entrepreneurial assessment report:
            
            {profile_summary}
            
            Focus on:
            - Key strengths and characteristics
            - Primary entrepreneurial archetype alignment
            - Overall leadership potential
            
            Write in a confident, professional tone suitable for a business context.
            """
            
            insights['executive_summary'] = self._call_openai_api(executive_prompt)
            
            # Generate Detailed Analysis
            analysis_prompt = f"""
            Based on this psychometric profile, provide a detailed trait analysis (3-4 paragraphs):
            
            {profile_summary}
            
            For each major trait strength:
            - Explain what this means in an entrepreneurial context
            - Provide specific examples of how this manifests
            - Connect to business success factors
            
            Write in an analytical but accessible tone.
            """
            
            insights['detailed_analysis'] = self._call_openai_api(analysis_prompt)
            
            # Generate Recommendations
            recommendations_prompt = f"""
            Based on this psychometric profile, provide 5-7 specific, actionable recommendations:
            
            {profile_summary}
            
            Categories:
            - Leadership development opportunities
            - Skill-building areas based on lower traits
            - Career path suggestions
            - Team collaboration strategies
            
            Format as a bulleted list with specific, actionable advice.
            """
            
            insights['recommendations'] = self._call_openai_api(recommendations_prompt)
            
            # Generate Growth Areas
            growth_prompt = f"""
            Based on this psychometric profile, identify key growth opportunities (2-3 paragraphs):
            
            {profile_summary}
            
            Focus on:
            - Traits that could be developed further
            - Potential blind spots or challenges
            - Strategies for continuous improvement
            
            Frame positively as growth opportunities, not weaknesses.
            """
            
            insights['growth_opportunities'] = self._call_openai_api(growth_prompt)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating LLM insights: {e}")
            return self._generate_fallback_content(profile)
    
    def _prepare_profile_for_llm(self, profile: PersonTraitProfile) -> str:
        """Prepare profile data in a format suitable for LLM processing"""
        summary = f"Person ID: {profile.person_id}\\n"
        summary += f"Overall Score: {profile.overall_score:.3f}\\n"
        summary += f"Assessment Completion: {profile.completion_rate:.1%}\\n\\n"
        
        summary += "TRAIT SCORES:\\n"
        for trait in profile.traits:
            summary += f"- {trait.trait_name}: {trait.score:.3f} (Percentile: {trait.percentile:.1f}%, Level: {trait.level.value if trait.level else 'N/A'})\\n"
        
        if profile.primary_archetype:
            summary += f"\\nPRIMARY ARCHETYPE:\\n"
            summary += f"- Type: {profile.primary_archetype.archetype.value.replace('_', ' ').title()}\\n"
            summary += f"- Match Score: {profile.primary_archetype.score:.3f}\\n"
            summary += f"- Confidence: {profile.primary_archetype.confidence:.3f}\\n"
            summary += f"- Description: {profile.primary_archetype.description}\\n"
            summary += f"- Key Characteristics: {', '.join(profile.primary_archetype.characteristics)}\\n"
        
        if profile.secondary_archetypes:
            summary += f"\\nSECONDARY ARCHETYPES:\\n"
            for arch in profile.secondary_archetypes:
                summary += f"- {arch.archetype.value.replace('_', ' ').title()}: {arch.score:.3f}\\n"
        
        return summary
    
    def _get_verrita_unified_css(self) -> str:
        """Generate CSS styles matching the unified report"""
        return """
        :root {
            --vertria-burgundy: #570F27;
            --vertria-dark-blue: #151A4A;
            --vertria-yellow: #FFDC58;
            --vertria-deep-burgundy: #240610;
            --vertria-light-burgundy: #8B2545;
            --vertria-accent-blue: #2E4A7A;
            --vertria-background: #FEFEFE;
            --vertria-light-gray: #F8F9FA;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: var(--vertria-dark-blue); background-color: var(--vertria-background); font-size: 16px; }
        h1, h2, h3 { font-family: 'Playfair Display', Georgia, serif; font-weight: 600; color: var(--vertria-burgundy); margin-bottom: 1rem; }
        .report-container { max-width: 1000px; margin: 0 auto; background: white; box-shadow: 0 10px 40px rgba(87, 15, 39, 0.1); overflow: hidden; }
        .report-header { background: linear-gradient(135deg, var(--vertria-burgundy) 0%, var(--vertria-deep-burgundy) 100%); color: white; padding: 3rem 2rem; text-align: center; position: relative; }
        .company-logo { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: var(--vertria-yellow); margin-bottom: 0.5rem; }
        .hero-quote { font-style: italic; color: #FFE888; margin-top: 0.75rem; }
        .intro-line { margin-top: 0.5rem; color: #FFE888; }
        .report-title { color: white; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .person-name { font-size: 1.3rem; font-weight: 500; color: var(--vertria-yellow); margin-bottom: 0.5rem; }
        .report-date { font-size: 0.95rem; opacity: 0.9; }
        .report-content { padding: 2.5rem; }
        .section { margin-bottom: 3rem; }
        .executive-summary { background: linear-gradient(135deg, var(--vertria-light-gray) 0%, #F0F2F5 100%); padding: 2rem; border-radius: 12px; border-left: 6px solid var(--vertria-burgundy); }
        .primary-archetype { background: linear-gradient(135deg, var(--vertria-burgundy) 0%, var(--vertria-light-burgundy) 100%); color: white; padding: 2.5rem; border-radius: 15px; text-align: center; margin-bottom: 2.5rem; }
        .archetype-name { font-size: 2.2rem; font-weight: 700; color: var(--vertria-yellow); margin-bottom: 0.5rem; }
        .archetype-match { font-size: 3.0rem; font-weight: 700; color: white; margin: 1rem 0; }
        .archetype-description { font-size: 1.1rem; opacity: 0.95; max-width: 600px; margin: 0 auto; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
        .metric-card { background: white; padding: 1.8rem; border-radius: 12px; text-align: center; border: 2px solid var(--vertria-light-gray); box-shadow: 0 4px 15px rgba(87, 15, 39, 0.05); }
        .metric-icon { font-size: 2.5rem; margin-bottom: 1rem; color: var(--vertria-burgundy); }
        .metric-value { font-size: 1.8rem; font-weight: 700; color: var(--vertria-burgundy); }
        .trait-item { display: flex; align-items: center; padding: 1rem; margin-bottom: 1rem; background: var(--vertria-light-gray); border-radius: 8px; border-left: 4px solid var(--vertria-burgundy); }
        .trait-name { flex: 1; font-weight: 500; }
        .trait-score { font-weight: 600; color: var(--vertria-burgundy); margin-right: 1rem; min-width: 60px; }
        .trait-bar-container { flex: 2; height: 8px; background: #E5E7EB; border-radius: 4px; overflow: hidden; margin-right: 1rem; }
        .trait-bar { height: 100%; border-radius: 4px; }
        .trait-bar.low { background: linear-gradient(90deg, #b91c1c, #ef4444); }
        .trait-bar.med { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
        .trait-bar.high { background: linear-gradient(90deg, #15803d, #22c55e); }
        .chart-section { margin-bottom: 2.5rem; }
        .chart-container { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(87, 15, 39, 0.05); margin-bottom: 2rem; }
        .growth-recommendations { background: linear-gradient(135deg, #FFF9E6 0%, #FFF4CC 100%); padding: 2rem; border-radius: 12px; border-left: 6px solid var(--vertria-yellow); }
        .metric-label { font-size: 0.9rem; color: var(--vertria-dark-blue); opacity: 0.8; margin-top: 0.5rem; }
        """
    
    def _generate_trait_bars(self, traits) -> str:
        """Generate HTML for trait bars in unified style"""
        trait_html = ""
        for trait in traits:
            # Convert percentile to score for display
            score = trait.percentile
            bar_width = min(score, 100)
            
            # Determine bar color based on score
            if score >= 70:
                bar_class = "high"
            elif score >= 40:
                bar_class = "med"
            else:
                bar_class = "low"
            
            trait_html += f"""
            <div class="trait-item">
                <div class="trait-name">{trait.trait_name}</div>
                <div class="trait-score">{score:.0f}%</div>
                <div class="trait-bar-container">
                    <div class="trait-bar {bar_class}" style="width: {bar_width}%;"></div>
                </div>
            </div>
            """
        
        return trait_html
    
    def _create_radar_visualization(self, traits) -> str:
        """Create radar chart visualization using the visualization engine"""
        try:
            # Create trait data dictionary for radar chart
            trait_data = {trait.trait_name: trait.percentile for trait in traits}
            
            # Use visualization helper to create radar chart
            fig = self.viz_helper.create_trait_radar_chart(trait_data, "Trait Profile")
            
            # Convert to HTML
            radar_html = fig.to_html(
                include_plotlyjs='inline',
                div_id='radar-chart',
                config={'displayModeBar': False}
            )
            
            return radar_html
            
        except Exception as e:
            self.logger.error(f"Error creating radar visualization: {e}")
            return f"<p>Radar chart visualization unavailable: {str(e)}</p>"
    
    def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API with error handling"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional psychometric assessment expert and executive coach specializing in entrepreneurial leadership development."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {e}")
            return f"Unable to generate personalized insights. Please check API configuration. Error: {str(e)}"
    
    def _generate_fallback_content(self, profile: PersonTraitProfile) -> Dict[str, str]:
        """Generate fallback content when LLM is not available"""
        content = {}
        
        # Fallback executive summary
        content['executive_summary'] = f"""
        This comprehensive psychometric assessment reveals a unique entrepreneurial profile for {profile.person_id}. 
        With an overall assessment score of {profile.overall_score:.2f} and {profile.completion_rate:.1%} completion rate, 
        this analysis provides valuable insights into leadership potential and entrepreneurial capabilities.
        
        {f"The primary entrepreneurial archetype identified is {profile.primary_archetype.archetype.value.replace('_', ' ').title()}, " + 
         f"indicating strengths in {', '.join(profile.primary_archetype.matching_traits[:3])}." if profile.primary_archetype else 
         "The profile demonstrates a balanced mix of entrepreneurial traits."}
        """
        
        # Fallback detailed analysis
        strong_traits = [t for t in profile.traits if t.percentile > 70]
        content['detailed_analysis'] = f"""
        The trait analysis reveals several key strengths:
        {' '.join([f"{trait.trait_name} shows excellent development at the {trait.percentile:.0f} percentile." for trait in strong_traits[:3]])}
        
        These characteristics suggest strong potential for entrepreneurial success and leadership effectiveness.
        The combination of these traits creates a foundation for business development and team leadership.
        """
        
        # Fallback recommendations
        recommendations = [
            "Leverage your strongest traits in leadership roles and strategic decision-making",
            "Focus on developing areas with lower scores through targeted skill-building",
            "Consider entrepreneurial opportunities that align with your archetype strengths",
            "Build a diverse team that complements your trait profile",
            "Engage in continuous learning and professional development"
        ]
        
        if profile.growth_areas:
            recommendations.extend([f"Work on developing: {area}" for area in profile.growth_areas[:2]])
        
        content['recommendations'] = "\\n".join([f"• {rec}" for rec in recommendations])
        
        # Fallback growth opportunities
        content['growth_opportunities'] = f"""
        Key growth opportunities include developing traits that scored below the 50th percentile, 
        while continuing to leverage existing strengths. Focus on building complementary skills 
        that support your primary archetype while addressing any potential blind spots in your leadership approach.
        """
        
        return content
    
    def _generate_html_report(self, report_data: ReportData, llm_content: Dict[str, str]) -> str:
        """Generate the complete HTML report matching Verrita unified style"""
        profile = report_data.profile
        visualizations = report_data.visualizations
        
        # Generate trait bars for the unified style
        trait_bars = self._generate_trait_bars(profile.traits)
        
        # Get primary archetype info
        primary_archetype = profile.primary_archetype
        archetype_name = primary_archetype.archetype.value.replace('_', ' ').title() if primary_archetype else "Unknown"
        archetype_match = f"{primary_archetype.score * 100:.1f}" if primary_archetype else "0.0"
        
        # Generate visualization
        radar_chart_html = self._create_radar_visualization(profile.traits)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Entrepreneurial Assessment - {profile.person_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        {self._get_verrita_unified_css()}
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="report-container">
        <!-- Header -->
        <div class="report-header">
            <div class="company-logo">VERRITA</div>
            
            <h1 class="report-title">Unified Entrepreneurial Assessment</h1>
            
            <div class="intro-line">We're excited to help you discover your entrepreneurial strengths and build a focused path forward.</div>
            
            <div class="hero-quote">"Strategy turns ambition into a roadmap and risks into calculated bets." — Verrita</div>
            
            <div class="person-name">{profile.person_id}</div>
            <div class="report-date">Generated on {pd.Timestamp.now().strftime('%B %d, %Y')}</div>
        </div>
        
        <div class="report-content">
            <!-- Executive Summary -->
            <div class="section">
                <div class="executive-summary">
                    <h3>Executive Summary</h3>
                    <p>{llm_content.get('executive_summary', 'Executive summary not available.')}</p>
                </div>
            </div>

            <!-- Primary Archetype -->
            <div class="section">
                <div class="primary-archetype">
                    <div class="archetype-name">{archetype_name}</div>
                    <div class="archetype-match">{archetype_match}%</div>
                    <div class="archetype-description"></div>
                </div>
            </div>

            <!-- Assessment Metrics -->
            <div class="section">
                <h2>Assessment Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-icon">🎯</div>
                        <div class="metric-value">{profile.overall_score:.2f}</div>
                        <div class="metric-label">Overall Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">✅</div>
                        <div class="metric-value">{profile.completion_rate:.1%}</div>
                        <div class="metric-label">Completion Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🔗</div>
                        <div class="metric-value">{len(profile.traits)}</div>
                        <div class="metric-label">Traits Analyzed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🏆</div>
                        <div class="metric-value">{archetype_match}%</div>
                        <div class="metric-label">Archetype Match</div>
                    </div>
                </div>
            </div>

            <!-- Trait Analysis -->
            <div class="section">
                <h2>Trait Analysis</h2>
                {trait_bars}
            </div>

            <!-- Radar Chart Visualization -->
            <div class="section">
                <h2>Trait Profile Visualization</h2>
                <div class="chart-container">
                    {radar_chart_html}
                </div>
            </div>

            <!-- Recommendations -->
            <div class="section">
                <div class="growth-recommendations">
                    <h3>Growth Recommendations</h3>
                    <p>{llm_content.get('recommendations', 'Recommendations not available.')}</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
            <div class="header-content">
                <h1 class="report-title">{report_data.report_title}</h1>
                <div class="person-info">
                    <h2>Individual Assessment Report</h2>
                    <p class="person-id">Assessment ID: {profile.person_id}</p>
                </div>
            </div>
            <div class="vertria-logo">
                <h3 style="color: white; margin: 0;">VERTRIA</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9em;">Entrepreneurial Assessment</p>
            </div>
        </header>

        <!-- Executive Summary -->
        <section class="section">
            <h2 class="section-title">Executive Summary</h2>
            <div class="content-box">
                <p>{llm_content.get('executive_summary', 'Executive summary not available.')}</p>
            </div>
        </section>

        <!-- Key Metrics -->
        <section class="section">
            <h2 class="section-title">Assessment Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>Overall Score</h3>
                    <div class="metric-value">{profile.overall_score:.2f}</div>
                </div>
                <div class="metric-card">
                    <h3>Completion Rate</h3>
                    <div class="metric-value">{profile.completion_rate:.1%}</div>
                </div>
                <div class="metric-card">
                    <h3>Traits Analyzed</h3>
                    <div class="metric-value">{len(profile.traits)}</div>
                </div>
                {f'''
                <div class="metric-card archetype-card">
                    <h3>Primary Archetype</h3>
                    <div class="archetype-name">{profile.primary_archetype.archetype.value.replace('_', ' ').title()}</div>
                    <div class="archetype-confidence">Confidence: {profile.primary_archetype.confidence:.1%}</div>
                </div>
                ''' if profile.primary_archetype else ''}
            </div>
        </section>

        <!-- Trait Profile Visualization -->
        <section class="section">
            <h2 class="section-title">Trait Profile</h2>
            <div class="visualization-container">
                {visualizations.get('radar_chart', '<p>Radar chart not available</p>')}
            </div>
        </section>

        <!-- Trait Details -->
        <section class="section">
            <h2 class="section-title">Detailed Trait Analysis</h2>
            <div class="content-box">
                <p>{llm_content.get('detailed_analysis', 'Detailed analysis not available.')}</p>
            </div>
            {visualizations.get('trait_levels', '')}
        </section>

        <!-- Archetype Analysis -->
        {f'''
        <section class="section">
            <h2 class="section-title">Entrepreneurial Archetype</h2>
            <div class="archetype-analysis">
                <div class="archetype-main">
                    <h3>{profile.primary_archetype.archetype.value.replace('_', ' ').title()}</h3>
                    <p class="archetype-description">{profile.primary_archetype.description}</p>
                    <div class="archetype-traits">
                        <h4>Core Strengths:</h4>
                        <ul>
                            {' '.join([f'<li>{trait}</li>' for trait in profile.primary_archetype.matching_traits])}
                        </ul>
                    </div>
                    <div class="archetype-characteristics">
                        <h4>Key Characteristics:</h4>
                        <ul>
                            {' '.join([f'<li>{char}</li>' for char in profile.primary_archetype.characteristics])}
                        </ul>
                    </div>
                </div>
                {visualizations.get('archetype_chart', '') if len(profile.secondary_archetypes) > 0 else ''}
            </div>
        </section>
        ''' if profile.primary_archetype else ''}

        <!-- Recommendations -->
        <section class="section">
            <h2 class="section-title">Personalized Recommendations</h2>
            <div class="content-box">
                <div class="recommendations-text">
                    {llm_content.get('recommendations', 'Recommendations not available.').replace('\\n', '<br>')}
                </div>
            </div>
        </section>

        <!-- Growth Opportunities -->
        <section class="section">
            <h2 class="section-title">Growth Opportunities</h2>
            <div class="content-box">
                <p>{llm_content.get('growth_opportunities', 'Growth opportunities analysis not available.')}</p>
            </div>
        </section>

        <!-- Footer -->
        <footer class="report-footer">
            <div class="footer-content">
                <p>&copy; 2024 Vertria - Entrepreneurial Assessment Platform</p>
                <p>Generated on {pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        </footer>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _get_css_styles(self) -> str:
        """Get comprehensive CSS styles with Vertria branding"""
        return f"""
        /* Vertria Branded Report Styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: {brand_config.FONTS['body']};
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }}

        .report-container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        /* Header Styles */
        .report-header {{
            background: linear-gradient(135deg, {brand_config.COLORS['primary_burgundy']} 0%, {brand_config.COLORS['deep_burgundy']} 100%);
            color: white;
            padding: 3rem 2rem;
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}

        .header-content {{
            flex: 1;
        }}

        .report-title {{
            font-family: {brand_config.FONTS['header']};
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .person-info h2 {{
            font-size: 1.3rem;
            color: {brand_config.COLORS['accent_yellow']};
            margin-bottom: 0.5rem;
        }}

        .person-id {{
            font-size: 1rem;
            opacity: 0.9;
        }}

        .vertria-logo {{
            text-align: right;
            padding: 1rem;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
        }}

        /* Section Styles */
        .section {{
            padding: 2rem;
            border-bottom: 1px solid #eee;
        }}

        .section:last-of-type {{
            border-bottom: none;
        }}

        .section-title {{
            font-family: {brand_config.FONTS['header']};
            font-size: 1.8rem;
            color: {brand_config.COLORS['primary_burgundy']};
            margin-bottom: 1.5rem;
            border-left: 4px solid {brand_config.COLORS['accent_yellow']};
            padding-left: 1rem;
        }}

        .content-box {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }}

        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background: white;
            border: 2px solid {brand_config.COLORS['light_gray']};
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .metric-card h3 {{
            color: {brand_config.COLORS['dark_blue']};
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: {brand_config.COLORS['primary_burgundy']};
        }}

        .archetype-card {{
            border-color: {brand_config.COLORS['accent_yellow']};
            background: linear-gradient(45deg, #fff 0%, #fffacd 100%);
        }}

        .archetype-name {{
            font-size: 1.2rem;
            font-weight: bold;
            color: {brand_config.COLORS['primary_burgundy']};
            margin-bottom: 0.5rem;
        }}

        .archetype-confidence {{
            font-size: 0.9rem;
            color: {brand_config.COLORS['dark_blue']};
        }}

        /* Trait Bars */
        .trait-bars {{
            margin-top: 1rem;
        }}

        .trait-bar-container {{
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            gap: 1rem;
        }}

        .trait-label {{
            flex: 0 0 200px;
            font-weight: 600;
            color: {brand_config.COLORS['dark_blue']};
        }}

        .trait-bar-track {{
            flex: 1;
            height: 25px;
            background: #e9ecef;
            border-radius: 12px;
            position: relative;
            overflow: hidden;
        }}

        .trait-bar-fill {{
            height: 100%;
            border-radius: 12px;
            position: relative;
            transition: width 0.8s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 8px;
        }}

        .trait-score {{
            color: white;
            font-weight: bold;
            font-size: 0.8rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }}

        .trait-level {{
            flex: 0 0 80px;
            text-align: center;
            font-weight: 600;
            color: {brand_config.COLORS['primary_burgundy']};
            font-size: 0.85rem;
        }}

        /* Archetype Analysis */
        .archetype-analysis {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-top: 1rem;
        }}

        .archetype-main h3 {{
            color: {brand_config.COLORS['primary_burgundy']};
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }}

        .archetype-description {{
            font-style: italic;
            margin-bottom: 1.5rem;
            color: #555;
        }}

        .archetype-traits, .archetype-characteristics {{
            margin-bottom: 1rem;
        }}

        .archetype-traits h4, .archetype-characteristics h4 {{
            color: {brand_config.COLORS['dark_blue']};
            margin-bottom: 0.5rem;
        }}

        .archetype-traits ul, .archetype-characteristics ul {{
            list-style: none;
            padding-left: 0;
        }}

        .archetype-traits li, .archetype-characteristics li {{
            background: {brand_config.COLORS['light_gray']};
            padding: 0.5rem;
            margin-bottom: 0.3rem;
            border-radius: 4px;
            border-left: 3px solid {brand_config.COLORS['accent_yellow']};
        }}

        /* Visualization Container */
        .visualization-container {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        /* Recommendations */
        .recommendations-text {{
            line-height: 1.8;
        }}

        .recommendations-text br {{
            margin: 0.5rem 0;
        }}

        /* Footer */
        .report-footer {{
            background: {brand_config.COLORS['dark_blue']};
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        .footer-content p {{
            margin-bottom: 0.5rem;
        }}

        /* Print Styles */
        @media print {{
            .report-container {{
                box-shadow: none;
            }}
            
            .section {{
                break-inside: avoid;
            }}
        }}
        """
    
    def save_report(self, html_content: str, filename: str, output_dir: str = "output/reports") -> str:
        """Save HTML report to file"""
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save HTML file
            file_path = output_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Report saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            raise