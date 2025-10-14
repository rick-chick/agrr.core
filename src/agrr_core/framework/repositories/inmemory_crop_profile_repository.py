"""In-memory repository for crop profiles (for testing)."""

from typing import Dict, List
from agrr_core.entity.entities.crop_profile_entity import CropProfile


class InMemoryCropProfileRepository:
    """In-memory implementation for crop profile storage.
    
    Used primarily for testing and temporary storage.
    """
    
    def __init__(self, profiles: List[CropProfile] = None):
        """Initialize in-memory repository.
        
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
    
    async def get(self) -> CropProfile:
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
    
    async def get_all(self) -> List[CropProfile]:
        """Get all crop profiles.
        
        Returns:
            List of all CropProfile instances
        """
        return list(self._profiles.values())

    async def save(self, profile: CropProfile) -> None:
        """Save a crop profile.
        
        Args:
            profile: CropProfile to save
        """
        key = self._make_key(profile)
        self._profiles[key] = profile
    
    async def get_by_crop_id(self, crop_id: str, variety: str = None) -> CropProfile:
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



