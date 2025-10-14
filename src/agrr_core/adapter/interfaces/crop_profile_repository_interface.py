"""Crop profile repository interface for adapter layer."""

from abc import ABC, abstractmethod

from agrr_core.entity.entities.crop_profile_entity import CropProfile


class CropProfileRepositoryInterface(ABC):
    """Abstract interface for crop profile repository.
    
    Implementations can be:
    - CropProfileFileRepository: Load from JSON files
    - CropProfileSQLRepository: Load from SQL database
    - CropProfileMemoryRepository: Load from in-memory storage
    """
    
    @abstractmethod
    async def get(self) -> CropProfile:
        """Get crop profile from configured source.
        
        Returns:
            CropProfile
            
        Note:
            Source configuration (file path, connection string, etc.)
            is injected at repository initialization, not passed here.
        """
        pass


