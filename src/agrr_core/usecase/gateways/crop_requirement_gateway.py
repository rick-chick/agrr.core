"""Gateway interface for crafting crop stage requirements (LLM-backed)."""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any

from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
    CropRequirementCraftRequestDTO,
)


class CropRequirementGateway(ABC):
    """Gateway for inferring crop requirements from external services/LLMs."""

    @abstractmethod
    async def craft(self, request: CropRequirementCraftRequestDTO) -> CropRequirementAggregate:
        """Infer and assemble a CropRequirementAggregate from the request."""
        pass

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
    async def get(self, file_path: str) -> CropRequirementAggregate:
        """Load crop requirements from file.
        
        Args:
            file_path: Path to crop requirement JSON file
            
        Returns:
            CropRequirementAggregate loaded from file
        """
        pass


