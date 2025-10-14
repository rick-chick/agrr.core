"""Output port for crafted crop requirements.

This presenter is intentionally thin: it only wraps success/error responses and
does not perform domain-to-dict mapping. The interactor or an adapter should
prepare the response payload (e.g., dict/DTO) before passing to `format_success`.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class CropProfileCraftOutputPort(ABC):
    """Interface for formatting crop requirement crafting responses."""

    @abstractmethod
    def format_error(self, error_message: str, error_code: str = "CROP_REQUIREMENT_ERROR") -> Dict[str, Any]:
        """Format error response."""
        pass

    @abstractmethod
    def format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format success response wrapper."""
        pass


