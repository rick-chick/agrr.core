"""Gateway interface for crop requirements."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)


class CropRequirementGateway(ABC):
    """Gateway for crop requirements (individual LLM calls and repository access)."""

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
            Dict containing crop_info and growth_periods
        """
        pass

    @abstractmethod
    async def research_stage_requirements(self, crop_name: str, variety: str, 
                                         stage_name: str, stage_description: str) -> Dict[str, Any]:
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
            Dict containing family information (family_ja and family_scientific)
        """
        pass

    @abstractmethod
    async def get(self) -> CropRequirementAggregate:
        """Load crop requirements from configured source.
        
        Returns:
            CropRequirementAggregate loaded from configured source
            
        Note:
            Source configuration (file path, etc.) is set at initialization.
        """
        pass


