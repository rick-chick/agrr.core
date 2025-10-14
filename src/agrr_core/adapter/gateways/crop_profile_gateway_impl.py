"""Adapter: Crop profile gateway implementation.

This implementation supports both data retrieval and profile generation:
- Data retrieval: From files, databases, or in-memory storage via repositories
- Profile generation: Via LLM or other generation methods

The gateway delegates to appropriate repositories based on the operation.
"""

from typing import Optional, Dict, Any, List

from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.adapter.interfaces.llm_client import LLMClient
from agrr_core.adapter.repositories.crop_profile_llm_repository import (
    CropProfileLLMRepository,
)


class CropProfileGatewayImpl(CropProfileGateway):
    """Gateway implementation for crop profiles.
    
    Supports:
    - get_all(): Retrieve all profiles from a repository (file, DB, memory, etc.)
    - generate(): Generate a profile using LLM or templates
    - Individual LLM operations: For step-by-step profile construction
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        profile_repository = None
    ):
        """Initialize with optional LLM client and repository.
        
        Args:
            llm_client: Optional LLM client for generation operations
            profile_repository: Optional repository for data retrieval operations
                Can be CropProfileFileRepository, InMemoryCropProfileRepository, etc.
        """
        self.llm_client = llm_client
        self.llm_repo = CropProfileLLMRepository(llm_client) if llm_client else None
        self.profile_repository = profile_repository

    async def get_all(self) -> List[CropProfile]:
        """Get all crop profiles from the configured repository.
        
        Returns:
            List of all CropProfile instances
            
        Raises:
            ValueError: If no repository is configured
        """
        if not self.profile_repository:
            raise ValueError("Profile repository not provided. Cannot retrieve profiles.")
        
        if not hasattr(self.profile_repository, 'get_all'):
            raise ValueError("Profile repository does not support get_all()")
        
        return await self.profile_repository.get_all()

    async def generate(self, crop_query: str) -> CropProfile:
        """Generate a crop profile from the given query.
        
        This is a convenience method that orchestrates the multi-step LLM process.
        For more granular control, use the individual LLM methods below.
        
        Args:
            crop_query: Query string describing the crop (e.g., "トマト", "rice Koshihikari")
            
        Returns:
            Generated CropProfile instance
            
        Raises:
            ValueError: If LLM client is not configured
            NotImplementedError: This method should be implemented by interactors
        """
        # Note: Full profile generation is complex and typically handled by interactors
        # that orchestrate multiple LLM calls. This gateway provides the individual
        # operations needed for that orchestration.
        raise NotImplementedError(
            "Full profile generation should be handled by an interactor. "
            "Use extract_crop_variety, define_growth_stages, and research_stage_requirements "
            "for step-by-step generation."
        )

    # Individual LLM operations for step-by-step profile construction
    # These are called by interactors to build profiles incrementally

    async def extract_crop_variety(self, crop_query: str) -> Dict[str, Any]:
        """Step 1: Extract crop name and variety from user input.
        
        Delegates to CropProfileLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot extract crop variety.")
        return await self.llm_repo.extract_crop_variety(crop_query)

    async def define_growth_stages(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Step 2: Define growth stages for the crop variety.
        
        Delegates to CropProfileLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot define growth stages.")
        return await self.llm_repo.define_growth_stages(crop_name, variety)

    async def research_stage_requirements(self, crop_name: str, variety: str, 
                                         stage_name: str, stage_description: str) -> Dict[str, Any]:
        """Step 3: Research variety-specific requirements for a specific stage.
        
        Delegates to CropProfileLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot research stage requirements.")
        return await self.llm_repo.research_stage_requirements(
            crop_name, variety, stage_name, stage_description
        )

    async def extract_crop_economics(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop economic information (area per unit and revenue per area).
        
        Delegates to CropProfileLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot extract crop economics.")
        return await self.llm_repo.extract_crop_economics(crop_name, variety)

    async def extract_crop_family(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop family (科) information.
        
        Delegates to CropProfileLLMRepository.
        """
        if not self.llm_repo:
            raise ValueError("LLM client not provided. Cannot extract crop family.")
        return await self.llm_repo.extract_crop_family(crop_name, variety)

    # Additional repository operations

    async def get(self) -> CropProfile:
        """Load crop profile from configured repository.
        
        Returns:
            CropProfile loaded from repository
        """
        if not self.profile_repository:
            raise ValueError("Profile repository not provided. Cannot load profile.")
        
        if not hasattr(self.profile_repository, 'get'):
            raise ValueError("Profile repository does not support get()")
        
        return await self.profile_repository.get()
    
    async def save(self, crop_profile: CropProfile) -> None:
        """Save a crop profile.
        
        Args:
            crop_profile: CropProfile to save
        """
        if not self.profile_repository:
            raise ValueError("Profile repository not provided. Cannot save profile.")
        
        if hasattr(self.profile_repository, 'save'):
            await self.profile_repository.save(crop_profile)
    
    async def delete(self) -> None:
        """Delete current crop profile."""
        if not self.profile_repository:
            raise ValueError("Profile repository not provided. Cannot delete profile.")
        
        if hasattr(self.profile_repository, 'delete'):
            await self.profile_repository.delete()



