"""Mapper for CropRequirement entities and DTOs.

This module provides mappers to convert between domain entities and data
transfer objects (DTOs) for crop requirements.
"""

from typing import Dict, Any

from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement


class CropRequirementMapper:
    """Map between CropRequirement domain entities and data transfer objects.
    
    Responsibilities:
    - Convert CropRequirementAggregate to response payload
    - Convert StageRequirement to dictionary
    - Handle nested entity structures
    
    Design Pattern: Mapper Pattern
    - Separates data transformation from business logic
    - Provides bidirectional conversion (if needed)
    - Centralizes entity-DTO mapping logic
    """
    
    @staticmethod
    def aggregate_to_payload(aggregate: CropRequirementAggregate) -> Dict[str, Any]:
        """Convert CropRequirementAggregate to response payload.
        
        This method transforms a domain aggregate into a dictionary suitable
        for API responses or presenter layers.
        
        Args:
            aggregate: CropRequirementAggregate domain entity
            
        Returns:
            Dictionary representation suitable for response
            
        Example:
            >>> crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
            >>> stage_reqs = [...]
            >>> aggregate = CropRequirementAggregate(crop, stage_reqs)
            >>> payload = CropRequirementMapper.aggregate_to_payload(aggregate)
            >>> payload["crop_id"]
            'rice'
        """
        return {
            "crop_id": aggregate.crop.crop_id,
            "crop_name": aggregate.crop.name,
            "variety": aggregate.crop.variety,
            "area_per_unit": aggregate.crop.area_per_unit,
            "revenue_per_area": aggregate.crop.revenue_per_area,
            "max_profit": aggregate.crop.max_profit,
            "stages": [
                CropRequirementMapper.stage_requirement_to_dict(sr)
                for sr in aggregate.stage_requirements
            ],
        }
    
    @staticmethod
    def stage_requirement_to_dict(stage_req: StageRequirement) -> Dict[str, Any]:
        """Convert StageRequirement entity to dictionary.
        
        Args:
            stage_req: StageRequirement entity
            
        Returns:
            Dictionary representation of stage requirement
            
        Example:
            >>> stage = GrowthStage("Growth", 1)
            >>> temp = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
            >>> sun = SunshineProfile(3.0, 6.0)
            >>> thermal = ThermalRequirement(400.0)
            >>> stage_req = StageRequirement(stage, temp, sun, thermal)
            >>> result = CropRequirementMapper.stage_requirement_to_dict(stage_req)
            >>> result["name"]
            'Growth'
        """
        return {
            "name": stage_req.stage.name,
            "order": stage_req.stage.order,
            "temperature": CropRequirementMapper._temperature_to_dict(
                stage_req.temperature
            ),
            "sunshine": CropRequirementMapper._sunshine_to_dict(
                stage_req.sunshine
            ),
            "thermal": CropRequirementMapper._thermal_to_dict(
                stage_req.thermal
            ),
        }
    
    @staticmethod
    def _temperature_to_dict(temperature: TemperatureProfile) -> Dict[str, float]:
        """Convert TemperatureProfile to dictionary.
        
        Args:
            temperature: TemperatureProfile entity
            
        Returns:
            Dictionary with temperature data
        """
        return {
            "base_temperature": temperature.base_temperature,
            "optimal_min": temperature.optimal_min,
            "optimal_max": temperature.optimal_max,
            "low_stress_threshold": temperature.low_stress_threshold,
            "high_stress_threshold": temperature.high_stress_threshold,
            "frost_threshold": temperature.frost_threshold,
            "sterility_risk_threshold": temperature.sterility_risk_threshold,
        }
    
    @staticmethod
    def _sunshine_to_dict(sunshine: SunshineProfile) -> Dict[str, float]:
        """Convert SunshineProfile to dictionary.
        
        Args:
            sunshine: SunshineProfile entity
            
        Returns:
            Dictionary with sunshine data
        """
        return {
            "minimum_sunshine_hours": sunshine.minimum_sunshine_hours,
            "target_sunshine_hours": sunshine.target_sunshine_hours,
        }
    
    @staticmethod
    def _thermal_to_dict(thermal: ThermalRequirement) -> Dict[str, float]:
        """Convert ThermalRequirement to dictionary.
        
        Args:
            thermal: ThermalRequirement entity
            
        Returns:
            Dictionary with thermal requirement data
        """
        return {
            "required_gdd": thermal.required_gdd,
        }

