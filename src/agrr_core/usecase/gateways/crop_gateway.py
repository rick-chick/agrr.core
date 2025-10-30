"""Gateway interface for crops."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.crop_entity import Crop

class CropGateway(ABC):
    """Gateway for crop data access."""

    @abstractmethod
    def get_all(self) -> List[Crop]:
        """Get all crops.
        
        Returns:
            List of all Crop entities
        """
        pass

