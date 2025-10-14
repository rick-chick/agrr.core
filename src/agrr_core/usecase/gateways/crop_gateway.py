"""Gateway interface for crops."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)


class CropGateway(ABC):
    """Gateway for crop data access."""

    @abstractmethod
    async def get_all(self) -> List[CropRequirementAggregate]:
        """Get all crops.
        
        Returns:
            List of all CropRequirementAggregate
        """
        pass

