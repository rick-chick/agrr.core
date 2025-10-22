"""Daemon monitoring and health check system."""

import time
import threading
import subprocess
import socket
import os
from typing import Optional, Callable
from datetime import datetime, timedelta

from ..logging.agrr_logger import get_logger, DaemonLogger
from ..notifications.error_notifier import get_notifier


class DaemonHealthChecker:
    """Daemon health monitoring system."""
    
    def __init__(self, 
                 socket_path: str = '/tmp/agrr.sock',
                 pid_file: str = '/tmp/agrr.pid',
                 check_interval: int = 60,
                 response_timeout: float = 5.0):
        """
        Initialize daemon health checker.
        
        Args:
            socket_path: Path to daemon socket
            pid_file: Path to daemon PID file
            check_interval: Health check interval in seconds
            response_timeout: Response timeout in seconds
        """
        self.socket_path = socket_path
        self.pid_file = pid_file
        self.check_interval = check_interval
        self.response_timeout = response_timeout
        self.logger = get_logger()
        self.notifier = get_notifier()
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_check_time: Optional[datetime] = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
    
    def start_monitoring(self):
        """Start daemon monitoring in background thread."""
        if self.monitoring:
            self.logger.warning("Monitoring is already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info(f"Daemon monitoring started", interval=f"{self.check_interval}s")
    
    def stop_monitoring(self):
        """Stop daemon monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Daemon monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                self._perform_health_check()
                self.consecutive_failures = 0  # Reset on success
            except Exception as e:
                self.consecutive_failures += 1
                self.logger.error(f"Health check failed", error=str(e), 
                                consecutive_failures=self.consecutive_failures)
                
                if self.consecutive_failures >= self.max_consecutive_failures:
                    self.logger.critical("Too many consecutive failures, triggering alert")
                    self.notifier.notify_daemon_down()
            
            time.sleep(self.check_interval)
    
    def _perform_health_check(self):
        """Perform single health check."""
        start_time = time.time()
        
        # Check if socket exists
        if not os.path.exists(self.socket_path):
            raise Exception("Daemon socket not found")
        
        # Check socket connectivity
        response_time = self._test_socket_connection()
        
        # Check PID file
        pid = self._get_daemon_pid()
        
        # Log health status
        self.logger.info(f"Health check passed", 
                        response_time=f"{response_time:.2f}s", 
                        pid=pid)
        
        self.last_check_time = datetime.now()
    
    def _test_socket_connection(self) -> float:
        """Test socket connection and return response time."""
        start_time = time.time()
        
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(self.response_timeout)
            sock.connect(self.socket_path)
            sock.close()
            
            response_time = time.time() - start_time
            return response_time
            
        except (ConnectionRefusedError, FileNotFoundError, socket.timeout) as e:
            raise Exception(f"Socket connection failed: {e}")
    
    def _get_daemon_pid(self) -> Optional[int]:
        """Get daemon PID from PID file."""
        if not os.path.exists(self.pid_file):
            return None
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            return pid
        except (ValueError, FileNotFoundError):
            return None
    
    def is_daemon_running(self) -> bool:
        """Check if daemon is currently running."""
        try:
            self._perform_health_check()
            return True
        except Exception:
            return False
    
    def get_daemon_status(self) -> dict:
        """Get comprehensive daemon status."""
        status = {
            "running": False,
            "socket_exists": os.path.exists(self.socket_path),
            "pid_file_exists": os.path.exists(self.pid_file),
            "pid": self._get_daemon_pid(),
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "consecutive_failures": self.consecutive_failures
        }
        
        if status["socket_exists"] and status["pid_file_exists"]:
            try:
                response_time = self._test_socket_connection()
                status["running"] = True
                status["response_time"] = response_time
            except Exception as e:
                status["error"] = str(e)
        
        return status


class DaemonAutoRecovery:
    """Automatic daemon recovery system."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 retry_interval: int = 30,
                 recovery_command: str = "agrr daemon restart"):
        """
        Initialize auto recovery system.
        
        Args:
            max_retries: Maximum number of recovery attempts
            retry_interval: Interval between retry attempts in seconds
            recovery_command: Command to run for recovery
        """
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.recovery_command = recovery_command.split()
        self.logger = get_logger()
        self.notifier = get_notifier()
        self.recovery_in_progress = False
    
    def attempt_recovery(self) -> bool:
        """Attempt to recover daemon."""
        if self.recovery_in_progress:
            self.logger.warning("Recovery already in progress")
            return False
        
        self.recovery_in_progress = True
        self.logger.info("Starting daemon recovery")
        
        try:
            for attempt in range(1, self.max_retries + 1):
                self.logger.info(f"Recovery attempt {attempt}/{self.max_retries}")
                
                try:
                    # Run recovery command
                    result = subprocess.run(
                        self.recovery_command,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        # Wait a bit for daemon to start
                        time.sleep(2)
                        
                        # Verify daemon is running
                        if self._verify_daemon_running():
                            self.logger.info(f"Daemon recovery successful on attempt {attempt}")
                            return True
                        else:
                            self.logger.warning(f"Recovery command succeeded but daemon not running")
                    else:
                        self.logger.error(f"Recovery command failed", 
                                        returncode=result.returncode,
                                        stderr=result.stderr)
                
                except subprocess.TimeoutExpired:
                    self.logger.error(f"Recovery command timed out on attempt {attempt}")
                except Exception as e:
                    self.logger.error(f"Recovery attempt {attempt} failed", error=str(e))
                
                if attempt < self.max_retries:
                    self.logger.info(f"Waiting {self.retry_interval}s before next attempt")
                    time.sleep(self.retry_interval)
            
            # All attempts failed
            self.logger.critical("All recovery attempts failed")
            self.notifier.notify_daemon_recovery_failed(self.max_retries)
            return False
            
        finally:
            self.recovery_in_progress = False
    
    def _verify_daemon_running(self) -> bool:
        """Verify that daemon is actually running."""
        try:
            checker = DaemonHealthChecker()
            return checker.is_daemon_running()
        except Exception:
            return False


class DaemonMonitor:
    """Comprehensive daemon monitoring system."""
    
    def __init__(self, config: dict = None):
        """Initialize daemon monitor."""
        self.config = config or {}
        self.health_checker = DaemonHealthChecker(
            check_interval=self.config.get('check_interval', 60),
            response_timeout=self.config.get('response_timeout', 5.0)
        )
        self.auto_recovery = DaemonAutoRecovery(
            max_retries=self.config.get('max_retries', 3),
            retry_interval=self.config.get('retry_interval', 30)
        )
        self.logger = get_logger()
        self.monitoring = False
    
    def start(self):
        """Start comprehensive monitoring."""
        if self.monitoring:
            self.logger.warning("Monitor is already running")
            return
        
        self.monitoring = True
        self.health_checker.start_monitoring()
        self.logger.info("Daemon monitor started")
    
    def stop(self):
        """Stop monitoring."""
        self.monitoring = False
        self.health_checker.stop_monitoring()
        self.logger.info("Daemon monitor stopped")
    
    def get_status(self) -> dict:
        """Get current daemon status."""
        return self.health_checker.get_daemon_status()
    
    def force_recovery(self) -> bool:
        """Force daemon recovery."""
        return self.auto_recovery.attempt_recovery()


# Global monitor instance
_global_monitor: Optional[DaemonMonitor] = None


def get_monitor() -> DaemonMonitor:
    """Get global monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = DaemonMonitor()
    return _global_monitor


def setup_monitoring(config: dict) -> DaemonMonitor:
    """Setup monitoring system from config."""
    global _global_monitor
    _global_monitor = DaemonMonitor(config)
    return _global_monitor
