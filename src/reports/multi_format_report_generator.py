"""
Multi-Format Report Generator for Victoria Project

Generates comprehensive reports in multiple formats (PDF, HTML, CSV, JSON)
with RaschPy analysis integration.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
from pathlib import Path
from datetime import datetime
import json
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader

# Import RaschPy integration
try:
    from ..data.rasch_analysis import RaschResults
except ImportError:
    RaschResults = None

# Import existing report generation
try:
    from .report_generator import generate_html_report, html_to_pdf
except ImportError:
    generate_html_report = None
    html_to_pdf = None

@dataclass
class ReportConfig:
    """Configuration for report generation."""
    include_person_profiles: bool = True
    include_item_analysis: bool = True
    include_fit_statistics: bool = True
    include_visualizations: bool = True
    include_rasch_measures: bool = True
    color_theme: str = "professional"
    format: str = "html"  # html, pdf, csv, json
    output_directory: str = "output/reports"

class MultiFormatReportGenerator:
    """
    Comprehensive report generator supporting multiple output formats.
    
    Features:
    - Individual person profiles
    - Item analysis reports
    - Group summary reports
    - Multi-format export (PDF, HTML, CSV, JSON)
    - RaschPy integration
    - Interactive visualizations
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the report generator.
        
        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up template environment
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates" / "html"
        
        self.template_dir = Path(template_dir)
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)
            self.logger.warning(f"Created template directory: {self.template_dir}")
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Add custom filters
        self.env.filters.update({
            'format_score': self._format_score,
            'format_percentile': self._format_percentile,
            'format_date': self._format_date
        })
        
        self.logger.info("MultiFormatReportGenerator initialized")
    
    def generate_comprehensive_report(self, 
                                    rasch_results: RaschResults,
                                    config: ReportConfig) -> Dict[str, Any]:
        """
        Generate comprehensive report with all requested formats.
        
        Args:
            rasch_results: Results from RaschPy analysis
            config: Report configuration
            
        Returns:
            Dictionary with generated report paths and metadata
        """
        output_dir = Path(config.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            'generation_time': datetime.now().isoformat(),
            'config': config,
            'formats': [],
            'files': {}
        }
        
        try:
            # Generate HTML report
            if config.format in ['html', 'all']:
                html_path = self._generate_html_report(rasch_results, config, output_dir)
                report_data['files']['html'] = html_path
                report_data['formats'].append('html')
            
            # Generate PDF report
            if config.format in ['pdf', 'all']:
                pdf_path = self._generate_pdf_report(rasch_results, config, output_dir)
                report_data['files']['pdf'] = pdf_path
                report_data['formats'].append('pdf')
            
            # Generate CSV exports
            if config.format in ['csv', 'all']:
                csv_paths = self._generate_csv_exports(rasch_results, config, output_dir)
                report_data['files']['csv'] = csv_paths
                report_data['formats'].append('csv')
            
            # Generate JSON export
            if config.format in ['json', 'all']:
                json_path = self._generate_json_export(rasch_results, config, output_dir)
                report_data['files']['json'] = json_path
                report_data['formats'].append('json')
            
            self.logger.info(f"Generated comprehensive report in {len(report_data['formats'])} formats")
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            report_data['error'] = str(e)
        
        return report_data
    
    def generate_individual_profiles(self, 
                                   rasch_results: RaschResults,
                                   config: ReportConfig) -> Dict[str, List[str]]:
        """
        Generate individual person profile reports.
        
        Args:
            rasch_results: Results from RaschPy analysis
            config: Report configuration
            
        Returns:
            Dictionary with lists of generated file paths by format
        """
        output_dir = Path(config.output_directory) / "individual_profiles"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = {'html': [], 'pdf': [], 'json': []}
        
        if rasch_results.person_abilities is None:
            self.logger.warning("No person abilities available for individual profiles")
            return generated_files
        
        try:
            for _, person in rasch_results.person_abilities.iterrows():
                person_id = person['person_id']
                
                # Generate HTML profile
                if config.format in ['html', 'all']:
                    html_path = self._generate_individual_html_profile(person, rasch_results, config, output_dir)
                    generated_files['html'].append(html_path)
                
                # Generate PDF profile
                if config.format in ['pdf', 'all']:
                    pdf_path = self._generate_individual_pdf_profile(person, rasch_results, config, output_dir)
                    generated_files['pdf'].append(pdf_path)
                
                # Generate JSON profile
                if config.format in ['json', 'all']:
                    json_path = self._generate_individual_json_profile(person, rasch_results, config, output_dir)
                    generated_files['json'].append(json_path)
            
            self.logger.info(f"Generated {len(rasch_results.person_abilities)} individual profiles")
            
        except Exception as e:
            self.logger.error(f"Error generating individual profiles: {e}")
        
        return generated_files
    
    def generate_item_analysis_report(self, 
                                    rasch_results: RaschResults,
                                    config: ReportConfig) -> str:
        """
        Generate comprehensive item analysis report.
        
        Args:
            rasch_results: Results from RaschPy analysis
            config: Report configuration
            
        Returns:
            Path to generated report
        """
        output_dir = Path(config.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Prepare item analysis data
            item_data = self._prepare_item_analysis_data(rasch_results)
            
            # Generate report content
            template = self._get_or_create_template('item_analysis_template.html')
            
            html_content = template.render(
                item_data=item_data,
                rasch_results=rasch_results,
                config=config,
                generation_time=datetime.now(),
                report_title="Item Analysis Report"
            )
            
            # Save HTML report
            html_path = output_dir / "item_analysis_report.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate PDF if requested
            if config.format in ['pdf', 'all']:
                pdf_path = output_dir / "item_analysis_report.pdf"
                if html_to_pdf:
                    html_to_pdf(html_content, str(pdf_path))
            
            self.logger.info(f"Generated item analysis report: {html_path}")
            return str(html_path)
            
        except Exception as e:
            self.logger.error(f"Error generating item analysis report: {e}")
            return ""
    
    def generate_group_summary_report(self, 
                                    rasch_results: RaschResults,
                                    config: ReportConfig) -> str:
        """
        Generate group summary report with population statistics.
        
        Args:
            rasch_results: Results from RaschPy analysis
            config: Report configuration
            
        Returns:
            Path to generated report
        """
        output_dir = Path(config.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Prepare group summary data
            group_data = self._prepare_group_summary_data(rasch_results)
            
            # Generate report content
            template = self._get_or_create_template('group_summary_template.html')
            
            html_content = template.render(
                group_data=group_data,
                rasch_results=rasch_results,
                config=config,
                generation_time=datetime.now(),
                report_title="Group Summary Report"
            )
            
            # Save HTML report
            html_path = output_dir / "group_summary_report.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate PDF if requested
            if config.format in ['pdf', 'all']:
                pdf_path = output_dir / "group_summary_report.pdf"
                if html_to_pdf:
                    html_to_pdf(html_content, str(pdf_path))
            
            self.logger.info(f"Generated group summary report: {html_path}")
            return str(html_path)
            
        except Exception as e:
            self.logger.error(f"Error generating group summary report: {e}")
            return ""
    
    def _generate_html_report(self, rasch_results: RaschResults, 
                             config: ReportConfig, output_dir: Path) -> str:
        """Generate HTML report."""
        try:
            # Prepare comprehensive data
            report_data = self._prepare_comprehensive_data(rasch_results)
            
            # Get or create template
            template = self._get_or_create_template('comprehensive_report_template.html')
            
            # Render HTML
            html_content = template.render(
                report_data=report_data,
                rasch_results=rasch_results,
                config=config,
                generation_time=datetime.now(),
                report_title="Comprehensive Assessment Report"
            )
            
            # Save HTML file
            html_path = output_dir / "comprehensive_report.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(html_path)
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return ""
    
    def _generate_pdf_report(self, rasch_results: RaschResults, 
                           config: ReportConfig, output_dir: Path) -> str:
        """Generate PDF report."""
        try:
            # Generate HTML first
            html_path = self._generate_html_report(rasch_results, config, output_dir)
            
            if html_path and html_to_pdf:
                # Read HTML content
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Generate PDF
                pdf_path = output_dir / "comprehensive_report.pdf"
                success = html_to_pdf(html_content, str(pdf_path))
                
                if success:
                    return str(pdf_path)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {e}")
            return ""
    
    def _generate_csv_exports(self, rasch_results: RaschResults, 
                            config: ReportConfig, output_dir: Path) -> Dict[str, str]:
        """Generate CSV exports."""
        csv_files = {}
        
        try:
            # Person abilities CSV
            if rasch_results.person_abilities is not None:
                person_path = output_dir / "person_abilities.csv"
                rasch_results.person_abilities.to_csv(person_path, index=False)
                csv_files['person_abilities'] = str(person_path)
            
            # Item difficulties CSV
            if rasch_results.item_difficulties is not None:
                item_path = output_dir / "item_difficulties.csv"
                rasch_results.item_difficulties.to_csv(item_path, index=False)
                csv_files['item_difficulties'] = str(item_path)
            
            # Transformed data CSV
            if rasch_results.transformed_data is not None:
                transform_path = output_dir / "transformed_data.csv"
                rasch_results.transformed_data.to_csv(transform_path, index=False)
                csv_files['transformed_data'] = str(transform_path)
            
            # Fit statistics CSV
            if rasch_results.fit_statistics is not None:
                fit_path = output_dir / "fit_statistics.csv"
                rasch_results.fit_statistics.to_csv(fit_path, index=False)
                csv_files['fit_statistics'] = str(fit_path)
            
            self.logger.info(f"Generated {len(csv_files)} CSV files")
            
        except Exception as e:
            self.logger.error(f"Error generating CSV exports: {e}")
        
        return csv_files
    
    def _generate_json_export(self, rasch_results: RaschResults, 
                            config: ReportConfig, output_dir: Path) -> str:
        """Generate JSON export."""
        try:
            # Prepare JSON data
            json_data = {
                'metadata': {
                    'generation_time': datetime.now().isoformat(),
                    'model_type': 'Rasch Analysis',
                    'success': rasch_results.success
                },
                'model_summary': rasch_results.model_summary,
                'person_abilities': rasch_results.person_abilities.to_dict('records') if rasch_results.person_abilities is not None else None,
                'item_difficulties': rasch_results.item_difficulties.to_dict('records') if rasch_results.item_difficulties is not None else None,
                'fit_statistics': rasch_results.fit_statistics.to_dict('records') if rasch_results.fit_statistics is not None else None,
                'transformed_data_sample': rasch_results.transformed_data.head(100).to_dict('records') if rasch_results.transformed_data is not None else None,
                'processing_log': rasch_results.processing_log,
                'errors': rasch_results.errors
            }
            
            # Save JSON file
            json_path = output_dir / "rasch_analysis_results.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            return str(json_path)
            
        except Exception as e:
            self.logger.error(f"Error generating JSON export: {e}")
            return ""
    
    def _generate_individual_html_profile(self, person: pd.Series, 
                                        rasch_results: RaschResults,
                                        config: ReportConfig, output_dir: Path) -> str:
        """Generate individual HTML profile."""
        try:
            person_id = person['person_id']
            
            # Get person's responses from transformed data
            person_responses = None
            if rasch_results.transformed_data is not None:
                person_responses = rasch_results.transformed_data[
                    rasch_results.transformed_data['Persons'] == person_id
                ]
            
            # Prepare person data
            person_data = {
                'person_id': person_id,
                'ability': person['ability'],
                'ability_se': person.get('ability_se', None),
                'person_fit': person.get('person_fit', None),
                'responses': person_responses.to_dict('records') if person_responses is not None else [],
                'response_count': len(person_responses) if person_responses is not None else 0
            }
            
            # Get or create template
            template = self._get_or_create_template('individual_profile_template.html')
            
            # Render HTML
            html_content = template.render(
                person_data=person_data,
                rasch_results=rasch_results,
                config=config,
                generation_time=datetime.now(),
                report_title=f"Individual Profile - {person_id}"
            )
            
            # Save HTML file
            html_path = output_dir / f"profile_{person_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(html_path)
            
        except Exception as e:
            self.logger.error(f"Error generating individual HTML profile: {e}")
            return ""
    
    def _generate_individual_pdf_profile(self, person: pd.Series, 
                                       rasch_results: RaschResults,
                                       config: ReportConfig, output_dir: Path) -> str:
        """Generate individual PDF profile."""
        try:
            # Generate HTML first
            html_path = self._generate_individual_html_profile(person, rasch_results, config, output_dir)
            
            if html_path and html_to_pdf:
                # Read HTML content
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Generate PDF
                person_id = person['person_id']
                pdf_path = output_dir / f"profile_{person_id}.pdf"
                success = html_to_pdf(html_content, str(pdf_path))
                
                if success:
                    return str(pdf_path)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error generating individual PDF profile: {e}")
            return ""
    
    def _generate_individual_json_profile(self, person: pd.Series, 
                                        rasch_results: RaschResults,
                                        config: ReportConfig, output_dir: Path) -> str:
        """Generate individual JSON profile."""
        try:
            person_id = person['person_id']
            
            # Get person's responses from transformed data
            person_responses = None
            if rasch_results.transformed_data is not None:
                person_responses = rasch_results.transformed_data[
                    rasch_results.transformed_data['Persons'] == person_id
                ]
            
            # Prepare JSON data
            json_data = {
                'person_id': person_id,
                'ability': float(person['ability']),
                'ability_se': float(person.get('ability_se', 0)) if person.get('ability_se') is not None else None,
                'person_fit': float(person.get('person_fit', 0)) if person.get('person_fit') is not None else None,
                'responses': person_responses.to_dict('records') if person_responses is not None else [],
                'response_count': len(person_responses) if person_responses is not None else 0,
                'generation_time': datetime.now().isoformat()
            }
            
            # Save JSON file
            json_path = output_dir / f"profile_{person_id}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            return str(json_path)
            
        except Exception as e:
            self.logger.error(f"Error generating individual JSON profile: {e}")
            return ""
    
    def _prepare_comprehensive_data(self, rasch_results: RaschResults) -> Dict[str, Any]:
        """Prepare comprehensive data for report generation."""
        return {
            'summary': rasch_results.model_summary,
            'person_count': len(rasch_results.person_abilities) if rasch_results.person_abilities is not None else 0,
            'item_count': len(rasch_results.item_difficulties) if rasch_results.item_difficulties is not None else 0,
            'success': rasch_results.success,
            'processing_log': rasch_results.processing_log,
            'errors': rasch_results.errors
        }
    
    def _prepare_item_analysis_data(self, rasch_results: RaschResults) -> Dict[str, Any]:
        """Prepare item analysis data."""
        item_data = {'items': []}
        
        if rasch_results.item_difficulties is not None:
            for _, item in rasch_results.item_difficulties.iterrows():
                item_data['items'].append({
                    'item_id': item['item_id'],
                    'difficulty': item['difficulty'],
                    'difficulty_se': item.get('difficulty_se', None),
                    'item_fit': item.get('item_fit', None)
                })
        
        return item_data
    
    def _prepare_group_summary_data(self, rasch_results: RaschResults) -> Dict[str, Any]:
        """Prepare group summary data."""
        group_data = {
            'model_summary': rasch_results.model_summary,
            'person_statistics': {},
            'item_statistics': {}
        }
        
        if rasch_results.person_abilities is not None:
            abilities = rasch_results.person_abilities['ability']
            group_data['person_statistics'] = {
                'mean_ability': float(abilities.mean()),
                'std_ability': float(abilities.std()),
                'min_ability': float(abilities.min()),
                'max_ability': float(abilities.max()),
                'count': len(abilities)
            }
        
        if rasch_results.item_difficulties is not None:
            difficulties = rasch_results.item_difficulties['difficulty']
            group_data['item_statistics'] = {
                'mean_difficulty': float(difficulties.mean()),
                'std_difficulty': float(difficulties.std()),
                'min_difficulty': float(difficulties.min()),
                'max_difficulty': float(difficulties.max()),
                'count': len(difficulties)
            }
        
        return group_data
    
    def _get_or_create_template(self, template_name: str) -> Any:
        """Get existing template or create a basic one."""
        try:
            return self.env.get_template(template_name)
        except Exception:
            # Create basic template
            basic_template = self._create_basic_template(template_name)
            template_path = self.template_dir / template_name
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(basic_template)
            return self.env.get_template(template_name)
    
    def _create_basic_template(self, template_name: str) -> str:
        """Create a basic template for the given name."""
        if 'comprehensive' in template_name:
            return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ report_title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .data-table { border-collapse: collapse; width: 100%; }
        .data-table th, .data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .data-table th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_title }}</h1>
        <p>Generated: {{ generation_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
    
    <div class="section">
        <h2>Analysis Summary</h2>
        {% if report_data.summary %}
            <p>Persons: {{ report_data.summary.persons_count }}</p>
            <p>Items: {{ report_data.summary.items_count }}</p>
            <p>Success: {{ report_data.success }}</p>
        {% endif %}
    </div>
    
    <div class="section">
        <h2>Processing Log</h2>
        <ul>
        {% for log_entry in rasch_results.processing_log %}
            <li>{{ log_entry }}</li>
        {% endfor %}
        </ul>
    </div>
</body>
</html>
"""
        elif 'individual' in template_name:
            return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ report_title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .stat-box { display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_title }}</h1>
        <p>Generated: {{ generation_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
    
    <div class="section">
        <h2>Person Statistics</h2>
        <div class="stat-box">
            <strong>Person ID:</strong> {{ person_data.person_id }}
        </div>
        <div class="stat-box">
            <strong>Ability:</strong> {{ person_data.ability|format_score }}
        </div>
        <div class="stat-box">
            <strong>Responses:</strong> {{ person_data.response_count }}
        </div>
    </div>
</body>
</html>
"""
        else:
            return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ report_title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_title }}</h1>
        <p>Generated: {{ generation_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>
</body>
</html>
"""
    
    def _format_score(self, value: Any, precision: int = 2) -> str:
        """Format score to specified precision."""
        try:
            return f"{float(value):.{precision}f}"
        except (ValueError, TypeError):
            return "N/A"
    
    def _format_percentile(self, value: Any) -> str:
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
    
    def _format_date(self, date_obj: datetime) -> str:
        """Format datetime object."""
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')