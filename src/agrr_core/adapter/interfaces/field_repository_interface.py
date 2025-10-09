"""Field repository interface (Adapter layer).

This interface defines the contract for field data repositories.
"""

from abc import ABC, abstractmethod
from typing import Optional

from agrr_core.entity.entities.field_entity import Field


class FieldRepositoryInterface(ABC):
    """Interface for field repository implementations."""

    @abstractmethod
    async def get(self, field_id: str) -> Optional[Field]:
        """Get field by ID.
        
        Args:
            field_id: Field identifier
            
        Returns:
            Field entity if found, None otherwise
        """
        pass
