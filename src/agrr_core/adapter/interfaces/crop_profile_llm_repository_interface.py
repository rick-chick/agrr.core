"""Crop profile LLM repository interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class CropProfileLLMRepositoryInterface(ABC):
    """Abstract interface for LLM-based crop profile generation.
    
    Implementations use LLM clients to generate crop profiles dynamically.
    """
    
    @abstractmethod
    async def extract_crop_variety(self, crop_query: str) -> Dict[str, Any]:
        """Step 1: Extract crop name and variety from user input.
        
        Args:
            crop_query: User input containing crop and variety information
            
        Returns:
            Dict containing crop_name and variety
        """
        pass

    @abstractmethod
    async def define_growth_stages(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Step 2: Define growth stages for the crop variety.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing crop_info and growth_stages
        """
        pass

    @abstractmethod
    async def research_stage_requirements(
        self, 
        crop_name: str, 
        variety: str, 
        stage_name: str, 
        stage_description: str
    ) -> Dict[str, Any]:
        """Step 3: Research variety-specific requirements for a specific stage.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            stage_name: Name of the growth stage
            stage_description: Description of the growth stage
            
        Returns:
            Dict containing detailed requirements for the stage
        """
        pass

    @abstractmethod
    async def extract_crop_economics(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop economic information (area per unit and revenue per area).
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing area_per_unit and revenue_per_area
        """
        pass

    @abstractmethod
    async def extract_crop_family(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop family (科) information.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing family information
        """
        pass

