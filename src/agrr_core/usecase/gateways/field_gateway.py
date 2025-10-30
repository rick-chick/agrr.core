"""Field gateway interface (UseCase layer).

This gateway provides access to field data from external sources.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from agrr_core.entity.entities.field_entity import Field

class FieldGateway(ABC):
    """Gateway interface for field operations."""

    @abstractmethod
    def get(self, field_id: str) -> Optional[Field]:
        """Get field by ID.
        
        Args:
            field_id: Field identifier
            
        Returns:
            Field entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[Field]:
        """Get all fields from configured source.
        
        Returns:
            List of Field entities
            
        Note:
            Source configuration is provided at initialization, not here.
        """
        pass
