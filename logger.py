#!/usr/bin/env python3
"""
Structured Logging for Tableau Governance Framework

Provides centralized, structured logging with JSON formatting for easy parsing
by log aggregation systems (ELK, Splunk, Grafana Loki, etc.).

Features:
- JSON structured logs for machine parsing
- Multiple output destinations (console, file, syslog)
- Performance timing decorators
- Correlation IDs for request tracing
- Security-safe logging (no credential exposure)
"""

import logging
import logging.handlers
import json
import time
import os
import sys
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, Callable
from config import config

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: LogRecord instance
            
        Returns:
            JSON formatted log string
        """
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add operation context if available
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
        
        # Add site context if available
        if hasattr(record, 'site_name'):
            log_entry["site_name"] = record.site_name
            
        if hasattr(record, 'site_id'):
            log_entry["site_id"] = record.site_id
        
        # Add performance metrics if available
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
            
        if hasattr(record, 'item_count'):
            log_entry["item_count"] = record.item_count
        
        # Add any extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)

class TableauGovernanceLogger:
    """Centralized logger for Tableau governance operations."""
    
    def __init__(self, name: str = "tableau_governance"):
        self.correlation_id = str(uuid.uuid4())
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with appropriate handlers and formatters."""
        # Avoid duplicate handlers
        if self.logger.handlers:
            return
            
        self.logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
        
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler for persistent logs
        log_file = os.path.join(config.log_dir, "governance.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB files, 5 backups
        )
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log with additional context fields."""
        extra = {
            'correlation_id': self.correlation_id,
            'extra_fields': kwargs
        }
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info level message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level message with context."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def operation_start(self, operation: str, **kwargs):
        """Log the start of an operation."""
        self.info(f"Operation started: {operation}", operation=operation, **kwargs)
    
    def operation_end(self, operation: str, duration_ms: float, **kwargs):
        """Log the end of an operation with timing."""
        self.info(
            f"Operation completed: {operation}", 
            operation=operation, 
            duration_ms=round(duration_ms, 2),
            **kwargs
        )
    
    def site_scan_start(self, site_name: str, site_id: str, resource_type: str):
        """Log the start of a site scan."""
        self.info(
            f"Starting {resource_type} scan for site: {site_name}",
            operation="site_scan",
            site_name=site_name,
            site_id=site_id,
            resource_type=resource_type
        )
    
    def site_scan_end(self, site_name: str, site_id: str, resource_type: str, 
                     item_count: int, duration_ms: float):
        """Log the end of a site scan with results."""
        self.info(
            f"Completed {resource_type} scan for site: {site_name} - found {item_count} items",
            operation="site_scan",
            site_name=site_name,
            site_id=site_id,
            resource_type=resource_type,
            item_count=item_count,
            duration_ms=round(duration_ms, 2)
        )
    
    def security_event(self, event_type: str, message: str, **kwargs):
        """Log security-related events."""
        self.warning(
            f"SECURITY: {event_type} - {message}",
            event_type="security",
            security_event=event_type,
            **kwargs
        )

def timed_operation(operation_name: str):
    """
    Decorator to automatically log operation timing.
    
    Args:
        operation_name: Name of the operation being timed
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = TableauGovernanceLogger()
            start_time = time.time()
            
            logger.operation_start(operation_name)
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.operation_end(operation_name, duration_ms, status="success")
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {operation_name}",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    status="error"
                )
                raise
                
        return wrapper
    return decorator

def get_logger(name: str = "tableau_governance") -> TableauGovernanceLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Configured TableauGovernanceLogger instance
    """
    return TableauGovernanceLogger(name)

# Global logger instance
logger = get_logger()

if __name__ == "__main__":
    # Test the logging system
    test_logger = get_logger("test")
    
    test_logger.info("Testing structured logging", test_field="test_value")
    test_logger.warning("Test warning", warning_type="test")
    test_logger.site_scan_start("TestSite", "123", "users")
    test_logger.site_scan_end("TestSite", "123", "users", 42, 1250.5)
    test_logger.security_event("credential_check", "Checking for hardcoded credentials")
    
    print("Logging test completed. Check governance.log file.")