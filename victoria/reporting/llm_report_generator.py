"""
LLM-Powered HTML Report Generator - Clean Version
Generates individual reports matching the unified Verrita style
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
        
        # Generate LLM content
        if self.llm_enabled:
            llm_content = self._generate_llm_content(profile)
        else:
            llm_content = self._generate_fallback_content(profile)
        
        # Create visualizations
        visualizations = self._create_visualizations(profile)
        report_data.visualizations = visualizations
        
        # Generate HTML report
        html_content = self._generate_unified_html_report(profile, llm_content)
        
        self.logger.info(f"Report generated successfully for {profile.person_id}")
        return html_content
    
    def _generate_llm_content(self, profile: PersonTraitProfile) -> Dict[str, str]:
        """Generate LLM-powered content for the report"""
        content = {}
        
        # Generate executive summary
        summary_prompt = self._create_executive_summary_prompt(profile)
        content['executive_summary'] = self._call_openai_api(summary_prompt)
        
        # Generate recommendations
        recommendations_prompt = self._create_recommendations_prompt(profile)
        content['recommendations'] = self._call_openai_api(recommendations_prompt)
        
        return content
    
    def _create_executive_summary_prompt(self, profile: PersonTraitProfile) -> str:
        """Create prompt for executive summary"""
        primary_archetype = profile.primary_archetype
        archetype_name = primary_archetype.archetype.value.replace('_', ' ').title() if primary_archetype else "Unknown"
        
        trait_summary = "\\n".join([
            f"- {trait.trait_name}: {trait.percentile:.0f}th percentile"
            for trait in profile.traits
        ])
        
        return f"""
        Create an executive summary for an entrepreneurial assessment report for person {profile.person_id}.
        
        Profile Details:
        - Overall Score: {profile.overall_score:.2f}
        - Completion Rate: {profile.completion_rate:.1%}
        - Primary Archetype: {archetype_name}
        - Archetype Match: {primary_archetype.score * 100:.1f}% if primary_archetype else 0%
        
        Trait Profile:
        {trait_summary}
        
        Write a professional, encouraging executive summary that:
        1. Highlights their primary archetype and what it means
        2. Mentions their strongest traits (above 70th percentile)
        3. Emphasizes their entrepreneurial potential
        4. Uses a confident, empowering tone consistent with Verrita's brand
        
        Keep it 2-3 paragraphs, professional yet inspiring.
        """
    
    def _create_recommendations_prompt(self, profile: PersonTraitProfile) -> str:
        """Create prompt for growth recommendations"""
        
        strong_traits = [t for t in profile.traits if t.percentile > 70]
        growth_traits = [t for t in profile.traits if t.percentile < 50]
        
        return f"""
        Create personalized growth recommendations for this entrepreneurial profile:
        
        Strong Areas (leverage these):
        {chr(10).join([f'- {t.trait_name}: {t.percentile:.0f}%' for t in strong_traits[:3]])}
        
        Growth Areas (develop these):
        {chr(10).join([f'- {t.trait_name}: {t.percentile:.0f}%' for t in growth_traits[:3]])}
        
        Primary Archetype: {profile.primary_archetype.archetype.value.replace('_', ' ').title() if profile.primary_archetype else 'Unknown'}
        
        Provide 3-4 specific, actionable recommendations that:
        1. Build on their strengths
        2. Address growth areas
        3. Align with their archetype
        4. Are practical and achievable
        
        Use bullet points and keep it encouraging and actionable.
        """
    
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
        strong_traits = [t for t in profile.traits if t.percentile > 70]
        
        content['executive_summary'] = f"""
        This comprehensive psychometric assessment reveals a unique entrepreneurial profile for {profile.person_id}. 
        With an overall assessment score of {profile.overall_score:.2f} and {profile.completion_rate:.1%} completion rate, 
        this analysis provides valuable insights into leadership potential and entrepreneurial capabilities.
        
        Your strongest traits include {', '.join([t.trait_name for t in strong_traits[:3]])}, 
        positioning you well for entrepreneurial success and leadership effectiveness.
        """
        
        # Fallback recommendations
        recommendations = [
            "Leverage your strongest traits in leadership roles and strategic decision-making",
            "Focus on developing areas with lower scores through targeted skill-building",
            "Consider entrepreneurial opportunities that align with your archetype strengths",
            "Build a diverse team that complements your trait profile"
        ]
        
        content['recommendations'] = "\\n".join([f"• {rec}" for rec in recommendations])
        
        return content
    
    def _create_visualizations(self, profile: PersonTraitProfile) -> Dict[str, str]:
        """Create visualizations for the report"""
        visualizations = {}
        
        try:
            # Create trait data dictionary for radar chart
            trait_data = {trait.trait_name: trait.percentile for trait in profile.traits}
            
            # Use visualization helper to create radar chart
            fig = self.viz_helper.create_trait_radar_chart(trait_data, "Entrepreneurial Trait Profile")
            
            # Convert to HTML
            radar_html = fig.to_html(
                include_plotlyjs='inline',
                div_id='radar-chart',
                config={'displayModeBar': False}
            )
            
            visualizations['radar_chart'] = radar_html
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")
            visualizations['radar_chart'] = f"<p>Visualization unavailable: {str(e)}</p>"
        
        return visualizations
    
    def _generate_unified_html_report(self, profile: PersonTraitProfile, llm_content: Dict[str, str]) -> str:
        """Generate HTML report matching the unified Verrita style"""
        
        # Get archetype info
        primary_archetype = profile.primary_archetype
        archetype_name = primary_archetype.archetype.value.replace('_', ' ').title() if primary_archetype else "Unknown"
        archetype_match = f"{primary_archetype.score * 100:.1f}" if primary_archetype else "0.0"
        
        # Generate trait bars
        trait_bars = self._generate_trait_bars(profile.traits)
        
        # Generate radar chart
        radar_chart = self._create_visualizations(profile)['radar_chart']
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Entrepreneurial Assessment - {profile.person_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        {self._get_verrita_css()}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <div class="company-logo">VERRITA</div>
            <h1 class="report-title">Unified Entrepreneurial Assessment</h1>
            <div class="intro-line">We're excited to help you discover your entrepreneurial strengths and build a focused path forward.</div>
            <div class="hero-quote">"Strategy turns ambition into a roadmap and risks into calculated bets." — Verrita</div>
            <div class="person-name">{profile.person_id}</div>
            <div class="report-date">Generated on {pd.Timestamp.now().strftime('%B %d, %Y')}</div>
        </div>
        
        <div class="report-content">
            <div class="section">
                <div class="executive-summary">
                    <h3>Executive Summary</h3>
                    <p>{llm_content.get('executive_summary', 'Executive summary not available.')}</p>
                </div>
            </div>

            <div class="section">
                <div class="primary-archetype">
                    <div class="archetype-name">{archetype_name}</div>
                    <div class="archetype-match">{archetype_match}%</div>
                </div>
            </div>

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

            <div class="section">
                <h2>Trait Analysis</h2>
                {trait_bars}
            </div>

            <div class="section">
                <h2>Trait Profile Visualization</h2>
                <div class="chart-container">
                    {radar_chart}
                </div>
            </div>

            <div class="section">
                <div class="growth-recommendations">
                    <h3>Growth Recommendations</h3>
                    <p>{llm_content.get('recommendations', 'Recommendations not available.')}</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

    def _get_verrita_css(self) -> str:
        """Get Verrita unified CSS styles"""
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
        .chart-container { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(87, 15, 39, 0.05); margin-bottom: 2rem; }
        .growth-recommendations { background: linear-gradient(135deg, #FFF9E6 0%, #FFF4CC 100%); padding: 2rem; border-radius: 12px; border-left: 6px solid var(--vertria-yellow); }
        .metric-label { font-size: 0.9rem; color: var(--vertria-dark-blue); opacity: 0.8; margin-top: 0.5rem; }
        """
    
    def _generate_trait_bars(self, traits) -> str:
        """Generate trait bars HTML"""
        trait_html = ""
        for trait in traits:
            score = trait.percentile
            bar_width = min(score, 100)
            
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

    def save_report(self, html_content: str, filename: str, output_dir: str = "output/reports") -> str:
        """Save HTML report to file"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            file_path = output_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Report saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            raise