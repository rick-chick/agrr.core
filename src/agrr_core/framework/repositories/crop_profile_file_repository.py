"""File-based implementation of CropProfileRepository."""

import json
from typing import List, Dict, Optional
from agrr_core.entity import (
    Crop,
    GrowthStage,
    TemperatureProfile,
    SunshineProfile,
    ThermalRequirement,
    StageRequirement,
)
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.adapter.interfaces.crop_profile_repository_interface import (
    CropProfileRepositoryInterface,
)
from agrr_core.adapter.interfaces.file_repository_interface import FileRepositoryInterface


class CropProfileFileRepository(CropProfileRepositoryInterface):
    """File-based implementation of CropProfileRepository.
    
    This repository can handle both:
    - Single crop profile files (one profile per file)
    - Collection files (multiple profiles in one file)
    
    File path is configured at initialization.
    """
    
    def __init__(self, file_repository: FileRepositoryInterface, file_path: str = ""):
        """Initialize crop profile file repository.
        
        Args:
            file_repository: File repository for file I/O operations (Framework layer)
            file_path: File path to crop profile JSON file (optional, can be provided to get)
        """
        self.file_repository = file_repository
        self.file_path = file_path
        self._cache: Optional[Dict[str, CropProfile]] = None
    
    async def get(self) -> CropProfile:
        """Get crop profile from configured file.
        
        Returns:
            CropProfile loaded from file
        """
        if not self.file_path:
            raise ValueError("file_path not set. Cannot load crop profile.")
        
        # Read file using repository
        content = await self.file_repository.read(self.file_path)
        
        # Parse JSON
        data = json.loads(content)
        
        # Check if this is a collection file or single profile file
        if 'crops' in data:
            # Collection file - get first crop (for backward compatibility)
            return self._parse_crop_data(data['crops'][0])
        else:
            # Single profile file
            return self._parse_single_profile(data)
    
    async def get_all(self) -> List[CropProfile]:
        """Get all crop profiles from the file.
        
        Works for both single profile and collection files.
        
        Returns:
            List of all CropProfile instances
        """
        await self._load_cache()
        return list(self._cache.values())
    
    async def _load_cache(self) -> None:
        """Load all crops from file into cache."""
        if self._cache is not None:
            return
        
        content = await self.file_repository.read(self.file_path)
        data = json.loads(content)
        
        self._cache = {}
        
        # Check if this is a collection file or single profile file
        if 'crops' in data:
            # Collection file
            for crop_data in data['crops']:
                crop_profile = self._parse_crop_data(crop_data)
                key = self._make_cache_key(crop_profile)
                self._cache[key] = crop_profile
        else:
            # Single profile file
            crop_profile = self._parse_single_profile(data)
            key = self._make_cache_key(crop_profile)
            self._cache[key] = crop_profile
    
    def _make_cache_key(self, profile: CropProfile) -> str:
        """Create cache key from crop profile."""
        crop_id = profile.crop.crop_id
        variety = profile.crop.variety
        return f"{crop_id}:{variety}" if variety else crop_id
    
    def _parse_single_profile(self, data: dict) -> CropProfile:
        """Parse single crop profile from JSON.
        
        Args:
            data: Dictionary containing crop and stage_requirements at top level
            
        Returns:
            CropProfile
        """
        # Parse crop info
        crop_data = data['crop']
        crop = Crop(
            crop_id=crop_data['crop_id'],
            name=crop_data['name'],
            area_per_unit=crop_data.get('area_per_unit', 0.25),
            variety=crop_data.get('variety'),
            revenue_per_area=crop_data.get('revenue_per_area'),
            max_revenue=crop_data.get('max_revenue'),
            groups=crop_data.get('groups')
        )
        
        # Parse stage requirements
        stage_requirements = self._parse_stage_requirements(data['stage_requirements'])
        
        return CropProfile(
            crop=crop,
            stage_requirements=stage_requirements
        )
    
    def _parse_crop_data(self, crop_data: dict) -> CropProfile:
        """Parse crop data from collection file JSON into CropProfile.
        
        Args:
            crop_data: Dictionary containing crop and stage_requirements
            
        Returns:
            CropProfile
        """
        # Parse crop info
        crop_info = crop_data['crop']
        crop = Crop(
            crop_id=crop_info['crop_id'],
            name=crop_info['name'],
            area_per_unit=crop_info.get('area_per_unit', 0.25),
            variety=crop_info.get('variety'),
            revenue_per_area=crop_info.get('revenue_per_area'),
            max_revenue=crop_info.get('max_revenue'),
            groups=crop_info.get('groups')
        )
        
        # Parse stage requirements
        stage_requirements = self._parse_stage_requirements(crop_data['stage_requirements'])
        
        return CropProfile(
            crop=crop,
            stage_requirements=stage_requirements
        )
    
    def _parse_stage_requirements(self, stages_data: list) -> List[StageRequirement]:
        """Parse stage requirements from JSON data.
        
        Args:
            stages_data: List of stage requirement dictionaries
            
        Returns:
            List of StageRequirement instances
        """
        stage_requirements = []
        for stage_data in stages_data:
            stage = GrowthStage(
                name=stage_data['stage']['name'],
                order=stage_data['stage']['order']
            )
            
            temp_data = stage_data['temperature']
            temperature = TemperatureProfile(
                base_temperature=temp_data['base_temperature'],
                optimal_min=temp_data['optimal_min'],
                optimal_max=temp_data['optimal_max'],
                low_stress_threshold=temp_data.get('low_stress_threshold', temp_data['optimal_min']),
                high_stress_threshold=temp_data.get('high_stress_threshold', temp_data['optimal_max']),
                frost_threshold=temp_data.get('frost_threshold', 0.0),
                sterility_risk_threshold=temp_data.get('sterility_risk_threshold')
            )
            
            sunshine_data = stage_data.get('sunshine', {})
            sunshine = SunshineProfile(
                minimum_sunshine_hours=sunshine_data.get('minimum_sunshine_hours', 3.0),
                target_sunshine_hours=sunshine_data.get('target_sunshine_hours', 6.0)
            )
            
            thermal_data = stage_data['thermal']
            thermal = ThermalRequirement(
                required_gdd=thermal_data['required_gdd']
            )
            
            stage_req = StageRequirement(
                stage=stage,
                temperature=temperature,
                sunshine=sunshine,
                thermal=thermal
            )
            stage_requirements.append(stage_req)
        
        return stage_requirements



