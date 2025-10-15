"""Framework clients for external system connections."""

from .http_client import HttpClient
from .llm_client import LLMClient

__all__ = [
    'HttpClient',
    'LLMClient',
]

