#!/usr/bin/env python3
"""
Unit tests for logging module.

Tests the structured logging system including JSON formatting,
timing decorators, and security-safe logging.
"""

import pytest
import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import JSONFormatter, TableauGovernanceLogger, timed_operation, get_logger
import logging

class TestJSONFormatter:
    """Test cases for JSONFormatter class."""
    
    def test_basic_formatting(self):
        """Test basic JSON log formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=1,
            msg="Test message", args=(), exc_info=None, func="test_func"
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["function"] == "test_func"
        assert log_data["line"] == 1
        assert "timestamp" in log_data
    
    def test_correlation_id_handling(self):
        """Test correlation ID inclusion in logs."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=1,
            msg="Test message", args=(), exc_info=None, func="test_func"
        )
        record.correlation_id = "test-123"
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["correlation_id"] == "test-123"
    
    def test_operation_context(self):
        """Test operation context in logs."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=1,
            msg="Test message", args=(), exc_info=None, func="test_func"
        )
        record.operation = "user_scan"
        record.site_name = "TestSite"
        record.duration_ms = 1250.5
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["operation"] == "user_scan"
        assert log_data["site_name"] == "TestSite"
        assert log_data["duration_ms"] == 1250.5

class TestTableauGovernanceLogger:
    """Test cases for TableauGovernanceLogger class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Use temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('logger.config')
    def test_logger_initialization(self, mock_config):
        """Test logger initialization."""
        mock_config.log_level = "INFO"
        mock_config.log_dir = self.temp_dir
        
        logger = TableauGovernanceLogger("test")
        
        assert logger.logger.name == "test"
        assert len(logger.correlation_id) > 0
        assert logger.logger.level == logging.INFO
    
    @patch('logger.config')
    def test_info_logging(self, mock_config):
        """Test info level logging with context."""
        mock_config.log_level = "INFO"
        mock_config.log_dir = self.temp_dir
        
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = TableauGovernanceLogger("test")
            logger.info("Test message", test_field="test_value")
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.INFO
            assert call_args[0][1] == "Test message"
            assert "extra_fields" in call_args[1]["extra"]
            assert call_args[1]["extra"]["extra_fields"]["test_field"] == "test_value"
    
    @patch('logger.config')
    def test_operation_timing(self, mock_config):
        """Test operation start/end logging."""
        mock_config.log_level = "INFO"
        mock_config.log_dir = self.temp_dir
        
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = TableauGovernanceLogger("test")
            logger.operation_start("test_operation", param1="value1")
            logger.operation_end("test_operation", 1250.5, status="success")
            
            assert mock_log.call_count == 2
            
            # Check start call
            start_call = mock_log.call_args_list[0]
            assert "Operation started: test_operation" in start_call[0][1]
            
            # Check end call  
            end_call = mock_log.call_args_list[1]
            assert "Operation completed: test_operation" in end_call[0][1]
    
    @patch('logger.config')
    def test_site_scan_logging(self, mock_config):
        """Test site scan specific logging."""
        mock_config.log_level = "INFO"
        mock_config.log_dir = self.temp_dir
        
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = TableauGovernanceLogger("test")
            logger.site_scan_start("TestSite", "123", "users")
            logger.site_scan_end("TestSite", "123", "users", 42, 1500.0)
            
            assert mock_log.call_count == 2
            
            # Verify site context is included
            for call in mock_log.call_args_list:
                extra = call[1]["extra"]
                assert "site_name" in extra.get("extra_fields", {}) or call[1].get("extra_fields", {})
    
    @patch('logger.config')
    def test_security_event_logging(self, mock_config):
        """Test security event logging."""
        mock_config.log_level = "INFO"
        mock_config.log_dir = self.temp_dir
        
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = TableauGovernanceLogger("test")
            logger.security_event("credential_check", "Found hardcoded credentials", file="test.py")
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.WARNING
            assert "SECURITY:" in call_args[0][1]
            assert "credential_check" in call_args[0][1]

class TestTimedOperation:
    """Test cases for timed_operation decorator."""
    
    @patch('logger.TableauGovernanceLogger')
    def test_successful_operation_timing(self, mock_logger_class):
        """Test timing of successful operations."""
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        @timed_operation("test_operation")
        def test_function():
            return "success"
        
        result = test_function()
        
        assert result == "success"
        mock_logger.operation_start.assert_called_once_with("test_operation")
        mock_logger.operation_end.assert_called_once()
        
        # Check that end call includes duration and status
        end_call_args = mock_logger.operation_end.call_args
        assert end_call_args[0][0] == "test_operation"
        assert end_call_args[1]["status"] == "success"
        assert "duration_ms" in end_call_args[0]
    
    @patch('logger.TableauGovernanceLogger')
    def test_failed_operation_timing(self, mock_logger_class):
        """Test timing of failed operations."""
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger
        
        @timed_operation("test_operation")
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_function()
        
        mock_logger.operation_start.assert_called_once_with("test_operation")
        mock_logger.error.assert_called_once()
        
        # Check error logging details
        error_call_args = mock_logger.error.call_args
        assert "Operation failed: test_operation" in error_call_args[0][0]
        assert error_call_args[1]["error_type"] == "ValueError"
        assert error_call_args[1]["error_message"] == "Test error"
        assert error_call_args[1]["status"] == "error"

class TestGetLogger:
    """Test cases for get_logger function."""
    
    def test_get_logger_returns_instance(self):
        """Test that get_logger returns TableauGovernanceLogger instance."""
        with patch('logger.config'):
            logger = get_logger("test")
            assert isinstance(logger, TableauGovernanceLogger)
            assert logger.logger.name == "test"
    
    def test_default_logger_name(self):
        """Test default logger name."""
        with patch('logger.config'):
            logger = get_logger()
            assert logger.logger.name == "tableau_governance"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])