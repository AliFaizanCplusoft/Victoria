"""
Reports module for Victoria Project psychometric assessment system.
"""

try:
    from .report_generator import generate_batch_reports
except ImportError:
    generate_batch_reports = None

try:
    from .personality_report_generator import PersonalityReportGenerator, ReportConfig
except ImportError:
    PersonalityReportGenerator = None
    ReportConfig = None

try:
    from .pdf_generator import PsychometricPDFGenerator
except ImportError:
    PsychometricPDFGenerator = None

__all__ = ['generate_batch_reports', 'PersonalityReportGenerator', 'ReportConfig', 'PsychometricPDFGenerator']