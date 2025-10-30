"""In-memory crop profile gateway implementation.

This gateway directly implements CropProfileGateway interface for in-memory crop profile storage.
"""

from typing import Dict, List

from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway

class CropProfileInMemoryGateway(CropProfileGateway):
    """In-memory implementation of CropProfileGateway.
    
    Directly implements CropProfileGateway interface without intermediate layers.
    Used primarily for testing and temporary storage.
    """
    
    def __init__(self, profiles: List[CropProfile] = None):
        """Initialize in-memory gateway.
        
        Args:
            profiles: Optional list of initial crop profiles
        """
        self._profiles: Dict[str, CropProfile] = {}
        
        if profiles:
            for profile in profiles:
                key = self._make_key(profile)
                self._profiles[key] = profile
    
    def _make_key(self, profile: CropProfile) -> str:
        """Create key from crop profile."""
        crop_id = profile.crop.crop_id
        variety = profile.crop.variety
        return f"{crop_id}:{variety}" if variety else crop_id
    
    def get(self) -> CropProfile:
        """Get the most recently saved crop profile.
        
        Returns:
            CropProfile instance (most recently saved)
            
        Raises:
            ValueError: If no profile is saved
            
        Note:
            If multiple profiles are saved, returns the last one saved.
            This is useful for sequential save/get operations in optimization workflows.
        """
        if len(self._profiles) == 0:
            raise ValueError("No crop profile saved. Call save() first.")
        
        # Return the most recently saved profile (last item in dict)
        return list(self._profiles.values())[-1]
    
    def get_all(self) -> List[CropProfile]:
        """Get all crop profiles.
        
        Returns:
            List of all CropProfile instances
        """
        return list(self._profiles.values())

    def save(self, profile: CropProfile) -> None:
        """Save a crop profile.
        
        Args:
            profile: CropProfile to save
        """
        key = self._make_key(profile)
        self._profiles[key] = profile
    
    def delete(self) -> None:
        """Delete current crop profile.
        
        Note: In-memory implementation clears all profiles.
        """
        self._profiles.clear()
    
    def get_by_crop_id(self, crop_id: str, variety: str = None) -> CropProfile:
        """Get crop profile by crop_id and variety.
        
        Args:
            crop_id: Crop identifier
            variety: Optional variety name
            
        Returns:
            CropProfile instance
            
        Raises:
            KeyError: If profile not found
        """
        key = f"{crop_id}:{variety}" if variety else crop_id
        return self._profiles[key]
    
    # LLM operations not supported
    
    def generate(self, crop_query: str) -> CropProfile:
        """Generate a crop profile.
        
        Raises:
            NotImplementedError: In-memory gateway doesn't support generation
        """
        raise NotImplementedError(
            "Profile generation not supported by in-memory gateway. "
            "Use CropProfileLLMGateway instead."
        )
    
    def extract_crop_variety(self, crop_query: str) -> Dict:
        """Extract crop variety.
        
        Raises:
            NotImplementedError: In-memory gateway doesn't support LLM operations
        """
        raise NotImplementedError(
            "LLM operations not supported by in-memory gateway."
        )
    
    def define_growth_stages(self, crop_name: str, variety: str) -> Dict:
        """Define growth stages.
        
        Raises:
            NotImplementedError: In-memory gateway doesn't support LLM operations
        """
        raise NotImplementedError(
            "LLM operations not supported by in-memory gateway."
        )
    
    def research_stage_requirements(
        self, 
        crop_name: str, 
        variety: str, 
        stage_name: str, 
        stage_description: str
    ) -> Dict:
        """Research stage requirements.
        
        Raises:
            NotImplementedError: In-memory gateway doesn't support LLM operations
        """
        raise NotImplementedError(
            "LLM operations not supported by in-memory gateway."
        )
    
    def extract_crop_economics(self, crop_name: str, variety: str) -> Dict:
        """Extract crop economics.
        
        Raises:
            NotImplementedError: In-memory gateway doesn't support LLM operations
        """
        raise NotImplementedError(
            "LLM operations not supported by in-memory gateway."
        )
    
    def extract_crop_family(self, crop_name: str, variety: str) -> Dict:
        """Extract crop family.
        
        Raises:
            NotImplementedError: In-memory gateway doesn't support LLM operations
        """
        raise NotImplementedError(
            "LLM operations not supported by in-memory gateway."
        )

