"""
Comprehensive Logging Configuration for Victoria Project
Provides structured logging with different levels and outputs
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'pipeline_stage'):
            log_entry['pipeline_stage'] = record.pipeline_stage
        if hasattr(record, 'processing_time'):
            log_entry['processing_time'] = record.processing_time
        
        return json.dumps(log_entry)

class VictoriaProjectLogger:
    """
    Centralized logging configuration for the Victoria Project.
    
    Provides different logging outputs:
    - Console logging (INFO and above)
    - File logging (DEBUG and above)
    - Error logging (ERROR and above to separate file)
    - JSON structured logging for analysis
    """
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize the logging system.
        
        Args:
            log_directory: Directory to store log files
        """
        self.log_dir = Path(log_directory)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamp for log files
        self.timestamp = datetime.now().strftime("%Y%m%d")
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up all logging handlers and formatters."""
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # 1. Console Handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)
        
        # 2. Main Log File Handler (DEBUG and above)
        main_log_file = self.log_dir / f"victoria_project_{self.timestamp}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
        
        # 3. Error Log File Handler (ERROR and above)
        error_log_file = self.log_dir / f"errors_{self.timestamp}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        root_logger.addHandler(error_handler)
        
        # 4. JSON Structured Log Handler
        json_log_file = self.log_dir / f"structured_{self.timestamp}.json"
        json_handler = logging.FileHandler(json_log_file)
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
        
        # 5. Pipeline-specific Handler
        pipeline_log_file = self.log_dir / f"pipeline_{self.timestamp}.log"
        pipeline_handler = logging.FileHandler(pipeline_log_file)
        pipeline_handler.setLevel(logging.INFO)
        pipeline_handler.setFormatter(file_format)
        
        # Add pipeline handler to pipeline logger
        pipeline_logger = logging.getLogger('src.pipeline')
        pipeline_logger.addHandler(pipeline_handler)
        
        logging.info("Victoria Project logging system initialized")

class PipelineMetrics:
    """
    Metrics collection and logging for pipeline operations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.metrics[operation] = {
            'start_time': datetime.now(),
            'status': 'running'
        }
        self.logger.info(f"Started operation: {operation}")
    
    def end_timer(self, operation: str, success: bool = True, **kwargs):
        """End timing an operation."""
        if operation not in self.metrics:
            self.logger.warning(f"No start time found for operation: {operation}")
            return
        
        end_time = datetime.now()
        duration = (end_time - self.metrics[operation]['start_time']).total_seconds()
        
        self.metrics[operation].update({
            'end_time': end_time,
            'duration_seconds': duration,
            'status': 'success' if success else 'failed',
            **kwargs
        })
        
        # Log with extra fields
        extra = {
            'pipeline_stage': operation,
            'processing_time': duration,
            'status': 'success' if success else 'failed'
        }
        extra.update(kwargs)
        
        self.logger.info(
            f"Completed operation: {operation} in {duration:.2f}s",
            extra=extra
        )
    
    def log_metric(self, metric_name: str, value: Any, **kwargs):
        """Log a custom metric."""
        extra = {
            'metric_name': metric_name,
            'metric_value': value
        }
        extra.update(kwargs)
        
        self.logger.info(f"Metric {metric_name}: {value}", extra=extra)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        summary = {
            'total_operations': len(self.metrics),
            'successful_operations': sum(1 for m in self.metrics.values() if m.get('status') == 'success'),
            'failed_operations': sum(1 for m in self.metrics.values() if m.get('status') == 'failed'),
            'total_processing_time': sum(m.get('duration_seconds', 0) for m in self.metrics.values()),
            'operations': self.metrics
        }
        return summary

class ErrorHandler:
    """
    Centralized error handling for the Victoria Project.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None, 
                    critical: bool = False):
        """
        Handle an error with appropriate logging and context.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            critical: Whether this is a critical error
        """
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Prepare error context
        error_context = {
            'error_type': error_type,
            'error_count': self.error_counts[error_type],
            'critical': critical
        }
        
        if context:
            error_context.update(context)
        
        # Log the error
        log_level = logging.CRITICAL if critical else logging.ERROR
        self.logger.log(
            log_level,
            f"{error_type}: {str(error)}",
            exc_info=True,
            extra=error_context
        )
        
        # If critical, also log to console
        if critical:
            print(f"CRITICAL ERROR: {error_type}: {str(error)}")
    
    def handle_warning(self, message: str, context: Dict[str, Any] = None):
        """Handle a warning with context."""
        warning_context = context or {}
        self.logger.warning(message, extra=warning_context)
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of error counts."""
        return self.error_counts.copy()

# Convenience functions for easy logging setup
def setup_logging(log_directory: str = "logs") -> VictoriaProjectLogger:
    """
    Set up logging for the Victoria Project.
    
    Args:
        log_directory: Directory to store log files
        
    Returns:
        VictoriaProjectLogger instance
    """
    return VictoriaProjectLogger(log_directory)

def get_pipeline_metrics() -> PipelineMetrics:
    """Get a pipeline metrics instance."""
    return PipelineMetrics()

def get_error_handler() -> ErrorHandler:
    """Get an error handler instance."""
    return ErrorHandler()

# Context manager for operation timing
class OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name: str, metrics: PipelineMetrics = None):
        self.operation_name = operation_name
        self.metrics = metrics or get_pipeline_metrics()
        self.success = True
    
    def __enter__(self):
        self.metrics.start_timer(self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.success = False
        self.metrics.end_timer(self.operation_name, self.success)
        
        if exc_type is not None:
            error_handler = get_error_handler()
            error_handler.handle_error(
                exc_val,
                context={'operation': self.operation_name}
            )

# Decorator for automatic error handling
def handle_errors(operation_name: str = None):
    """
    Decorator for automatic error handling in functions.
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            error_handler = get_error_handler()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    e,
                    context={
                        'function': func.__name__,
                        'module': func.__module__,
                        'args': str(args)[:200],  # Truncate long args
                        'kwargs': str(kwargs)[:200]
                    }
                )
                raise
        
        return wrapper
    return decorator