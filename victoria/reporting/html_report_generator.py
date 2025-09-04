"""
HTML Report Generator - Integrates LLM-powered reports with the Victoria Pipeline
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid
import pandas as pd

from victoria.core.models import PersonTraitProfile, ReportData
from victoria.config.settings import app_config
from .llm_report_generator import LLMReportGenerator
from .dynamic_report_generator import DynamicReportGenerator

logger = logging.getLogger(__name__)

class HTMLReportGenerator:
    """
    Main HTML report generator that integrates with the Victoria Project pipeline
    Coordinates LLM-powered content generation with visualization and template rendering
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm_generator = LLMReportGenerator()
        self.dynamic_generator = DynamicReportGenerator()  # New dynamic generator
        
        # Output directories
        self.reports_dir = Path("output/reports")
        self.temp_dir = Path("output/temp")
        
        # Create directories
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_individual_report(self, profile: PersonTraitProfile, 
                                 format_type: str = "html",
                                 save_to_file: bool = True,
                                 use_dynamic: bool = True) -> Dict[str, Any]:
        """
        Generate an individual assessment report
        
        Args:
            profile: PersonTraitProfile object
            format_type: Output format ("html" or "pdf")
            save_to_file: Whether to save to file
            use_dynamic: Whether to use the new dynamic report generator (default: True)
            
        Returns:
            Dict with report content and metadata
        """
        self.logger.info(f"Generating individual report for {profile.person_id}")
        
        try:
            # Generate report ID
            report_id = f"report_{profile.person_id}_{uuid.uuid4().hex[:8]}"
            
            # Generate HTML content using new dynamic generator
            if use_dynamic:
                html_content = self.dynamic_generator.create_html_report(profile)
            else:
                # Fallback to LLM generator
                html_content = self.llm_generator.generate_comprehensive_report(
                    profile, report_id=report_id
                )
            
            result = {
                'report_id': report_id,
                'person_id': profile.person_id,
                'content': html_content,
                'format': format_type,
                'generator_used': 'dynamic' if use_dynamic else 'llm',
                'metadata': {
                    'generation_timestamp': pd.Timestamp.now().isoformat(),
                    'overall_score': profile.overall_score,
                    'completion_rate': profile.completion_rate,
                    'primary_archetype': profile.primary_archetype.archetype.value if profile.primary_archetype else None,
                    'traits_count': len(profile.traits)
                }
            }
            
            # Save to file if requested
            if save_to_file:
                filename = f"vertria_{profile.person_id}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
                file_path = self.reports_dir / filename
                
                # Write the HTML content to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                result['file_path'] = str(file_path)
                result['filename'] = filename
            
            self.logger.info(f"Individual report generated successfully: {report_id} (using {'dynamic' if use_dynamic else 'llm'} generator)")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating individual report: {e}")
            raise
    
    def generate_batch_reports(self, profiles: Dict[str, PersonTraitProfile],
                             format_type: str = "html") -> Dict[str, Any]:
        """
        Generate reports for multiple profiles
        
        Args:
            profiles: Dictionary of PersonTraitProfile objects
            format_type: Output format
            
        Returns:
            Dictionary with batch generation results
        """
        self.logger.info(f"Generating batch reports for {len(profiles)} profiles")
        
        results = {
            'batch_id': f"batch_{uuid.uuid4().hex[:8]}",
            'total_profiles': len(profiles),
            'successful_reports': [],
            'failed_reports': [],
            'summary': {}
        }
        
        for person_id, profile in profiles.items():
            try:
                report_result = self.generate_individual_report(profile, format_type)
                results['successful_reports'].append(report_result)
                
            except Exception as e:
                self.logger.error(f"Failed to generate report for {person_id}: {e}")
                results['failed_reports'].append({
                    'person_id': person_id,
                    'error': str(e)
                })
        
        # Generate summary
        results['summary'] = {
            'success_count': len(results['successful_reports']),
            'failure_count': len(results['failed_reports']),
            'success_rate': len(results['successful_reports']) / len(profiles) if profiles else 0
        }
        
        self.logger.info(f"Batch report generation completed: {results['summary']}")
        return results
    
    def generate_group_summary_report(self, profiles: Dict[str, PersonTraitProfile]) -> Dict[str, Any]:
        """
        Generate a group summary report analyzing multiple profiles
        """
        self.logger.info(f"Generating group summary report for {len(profiles)} profiles")
        
        try:
            # Analyze group data
            group_analysis = self._analyze_group_data(profiles)
            
            # Generate group report HTML
            html_content = self._generate_group_html(group_analysis)
            
            # Save report
            report_id = f"group_summary_{uuid.uuid4().hex[:8]}"
            filename = f"{report_id}.html"
            file_path = self.llm_generator.save_report(html_content, filename, str(self.reports_dir))
            
            return {
                'report_id': report_id,
                'type': 'group_summary',
                'content': html_content,
                'file_path': file_path,
                'filename': filename,
                'profiles_analyzed': len(profiles),
                'group_analysis': group_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error generating group summary report: {e}")
            raise
    
    def _analyze_group_data(self, profiles: Dict[str, PersonTraitProfile]) -> Dict[str, Any]:
        """Analyze group-level patterns and statistics"""
        analysis = {
            'total_profiles': len(profiles),
            'average_scores': {},
            'archetype_distribution': {},
            'trait_statistics': {},
            'completion_rates': []
        }
        
        # Collect data
        all_traits = {}
        archetype_counts = {}
        
        for profile in profiles.values():
            # Completion rates
            analysis['completion_rates'].append(profile.completion_rate)
            
            # Archetype distribution
            if profile.primary_archetype:
                arch_name = profile.primary_archetype.archetype.value
                archetype_counts[arch_name] = archetype_counts.get(arch_name, 0) + 1
            
            # Trait scores
            for trait in profile.traits:
                if trait.trait_name not in all_traits:
                    all_traits[trait.trait_name] = []
                all_traits[trait.trait_name].append(trait.score)
        
        # Calculate statistics
        import numpy as np
        
        analysis['average_completion_rate'] = np.mean(analysis['completion_rates'])
        analysis['archetype_distribution'] = archetype_counts
        
        for trait_name, scores in all_traits.items():
            analysis['trait_statistics'][trait_name] = {
                'mean': np.mean(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores),
                'median': np.median(scores)
            }
        
        return analysis
    
    def _generate_group_html(self, group_analysis: Dict[str, Any]) -> str:
        """Generate HTML for group summary report"""
        # This is a simplified version - you could expand with more sophisticated templates
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Group Summary Report</title>
            <style>
                {self.llm_generator._get_css_styles()}
                .group-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <header class="report-header">
                    <div class="header-content">
                        <h1>Group Assessment Summary</h1>
                        <h2>{group_analysis['total_profiles']} Profiles Analyzed</h2>
                    </div>
                </header>
                
                <section class="section">
                    <h2 class="section-title">Group Overview</h2>
                    <div class="group-stats">
                        <div class="metric-card">
                            <h3>Average Completion Rate</h3>
                            <div class="metric-value">{group_analysis['average_completion_rate']:.1%}</div>
                        </div>
                        <div class="metric-card">
                            <h3>Total Profiles</h3>
                            <div class="metric-value">{group_analysis['total_profiles']}</div>
                        </div>
                    </div>
                </section>
                
                <section class="section">
                    <h2 class="section-title">Archetype Distribution</h2>
                    <div class="content-box">
                        {self._format_archetype_distribution(group_analysis['archetype_distribution'])}
                    </div>
                </section>
                
                <section class="section">
                    <h2 class="section-title">Trait Statistics</h2>
                    <div class="content-box">
                        {self._format_trait_statistics(group_analysis['trait_statistics'])}
                    </div>
                </section>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_archetype_distribution(self, distribution: Dict[str, int]) -> str:
        """Format archetype distribution for HTML"""
        if not distribution:
            return "<p>No archetype data available.</p>"
        
        total = sum(distribution.values())
        html = "<ul>"
        for archetype, count in distribution.items():
            percentage = (count / total) * 100
            formatted_name = archetype.replace('_', ' ').title()
            html += f"<li><strong>{formatted_name}:</strong> {count} individuals ({percentage:.1f}%)</li>"
        html += "</ul>"
        return html
    
    def _format_trait_statistics(self, trait_stats: Dict[str, Dict]) -> str:
        """Format trait statistics for HTML"""
        if not trait_stats:
            return "<p>No trait statistics available.</p>"
        
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr><th>Trait</th><th>Mean</th><th>Std Dev</th><th>Min</th><th>Max</th></tr>"
        
        for trait_name, stats in trait_stats.items():
            html += f"""
            <tr>
                <td style='border: 1px solid #ddd; padding: 8px;'><strong>{trait_name}</strong></td>
                <td style='border: 1px solid #ddd; padding: 8px;'>{stats['mean']:.3f}</td>
                <td style='border: 1px solid #ddd; padding: 8px;'>{stats['std']:.3f}</td>
                <td style='border: 1px solid #ddd; padding: 8px;'>{stats['min']:.3f}</td>
                <td style='border: 1px solid #ddd; padding: 8px;'>{stats['max']:.3f}</td>
            </tr>
            """
        html += "</table>"
        return html
    
    def integrate_with_pipeline(self, processed_profiles: Dict[str, PersonTraitProfile],
                               report_options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main integration point with the Victoria Project pipeline
        
        Args:
            processed_profiles: Output from trait scoring pipeline
            report_options: Configuration options for report generation
            
        Returns:
            Complete report generation results
        """
        options = report_options or {}
        
        self.logger.info(f"Integrating report generation with pipeline: {len(processed_profiles)} profiles")
        
        results = {
            'pipeline_integration': True,
            'input_profiles': len(processed_profiles),
            'individual_reports': None,
            'group_summary': None,
            'generation_timestamp': pd.Timestamp.now().isoformat()
        }
        
        try:
            # Generate individual reports if requested (default: True)
            if options.get('generate_individual', True):
                batch_results = self.generate_batch_reports(processed_profiles)
                results['individual_reports'] = batch_results
            
            # Generate group summary if requested (default: True for multiple profiles)
            if options.get('generate_group_summary', len(processed_profiles) > 1):
                group_summary = self.generate_group_summary_report(processed_profiles)
                results['group_summary'] = group_summary
            
            self.logger.info("Pipeline integration completed successfully")
            
        except Exception as e:
            self.logger.error(f"Pipeline integration failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_report_status(self) -> Dict[str, Any]:
        """Get status of report generation system"""
        return {
            'reports_directory': str(self.reports_dir),
            'temp_directory': str(self.temp_dir),
            'llm_enabled': self.llm_generator.llm_enabled,
            'openai_configured': bool(self.llm_generator.openai_api_key),
            'report_files': len(list(self.reports_dir.glob('*.html'))) if self.reports_dir.exists() else 0
        }