"""Adapter: Crop requirement gateway implementation.

This implementation uses CropRequirementLLMRepository for LLM-based operations.
"""

from typing import Optional, Dict, Any

from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
from agrr_core.adapter.interfaces.llm_client import LLMClient
from agrr_core.adapter.interfaces.crop_requirement_repository_interface import (
    CropRequirementRepositoryInterface,
)
from agrr_core.adapter.repositories.crop_requirement_llm_repository import (
    CropRequirementLLMRepository,
)
from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)


class CropRequirementGatewayImpl(CropRequirementGateway):
    """Gateway that uses CropRequirementLLMRepository for LLM operations."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        crop_requirement_repository: Optional[CropRequirementRepositoryInterface] = None
    ):
        """Initialize with optional LLM client and repository.
        
        Args:
            llm_client: Optional LLM client for LLM operations
            crop_requirement_repository: Optional repository for get operations
        """
        self.llm_client = llm_client
        self.llm_repo = CropRequirementLLMRepository(llm_client) if llm_client else None
        self.crop_requirement_repository = crop_requirement_repository

    async def extract_crop_variety(self, crop_query: str) -> Dict[str, Any]:
        """Step 1: Extract crop name and variety from user input.
        
        Delegates to CropRequirementLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot extract crop variety.")
        return await self.llm_repo.extract_crop_variety(crop_query)

    async def define_growth_stages(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Step 2: Define growth stages for the crop variety.
        
        Delegates to CropRequirementLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot define growth stages.")
        return await self.llm_repo.define_growth_stages(crop_name, variety)

    async def research_stage_requirements(self, crop_name: str, variety: str, 
                                         stage_name: str, stage_description: str) -> Dict[str, Any]:
        """Step 3: Research variety-specific requirements for a specific stage.
        
        Delegates to CropRequirementLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot research stage requirements.")
        return await self.llm_repo.research_stage_requirements(
            crop_name, variety, stage_name, stage_description
        )

    async def extract_crop_economics(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop economic information (area per unit and revenue per area).
        
        Delegates to CropRequirementLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot extract crop economics.")
        return await self.llm_repo.extract_crop_economics(crop_name, variety)

    async def extract_crop_family(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop family (科) information.
        
        Delegates to CropRequirementLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot extract crop family.")
        return await self.llm_repo.extract_crop_family(crop_name, variety)

    async def get(self) -> CropRequirementAggregate:
        """Load crop requirements from configured repository.
        
        Returns:
            CropRequirementAggregate loaded from repository
        """
        if not self.crop_requirement_repository:
            raise ValueError("CropRequirementRepository not provided. Cannot load requirements.")
        
        return await self.crop_requirement_repository.get()


