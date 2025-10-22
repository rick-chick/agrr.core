"""Configuration loader for AGRR application."""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Configuration loader with environment variable support."""
    
    def __init__(self, config_file: str = "agrr_config.yaml"):
        """Initialize config loader."""
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables."""
        # Load from file if exists
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            # Use default configuration
            self.config = self._get_default_config()
        
        # Override with environment variables
        self._apply_env_overrides()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "logging": {
                "enabled": True,
                "log_file": "/tmp/agrr.log",
                "daemon_log_file": "/tmp/agrr_daemon.log",
                "max_size": "10MB",
                "backup_count": 5,
                "level": "INFO"
            },
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "agrr-system@example.com",
                    "to_emails": []
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": ""
                }
            },
            "daemon": {
                "health_check": {
                    "enabled": True,
                    "check_interval": 60,
                    "response_timeout": 5.0,
                    "max_consecutive_failures": 3
                },
                "auto_recovery": {
                    "enabled": True,
                    "max_retries": 3,
                    "retry_interval": 30,
                    "recovery_command": "agrr daemon restart"
                }
            },
            "paths": {
                "socket_path": "/tmp/agrr.sock",
                "pid_file": "/tmp/agrr.pid"
            }
        }
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        env_mappings = {
            "AGRR_LOG_LEVEL": ("logging", "level"),
            "AGRR_LOG_FILE": ("logging", "log_file"),
            "AGRR_EMAIL_ENABLED": ("notifications", "email", "enabled"),
            "AGRR_EMAIL_SMTP_SERVER": ("notifications", "email", "smtp_server"),
            "AGRR_EMAIL_SMTP_PORT": ("notifications", "email", "smtp_port"),
            "AGRR_EMAIL_USERNAME": ("notifications", "email", "username"),
            "AGRR_EMAIL_PASSWORD": ("notifications", "email", "password"),
            "AGRR_EMAIL_FROM": ("notifications", "email", "from_email"),
            "AGRR_EMAIL_TO": ("notifications", "email", "to_emails"),
            "AGRR_SLACK_ENABLED": ("notifications", "slack", "enabled"),
            "AGRR_SLACK_WEBHOOK": ("notifications", "slack", "webhook_url"),
            "AGRR_SOCKET_PATH": ("paths", "socket_path"),
            "AGRR_PID_FILE": ("paths", "pid_file")
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(self.config, config_path, value)
    
    def _set_nested_value(self, config: Dict, path: tuple, value: Any):
        """Set nested configuration value."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        if path[-1] in ["smtp_port", "check_interval", "retry_interval", "max_retries", "max_consecutive_failures"]:
            value = int(value)
        elif path[-1] in ["response_timeout"]:
            value = float(value)
        elif path[-1] in ["enabled"]:
            value = value.lower() in ("true", "1", "yes", "on")
        elif path[-1] == "to_emails":
            value = [email.strip() for email in value.split(",")]
        
        current[path[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split(".")
        current = self.config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get("logging", {})
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration."""
        return self.get("notifications", {})
    
    def get_daemon_config(self) -> Dict[str, Any]:
        """Get daemon configuration."""
        return self.get("daemon", {})
    
    def get_paths_config(self) -> Dict[str, Any]:
        """Get paths configuration."""
        return self.get("paths", {})
    
    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled."""
        return self.get("logging.enabled", True)
    
    def is_email_enabled(self) -> bool:
        """Check if email notifications are enabled."""
        return self.get("notifications.email.enabled", False)
    
    def is_slack_enabled(self) -> bool:
        """Check if Slack notifications are enabled."""
        return self.get("notifications.slack.enabled", False)
    
    def is_auto_recovery_enabled(self) -> bool:
        """Check if auto recovery is enabled."""
        return self.get("daemon.auto_recovery.enabled", True)
    
    def is_health_check_enabled(self) -> bool:
        """Check if health check is enabled."""
        return self.get("daemon.health_check.enabled", True)


# Global config instance
_global_config: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """Get global config instance."""
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader()
    return _global_config


def load_config(config_file: str = "agrr_config.yaml") -> ConfigLoader:
    """Load configuration from file."""
    global _global_config
    _global_config = ConfigLoader(config_file)
    return _global_config
