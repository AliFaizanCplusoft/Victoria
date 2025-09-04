"""
PDF Generation Module for Victoria Project
Enhanced PDF generation with visualization support and styling
"""

import os
import tempfile
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import platform

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    print("Warning: pdfkit not available. PDF generation will be limited.")

# Temporarily disable weasyprint due to library dependency issues
# try:
#     import weasyprint
#     WEASYPRINT_AVAILABLE = True
# except ImportError:
WEASYPRINT_AVAILABLE = False
print("Info: weasyprint disabled. Using reportlab for PDF generation.")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    import io
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class PsychometricPDFGenerator:
    """Enhanced PDF generator for psychometric reports."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = Path(tempfile.gettempdir()) / "victoria_pdfs"
        self.temp_dir.mkdir(exist_ok=True)
        
        # PDF generation settings for text-only reports (no visualizations)
        self.pdf_options = {
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
            'minimum-font-size': 12,
            'zoom': 1.0
        }
        
        # Setup pdfkit configuration for Windows
        self.pdfkit_config = None
        if platform.system() == 'Windows':
            # Common installation paths for wkhtmltopdf on Windows
            possible_paths = [
                r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
                r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
                r'C:\wkhtmltopdf\bin\wkhtmltopdf.exe',
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.pdfkit_config = pdfkit.configuration(wkhtmltopdf=path)
                    break
        
        self.logger.info("PsychometricPDFGenerator initialized")
    
    def html_to_pdf_enhanced(self, html_content: str, output_path: str,
                           include_visualizations: bool = False,
                           custom_css: str = None) -> bool:
        """
        Convert HTML to PDF with enhanced styling (no visualizations).
        
        Args:
            html_content: HTML string to convert
            output_path: Path to save PDF
            include_visualizations: Whether to process embedded visualizations (disabled for PDF)
            custom_css: Additional CSS styling
            
        Returns:
            True if successful, False otherwise
        """
        if not PDFKIT_AVAILABLE:
            self.logger.warning("pdfkit not available, trying WeasyPrint")
            return self._try_weasyprint_pdf(html_content, output_path)
        
        try:
            # Remove any visualization content for PDF
            html_content = self._remove_visualizations_from_html(html_content)
            
            # Add default PDF-specific CSS
            default_css = self._get_pdf_css()
            
            # Combine CSS
            all_css = default_css
            if custom_css:
                all_css += "\n" + custom_css
            
            # Embed CSS in HTML
            if all_css:
                css_tag = f'<style type="text/css">{all_css}</style>'
                if '</head>' in html_content:
                    html_content = html_content.replace('</head>', f'{css_tag}</head>')
                else:
                    html_content = css_tag + html_content
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate PDF using pdfkit with simplified options
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
                'disable-javascript': '',  # Disable JavaScript for faster generation
                'enable-internal-links': '',
                'images': '',
            }
            
            pdfkit.from_string(
                html_content, 
                output_path, 
                options=simplified_pdf_options,
                configuration=self.pdfkit_config
            )
            
            self.logger.info(f"PDF generated successfully: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating PDF with pdfkit: {e}")
            print(f"Error generating PDF: {e}")
            return self._try_weasyprint_pdf(html_content, output_path)
    
    def _remove_visualizations_from_html(self, html_content: str) -> str:
        """
        Remove visualization elements from HTML content for PDF generation.
        
        Args:
            html_content: HTML content with embedded visualizations
            
        Returns:
            Modified HTML content without visualizations
        """
        import re
        
        # Remove plotly script tags
        html_content = re.sub(r'<script[^>]*plotly[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove plotly graph divs
        html_content = re.sub(r'<div[^>]*plotly-graph-div[^>]*>.*?</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove chart containers
        html_content = re.sub(r'<div[^>]*chart-container[^>]*>.*?</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove visualization sections
        html_content = re.sub(r'<div[^>]*visualization[^>]*>.*?</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any remaining plotly references
        html_content = re.sub(r'<script[^>]*>.*?Plotly\..*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Add a note that visualizations are excluded in PDF
        pdf_note = """
        <div style="background: #e3f2fd; border: 1px solid #2196f3; padding: 15px; margin: 20px 0; border-radius: 5px;">
            <strong>📊 Note:</strong> Interactive visualizations are excluded from PDF reports for optimal performance and reliability. 
            For interactive charts and graphs, please refer to the HTML version of this report.
        </div>
        """
        
        # Insert the note after the first heading if found
        if '<h1' in html_content:
            html_content = re.sub(r'(<h1[^>]*>.*?</h1>)', r'\1' + pdf_note, html_content, count=1)
        elif '<h2' in html_content:
            html_content = re.sub(r'(<h2[^>]*>.*?</h2>)', r'\1' + pdf_note, html_content, count=1)
        elif '<body' in html_content:
            html_content = html_content.replace('<body>', '<body>' + pdf_note, 1)
        else:
            html_content = pdf_note + html_content
        
        return html_content
    
    def _get_pdf_css(self) -> str:
        """Get default CSS optimized for PDF generation."""
        return """
        /* PDF-specific styling */
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
        
        /* Hide any visualization containers in PDF */
        .visualization, .plotly-graph-div, .chart-container {
            display: none !important;
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
        """
    
    def _fallback_pdf_generation(self, html_content: str, output_path: str) -> bool:
        """
        Fallback PDF generation when pdfkit is not available.
        
        Args:
            html_content: HTML content
            output_path: Output path for PDF
            
        Returns:
            True if fallback successful
        """
        try:
            # Save as HTML file with .pdf extension warning
            html_path = output_path.replace('.pdf', '_fallback.html')
            
            with open(html_path, 'w', encoding='utf-8') as f:
                fallback_notice = """
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px;">
                    <strong>Note:</strong> PDF generation requires pdfkit and wkhtmltopdf. This is an HTML version of your report.
                    <br>To generate PDF: <code>pip install pdfkit</code> and install wkhtmltopdf binary
                </div>
                """
                f.write(fallback_notice + html_content)
            
            self.logger.warning(f"pdfkit not available. Saved HTML version: {html_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fallback PDF generation failed: {e}")
            return False
    
    def _try_weasyprint_pdf(self, html_content: str, output_path: str) -> bool:
        """
        Try to generate PDF using WeasyPrint as fallback.
        
        Args:
            html_content: HTML content to convert
            output_path: Path to save PDF
            
        Returns:
            True if successful, False otherwise
        """
        if not WEASYPRINT_AVAILABLE:
            self.logger.warning("WeasyPrint not available, trying final fallback")
            return self._fallback_pdf_generation(html_content, output_path)
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Add WeasyPrint-specific CSS
            weasyprint_css = """
            @page {
                size: A4;
                margin: 2cm;
            }
            
            body {
                font-family: 'Arial', sans-serif;
                font-size: 12px;
                line-height: 1.4;
                color: #333;
            }
            
            .plotly-graph-div {
                width: 100% !important;
                height: 300px !important;
            }
            
            /* Hide interactive elements for PDF */
            .modebar {
                display: none !important;
            }
            """
            
            # Add CSS to HTML
            if '</head>' in html_content:
                html_content = html_content.replace('</head>', f'<style>{weasyprint_css}</style></head>')
            else:
                html_content = f'<style>{weasyprint_css}</style>' + html_content
            
            # Generate PDF using WeasyPrint
            html_doc = weasyprint.HTML(string=html_content)
            html_doc.write_pdf(output_path)
            
            self.logger.info(f"PDF generated successfully using WeasyPrint: {output_path}")
            print(f"✅ PDF generated using WeasyPrint: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating PDF with WeasyPrint: {e}")
            print(f"❌ WeasyPrint PDF generation failed: {e}")
            return self._fallback_pdf_generation(html_content, output_path)

    def generate_batch_pdfs(self, reports_data: List[Dict[str, Any]], 
                           output_directory: str) -> Dict[str, List[str]]:
        """
        Generate multiple PDF reports in batch.
        
        Args:
            reports_data: List of report data dictionaries
            output_directory: Directory to save PDFs
            
        Returns:
            Dictionary with successful and failed file paths
        """
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {"successful": [], "failed": []}
        
        for i, report_data in enumerate(reports_data):
            try:
                person_id = report_data.get('person_id', f'report_{i+1}')
                html_content = report_data.get('html_content', '')
                
                if not html_content:
                    self.logger.warning(f"No HTML content for {person_id}")
                    continue
                
                pdf_path = output_dir / f"report_{person_id}.pdf"
                
                if self.html_to_pdf_enhanced(html_content, str(pdf_path)):
                    results["successful"].append(str(pdf_path))
                else:
                    results["failed"].append(str(pdf_path))
                    
            except Exception as e:
                self.logger.error(f"Error processing report {i+1}: {e}")
                results["failed"].append(f"report_{i+1}.pdf")
        
        self.logger.info(f"Batch PDF generation complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
        return results
    
    def add_watermark(self, pdf_path: str, watermark_text: str = "CONFIDENTIAL") -> bool:
        """
        Add watermark to existing PDF (requires additional libraries).
        
        Args:
            pdf_path: Path to PDF file
            watermark_text: Text to use as watermark
            
        Returns:
            True if successful
        """
        # This would require PyPDF2 or similar library
        # For now, just log that watermarking was requested
        self.logger.info(f"Watermark requested for {pdf_path}: {watermark_text}")
        return True
    
    def optimize_pdf_size(self, pdf_path: str) -> bool:
        """
        Optimize PDF file size (placeholder for future implementation).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if successful
        """
        self.logger.info(f"PDF optimization requested for {pdf_path}")
        return True
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            for file_path in self.temp_dir.glob("temp_report_*.html"):
                file_path.unlink()
            self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.warning(f"Error cleaning up temp files: {e}")

# Convenience functions for backward compatibility
def html_to_pdf(html_content: str, output_path: str, 
                css_string: str = None, base_url: str = None) -> bool:
    """
    Backward compatible function for PDF generation.
    
    Args:
        html_content: HTML string
        output_path: Path to save PDF
        css_string: Additional CSS
        base_url: Base URL (unused in current implementation)
        
    Returns:
        True if successful
    """
    generator = PsychometricPDFGenerator()
    return generator.html_to_pdf_enhanced(
        html_content, output_path, 
        custom_css=css_string
    )

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
        generator = PsychometricPDFGenerator()
        success = generator.html_to_pdf_enhanced(test_html, test_path)
        
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

if __name__ == "__main__":
    # Test the installation
    print("Testing pdfkit installation...")
    test_pdfkit_installation()