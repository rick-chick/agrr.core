"""AGRR logging system with file rotation and structured logging."""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class AgrrLogger:
    """Enhanced logging system for AGRR application."""
    
    def __init__(self, 
                 log_file: str = '/tmp/agrr.log',
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 log_level: str = 'INFO'):
        """
        Initialize AGRR logger.
        
        Args:
            log_file: Path to log file
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_file = log_file
        self.logger = logging.getLogger('agrr')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create log directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with additional context."""
        if kwargs:
            context = ', '.join(f'{k}={v}' for k, v in kwargs.items())
            return f"{message} ({context})"
        return message


class DaemonLogger:
    """Specialized logger for daemon operations."""
    
    def __init__(self, log_file: str = '/tmp/agrr_daemon.log'):
        """Initialize daemon logger."""
        self.logger = AgrrLogger(log_file)
        self.start_time = datetime.now()
    
    def daemon_started(self, pid: int, socket_path: str):
        """Log daemon startup."""
        self.logger.info(f"Daemon started", pid=pid, socket=socket_path)
    
    def daemon_stopped(self, pid: int):
        """Log daemon shutdown."""
        uptime = datetime.now() - self.start_time
        self.logger.info(f"Daemon stopped", pid=pid, uptime=str(uptime))
    
    def request_received(self, command: str, client_info: str = ""):
        """Log incoming request."""
        self.logger.debug(f"Request received", command=command, client=client_info)
    
    def request_completed(self, command: str, duration: float, exit_code: int):
        """Log request completion."""
        self.logger.info(f"Request completed", 
                        command=command, 
                        duration=f"{duration:.2f}s", 
                        exit_code=exit_code)
    
    def request_failed(self, command: str, error: str, duration: float):
        """Log request failure."""
        self.logger.error(f"Request failed", 
                         command=command, 
                         error=error, 
                         duration=f"{duration:.2f}s")
    
    def health_check(self, status: str, response_time: float = None):
        """Log health check results."""
        if response_time:
            self.logger.info(f"Health check", status=status, response_time=f"{response_time:.2f}s")
        else:
            self.logger.info(f"Health check", status=status)


# Global logger instance
_global_logger: Optional[AgrrLogger] = None


def get_logger() -> AgrrLogger:
    """Get global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AgrrLogger()
    return _global_logger


def setup_logging(log_file: str = '/tmp/agrr.log', 
                  log_level: str = 'INFO') -> AgrrLogger:
    """Setup global logging configuration."""
    global _global_logger
    _global_logger = AgrrLogger(log_file=log_file, log_level=log_level)
    return _global_logger
