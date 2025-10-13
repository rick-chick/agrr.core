"""Crop requirement repository interface for adapter layer."""

from abc import ABC, abstractmethod

from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)


class CropRequirementRepositoryInterface(ABC):
    """Abstract interface for crop requirement repository.
    
    Implementations can be:
    - CropRequirementFileRepository: Load from JSON files
    - CropRequirementSQLRepository: Load from SQL database
    - CropRequirementMemoryRepository: Load from in-memory storage
    """
    
    @abstractmethod
    async def get(self) -> CropRequirementAggregate:
        """Get crop requirement from configured source.
        
        Returns:
            CropRequirementAggregate
            
        Note:
            Source configuration (file path, connection string, etc.)
            is injected at repository initialization, not passed here.
        """
        pass

