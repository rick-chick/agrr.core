"""Client interfaces for external connections."""

from .http_client_interface import HttpClientInterface
from .llm_client_interface import LLMClientInterface

__all__ = [
    'HttpClientInterface',
    'LLMClientInterface',
]

