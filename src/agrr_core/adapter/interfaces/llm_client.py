"""LLM client interface (adapter layer).

Defines the minimal async interface for Large Language Model clients used by
adapters/gateways. Concrete implementations should live under the adapter or
infrastructure layer and implement this contract.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMClient(ABC):
    """Abstract client for structured extraction with an LLM (provider-agnostic).

    The client is responsible for converting a provider-agnostic "structure"
    description into a provider-specific schema (e.g., JSON Schema) under the hood.
    """

    @abstractmethod
    async def struct(self, query: str, structure: Dict[str, Any], instruction: Optional[str] = None) -> Dict[str, Any]:
        """Return structured data following the provided structure description.

        Args:
            query: Free-form input for the LLM (domain-agnostic text).
            structure: Provider-agnostic nested structure description (keys and nesting),
                      e.g., {"stages": [{"name": None, "temperature": {"base_temperature": None}}]}.
            instruction: Optional system instruction to guide behavior.
        Returns:
            Dict[str, Any]: Structured object matching the described structure (best-effort).
        """
        raise NotImplementedError


