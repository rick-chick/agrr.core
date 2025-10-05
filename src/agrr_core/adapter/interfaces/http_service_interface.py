"""HTTP service interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class HttpServiceInterface(ABC):
    """Interface for basic HTTP operations."""
    
    @abstractmethod
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        pass
    
    @abstractmethod
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        pass
