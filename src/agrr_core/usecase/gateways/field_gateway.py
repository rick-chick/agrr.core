"""Field gateway interface (UseCase layer).

This gateway provides access to field data from external sources.
"""

from abc import ABC, abstractmethod
from typing import Optional

from agrr_core.entity.entities.field_entity import Field


class FieldGateway(ABC):
    """Gateway interface for field operations."""

    @abstractmethod
    async def get(self, field_id: str) -> Optional[Field]:
        """Get field by ID.
        
        Args:
            field_id: Field identifier
            
        Returns:
            Field entity if found, None otherwise
        """
        pass
