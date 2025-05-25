"""
Secure configuration management for Tableau governance automation.

This module handles loading configuration from both JSON files and environment variables,
with environment variables taking precedence for sensitive data like credentials.
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Configuration manager that prioritizes environment variables over JSON config."""
    
    def __init__(self, config_file: str = "cleanup_config.json"):
        self.config_file = config_file
        self._config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config_path = os.path.join(os.path.dirname(__file__), self.config_file)
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {config_path} not found, using defaults")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing {config_path}: {e}")
            return {}
    
    def get(self, key: str, default: Any = None, env_var: Optional[str] = None) -> Any:
        """
        Get configuration value with environment variable override.
        
        Args:
            key: Configuration key from JSON file
            default: Default value if not found
            env_var: Environment variable name to check first
        
        Returns:
            Configuration value (env var takes precedence over JSON)
        """
        if env_var and os.getenv(env_var):
            return os.getenv(env_var)
        return self._config_data.get(key, default)
    
    @property
    def server_url(self) -> str:
        """Tableau Server URL - REQUIRED"""
        url = self.get("server_url", env_var="TABLEAU_SERVER_URL")
        if not url or url == "https://your-tableau-server":
            raise ValueError("TABLEAU_SERVER_URL environment variable must be set")
        return url
    
    @property
    def token_name(self) -> str:
        """Tableau PAT name - REQUIRED"""
        token = self.get("token_name", env_var="TABLEAU_TOKEN_NAME")
        if not token or token == "your-pat-name":
            raise ValueError("TABLEAU_TOKEN_NAME environment variable must be set")
        return token
    
    @property
    def token_secret(self) -> str:
        """Tableau PAT secret - REQUIRED"""
        secret = self.get("token_secret", env_var="TABLEAU_TOKEN_SECRET")
        if not secret or secret == "your-pat-secret":
            raise ValueError("TABLEAU_TOKEN_SECRET environment variable must be set")
        return secret
    
    @property
    def site_id(self) -> str:
        """Tableau Site ID (empty string for default site)"""
        return self.get("site_id", "", "TABLEAU_SITE_ID")
    
    @property
    def stale_user_days(self) -> int:
        """Days to consider user inactive"""
        return int(self.get("stale_user_days", 730))
    
    @property
    def stale_content_days(self) -> int:
        """Days to consider content stale"""
        return int(self.get("stale_content_days", 730))
    
    @property
    def stale_site_days(self) -> int:
        """Days to consider site stale"""
        return int(self.get("stale_site_days", 730))
    
    @property
    def log_only(self) -> bool:
        """Whether to run in log-only mode (no deletions)"""
        return bool(self.get("log_only", True))
    
    @property
    def log_dir(self) -> str:
        """Directory for log output"""
        log_path = self.get("log_path", "../logs/")
        return os.path.join(os.path.dirname(__file__), log_path)
    
    @property
    def log_level(self) -> str:
        """Logging level"""
        return self.get("log_level", "INFO", "LOG_LEVEL")
    
    # Email configuration
    @property
    def smtp_server(self) -> Optional[str]:
        return self.get("smtp_server", env_var="SMTP_SERVER")
    
    @property
    def smtp_port(self) -> int:
        return int(self.get("smtp_port", 587, "SMTP_PORT"))
    
    @property
    def email_from(self) -> Optional[str]:
        return self.get("email_from", env_var="EMAIL_FROM")
    
    @property
    def email_to(self) -> Optional[str]:
        return self.get("email_to", env_var="EMAIL_TO")
    
    # Slack configuration
    @property
    def slack_token(self) -> Optional[str]:
        return self.get("slack_token", env_var="SLACK_BOT_TOKEN")
    
    @property
    def slack_channel(self) -> Optional[str]:
        return self.get("slack_channel", env_var="SLACK_CHANNEL")

# Global config instance
config = Config()