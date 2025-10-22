"""Error notification system for AGRR application."""

import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime

from ..logging.agrr_logger import get_logger


class NotificationChannel:
    """Base class for notification channels."""
    
    def send(self, title: str, message: str, details: Optional[Dict] = None):
        """Send notification."""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""
    
    def __init__(self, 
                 smtp_server: str,
                 smtp_port: int,
                 username: str,
                 password: str,
                 from_email: str,
                 to_emails: List[str]):
        """Initialize email notification channel."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.logger = get_logger()
    
    def send(self, title: str, message: str, details: Optional[Dict] = None):
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"AGRR Alert: {title}"
            
            body = f"""
AGRR System Alert

Title: {title}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Message: {message}
"""
            
            if details:
                body += f"\nDetails:\n{json.dumps(details, indent=2)}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent", title=title, recipients=len(self.to_emails))
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification", error=str(e))


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""
    
    def __init__(self, webhook_url: str):
        """Initialize Slack notification channel."""
        self.webhook_url = webhook_url
        self.logger = get_logger()
    
    def send(self, title: str, message: str, details: Optional[Dict] = None):
        """Send Slack notification."""
        try:
            payload = {
                "text": f"🚨 AGRR Alert: {title}",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "title": "Message",
                                "value": message,
                                "short": False
                            },
                            {
                                "title": "Time",
                                "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            if details:
                payload["attachments"][0]["fields"].append({
                    "title": "Details",
                    "value": f"```{json.dumps(details, indent=2)}```",
                    "short": False
                })
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Slack notification sent", title=title)
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification", error=str(e))


class ErrorNotifier:
    """Error notification system."""
    
    def __init__(self):
        """Initialize error notifier."""
        self.channels: List[NotificationChannel] = []
        self.logger = get_logger()
    
    def add_email_channel(self, 
                         smtp_server: str,
                         smtp_port: int,
                         username: str,
                         password: str,
                         from_email: str,
                         to_emails: List[str]):
        """Add email notification channel."""
        channel = EmailNotificationChannel(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            from_email=from_email,
            to_emails=to_emails
        )
        self.channels.append(channel)
        self.logger.info(f"Email notification channel added", recipients=len(to_emails))
    
    def add_slack_channel(self, webhook_url: str):
        """Add Slack notification channel."""
        channel = SlackNotificationChannel(webhook_url)
        self.channels.append(channel)
        self.logger.info("Slack notification channel added")
    
    def notify_error(self, 
                    error_type: str, 
                    message: str, 
                    details: Optional[Dict] = None):
        """Send error notification to all channels."""
        self.logger.error(f"Error notification triggered", error_type=error_type, msg=message)
        
        for channel in self.channels:
            try:
                channel.send(error_type, message, details)
            except Exception as e:
                self.logger.error(f"Failed to send notification via channel", 
                                channel=type(channel).__name__, error=str(e))
    
    def notify_daemon_down(self, pid: Optional[int] = None):
        """Notify that daemon is down."""
        message = f"AGRR daemon is not running"
        if pid:
            message += f" (PID: {pid})"
        
        self.notify_error("DAEMON_DOWN", message, {
            "timestamp": datetime.now().isoformat(),
            "pid": pid
        })
    
    def notify_daemon_recovery_failed(self, attempts: int):
        """Notify that daemon recovery failed."""
        self.notify_error("DAEMON_RECOVERY_FAILED", 
                         f"Failed to recover daemon after {attempts} attempts", {
            "timestamp": datetime.now().isoformat(),
            "attempts": attempts
        })
    
    def notify_prediction_error(self, model: str, error: str):
        """Notify prediction error."""
        self.notify_error("PREDICTION_ERROR", 
                         f"Prediction failed with {model} model", {
            "model": model,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })


# Global notifier instance
_global_notifier: Optional[ErrorNotifier] = None


def get_notifier() -> ErrorNotifier:
    """Get global notifier instance."""
    global _global_notifier
    if _global_notifier is None:
        _global_notifier = ErrorNotifier()
    return _global_notifier


def setup_notifications(config: Dict) -> ErrorNotifier:
    """Setup notification system from config."""
    notifier = ErrorNotifier()
    
    # Email configuration
    if config.get('email', {}).get('enabled', False):
        email_config = config['email']
        notifier.add_email_channel(
            smtp_server=email_config['smtp_server'],
            smtp_port=email_config['smtp_port'],
            username=email_config['username'],
            password=email_config['password'],
            from_email=email_config['from_email'],
            to_emails=email_config['to_emails']
        )
    
    # Slack configuration
    if config.get('slack', {}).get('enabled', False):
        slack_config = config['slack']
        notifier.add_slack_channel(slack_config['webhook_url'])
    
    return notifier
