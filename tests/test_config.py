#!/usr/bin/env python3
"""
Unit tests for configuration module.

Tests the secure configuration system including environment variable
handling and validation.
"""

import pytest
import os
import tempfile
import json
from unittest.mock import patch, mock_open
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

class TestConfig:
    """Test cases for Config class."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        # Mock empty config file
        with patch("builtins.open", mock_open(read_data="{}")):
            config = Config("test_config.json")
            
            assert config.stale_user_days == 365
            assert config.stale_content_days == 730
            assert config.stale_site_days == 365
            assert config.log_only is True
            assert config.log_level == "INFO"
    
    def test_config_from_json(self):
        """Test loading configuration from JSON file."""
        test_config = {
            "stale_user_days": 180,
            "stale_content_days": 365,
            "log_only": False
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_config))):
            config = Config("test_config.json")
            
            assert config.stale_user_days == 180
            assert config.stale_content_days == 365
            assert config.log_only is False
    
    def test_environment_variable_override(self):
        """Test that environment variables override JSON config."""
        test_config = {
            "stale_user_days": 180,
            "log_level": "DEBUG"
        }
        
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            with patch("builtins.open", mock_open(read_data=json.dumps(test_config))):
                config = Config("test_config.json")
                
                assert config.stale_user_days == 180  # From JSON
                assert config.log_level == "ERROR"     # From env var
    
    def test_required_credentials_validation(self):
        """Test that missing required credentials raise ValueError."""
        with patch("builtins.open", mock_open(read_data="{}")):
            config = Config("test_config.json")
            
            # Should raise ValueError for missing credentials
            with pytest.raises(ValueError, match="TABLEAU_SERVER_URL"):
                _ = config.server_url
                
            with pytest.raises(ValueError, match="TABLEAU_TOKEN_NAME"):
                _ = config.token_name
                
            with pytest.raises(ValueError, match="TABLEAU_TOKEN_SECRET"):
                _ = config.token_secret
    
    def test_valid_credentials(self):
        """Test that valid credentials are returned correctly."""
        test_env = {
            "TABLEAU_SERVER_URL": "https://test-server.com",
            "TABLEAU_TOKEN_NAME": "test-token",
            "TABLEAU_TOKEN_SECRET": "secret-123",
            "TABLEAU_SITE_ID": "test-site"
        }
        
        with patch.dict(os.environ, test_env):
            with patch("builtins.open", mock_open(read_data="{}")):
                config = Config("test_config.json")
                
                assert config.server_url == "https://test-server.com"
                assert config.token_name == "test-token"
                assert config.token_secret == "secret-123"
                assert config.site_id == "test-site"
    
    def test_missing_config_file_handling(self):
        """Test graceful handling of missing config file."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with patch("builtins.print") as mock_print:
                config = Config("nonexistent.json")
                
                # Should use defaults when file is missing
                assert config.stale_user_days == 365
                mock_print.assert_called_once()
                assert "Warning" in mock_print.call_args[0][0]
    
    def test_invalid_json_handling(self):
        """Test graceful handling of invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json {")):
            with patch("builtins.print") as mock_print:
                config = Config("invalid.json")
                
                # Should use defaults when JSON is invalid
                assert config.stale_user_days == 365
                mock_print.assert_called_once()
                assert "Error parsing" in mock_print.call_args[0][0]
    
    def test_log_dir_property(self):
        """Test log directory path construction."""
        with patch("builtins.open", mock_open(read_data='{"log_path": "../test_logs/"}')):
            config = Config("test_config.json")
            
            # Should construct path relative to config file
            assert config.log_dir.endswith("test_logs")
    
    def test_optional_config_properties(self):
        """Test optional configuration properties."""
        test_env = {
            "SMTP_SERVER": "smtp.test.com", 
            "SMTP_PORT": "465",
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_CHANNEL": "#test"
        }
        
        with patch.dict(os.environ, test_env):
            with patch("builtins.open", mock_open(read_data="{}")):
                config = Config("test_config.json")
                
                assert config.smtp_server == "smtp.test.com"
                assert config.smtp_port == 465
                assert config.slack_token == "xoxb-test"
                assert config.slack_channel == "#test"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])