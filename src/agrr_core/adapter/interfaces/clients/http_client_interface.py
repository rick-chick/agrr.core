"""HTTP client interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class HttpClientInterface(ABC):
    """Interface for basic HTTP operations."""
    
    @abstractmethod
    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        pass
    
    @abstractmethod
    def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        pass

