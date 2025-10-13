"""File-based implementation of CropRequirementRepository."""

import json
from agrr_core.entity import (
    Crop,
    GrowthStage,
    TemperatureProfile,
    SunshineProfile,
    ThermalRequirement,
    StageRequirement,
)
from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)
from agrr_core.adapter.interfaces.crop_requirement_repository_interface import (
    CropRequirementRepositoryInterface,
)
from agrr_core.adapter.interfaces.file_repository_interface import FileRepositoryInterface


class CropRequirementFileRepository(CropRequirementRepositoryInterface):
    """File-based implementation of CropRequirementRepository.
    
    Reads crop requirements from JSON files.
    File path is configured at initialization.
    """
    
    def __init__(self, file_repository: FileRepositoryInterface, file_path: str):
        """Initialize crop requirement file repository.
        
        Args:
            file_repository: File repository for file I/O operations (Framework layer)
            file_path: File path to crop requirement JSON file
        """
        self.file_repository = file_repository
        self.file_path = file_path
    
    async def get(self) -> CropRequirementAggregate:
        """Get crop requirement from configured file.
        
        Returns:
            CropRequirementAggregate loaded from file
        """
        # Read file using repository
        content = await self.file_repository.read(self.file_path)
        
        # Parse JSON
        data = json.loads(content)
        
        # Parse crop info
        crop_data = data['crop']
        crop = Crop(
            crop_id=crop_data['crop_id'],
            name=crop_data['name'],
            area_per_unit=crop_data.get('area_per_unit', 0.25),
            variety=crop_data.get('variety'),
            revenue_per_area=crop_data.get('revenue_per_area'),
            max_revenue=crop_data.get('max_revenue'),
            groups=crop_data.get('groups')  # None if not present (backward compatibility)
        )
        
        # Parse stage requirements
        stage_requirements = []
        for stage_data in data['stage_requirements']:
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
        
        return CropRequirementAggregate(
            crop=crop,
            stage_requirements=stage_requirements
        )

