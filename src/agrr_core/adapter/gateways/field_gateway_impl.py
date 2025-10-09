"""Field gateway implementation (Adapter layer).

This implementation delegates to a field repository interface.
"""

from typing import Optional

from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.adapter.interfaces.field_repository_interface import FieldRepositoryInterface


class FieldGatewayImpl(FieldGateway):
    """Implementation of FieldGateway using repository interface."""

    def __init__(self, field_repository: FieldRepositoryInterface):
        """Initialize with field repository.
        
        Args:
            field_repository: Repository for field data access
        """
        self.field_repository = field_repository

    async def get(self, field_id: str) -> Optional[Field]:
        """Get field by ID.
        
        Args:
            field_id: Field identifier
            
        Returns:
            Field entity if found, None otherwise
        """
        return await self.field_repository.get(field_id)
