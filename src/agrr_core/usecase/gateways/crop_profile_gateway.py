"""Gateway interface for crop profiles."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.crop_profile_entity import CropProfile


class CropProfileGateway(ABC):
    """Gateway for crop profile data access and generation.
    
    This gateway abstracts both data retrieval (from files, databases, memory, sessions)
    and profile generation (from templates, LLMs, or other sources).
    """

    @abstractmethod
    async def get_all(self) -> List[CropProfile]:
        """Get all crop profiles from the configured data source.
        
        Data sources may include: files, SQL databases, in-memory storage, sessions, etc.
        The implementation determines the actual source.
        
        Returns:
            List of all CropProfile instances
        """
        pass

    @abstractmethod
    async def generate(self, crop_query: str) -> CropProfile:
        """Generate a crop profile from the given query.
        
        Generation methods may include: templates, LLMs, or other generation strategies.
        The implementation determines the actual generation method.
        
        Args:
            crop_query: Query string describing the crop (e.g., "トマト", "rice Koshihikari")
            
        Returns:
            Generated CropProfile instance
        """
        pass



