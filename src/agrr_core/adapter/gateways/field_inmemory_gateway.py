"""In-memory field gateway implementation.

This gateway directly implements FieldGateway interface for in-memory field storage.
"""

from typing import Dict, Optional, List

from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.gateways.field_gateway import FieldGateway


class FieldInMemoryGateway(FieldGateway):
    """In-memory implementation of FieldGateway.
    
    Directly implements FieldGateway interface without intermediate layers.
    Stores fields in memory for testing and development.
    """

    def __init__(self):
        """Initialize with empty field storage."""
        self._fields: Dict[str, Field] = {}

    async def get(self, field_id: str) -> Optional[Field]:
        """Get field by ID.
        
        Args:
            field_id: Field identifier
            
        Returns:
            Field entity if found, None otherwise
        """
        return self._fields.get(field_id)
    
    async def get_all(self) -> List[Field]:
        """Get all fields from configured source.
        
        Returns:
            List of Field entities
        """
        return list(self._fields.values())

    async def save(self, field: Field) -> None:
        """Save a field.
        
        Args:
            field: Field entity to save
        """
        self._fields[field.field_id] = field

    async def delete(self, field_id: str) -> bool:
        """Delete a field.
        
        Args:
            field_id: Field identifier
            
        Returns:
            True if deleted, False if not found
        """
        if field_id in self._fields:
            del self._fields[field_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all fields (for testing)."""
        self._fields.clear()

