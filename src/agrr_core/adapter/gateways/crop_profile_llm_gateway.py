"""LLM-based gateway for crop profile generation."""

from typing import List, Dict, Any

from agrr_core.entity import (
    Crop,
    GrowthStage,
    TemperatureProfile,
    SunshineProfile,
    ThermalRequirement,
    StageRequirement,
)
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.framework.repositories.crop_profile_llm_repository import CropProfileLLMRepository


class CropProfileLLMGateway(CropProfileGateway):
    """Gateway implementation using LLM for crop profile generation.
    
    This gateway uses an LLM client to generate crop profiles dynamically
    based on user queries.
    """
    
    def __init__(self, llm_repository: CropProfileLLMRepository):
        """Initialize LLM gateway.
        
        Args:
            llm_repository: LLM repository for generating crop profiles
        """
        self.llm_repository = llm_repository
    
    async def get_all(self) -> List[CropProfile]:
        """Get all crop profiles.
        
        Note: LLM-based gateway does not support listing all profiles.
        
        Returns:
            Empty list
        """
        return []
    
    # LLM-specific methods - delegate to repository
    async def extract_crop_variety(self, crop_query: str) -> Dict[str, Any]:
        """Extract crop name and variety from user input."""
        return await self.llm_repository.extract_crop_variety(crop_query)
    
    async def define_growth_stages(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Define growth stages for the crop variety."""
        return await self.llm_repository.define_growth_stages(crop_name, variety)
    
    async def research_stage_requirements(
        self, crop_name: str, variety: str, stage_name: str, stage_description: str
    ) -> Dict[str, Any]:
        """Research variety-specific requirements for a specific stage."""
        return await self.llm_repository.research_stage_requirements(
            crop_name, variety, stage_name, stage_description
        )
    
    async def extract_crop_economics(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop economic information."""
        return await self.llm_repository.extract_crop_economics(crop_name, variety)
    
    async def extract_crop_family(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop family information."""
        return await self.llm_repository.extract_crop_family(crop_name, variety)
    
    async def generate(self, crop_query: str) -> CropProfile:
        """Generate a crop profile using LLM.
        
        Args:
            crop_query: Query string describing the crop (e.g., "トマト", "rice Koshihikari")
            
        Returns:
            Generated CropProfile instance
        """
        # Step 1: Extract crop name and variety
        crop_variety = await self.llm_repository.extract_crop_variety(crop_query)
        crop_name = crop_variety.get("crop_name", crop_query)
        variety = crop_variety.get("variety", "default")
        
        # Step 2: Define growth stages
        growth_data = await self.llm_repository.define_growth_stages(crop_name, variety)
        growth_periods = growth_data.get("growth_periods", [])
        
        # Step 3: Research requirements for each stage
        stage_requirements = []
        for i, period in enumerate(growth_periods, start=1):
            stage_name = period.get("period_name", f"Stage {i}")
            stage_description = period.get("period_description", "")
            
            requirements = await self.llm_repository.research_stage_requirements(
                crop_name, variety, stage_name, stage_description
            )
            
            # Create stage requirement
            stage = GrowthStage(name=stage_name, order=i)
            
            # Temperature profile
            temp_data = requirements.get("temperature", {})
            temperature = TemperatureProfile(
                base_temperature=float(temp_data.get("base_temperature", 10.0)),
                optimal_min=float(temp_data.get("optimal_min", 20.0)),
                optimal_max=float(temp_data.get("optimal_max", 30.0)),
                low_stress_threshold=float(temp_data.get("low_stress_threshold", 15.0)),
                high_stress_threshold=float(temp_data.get("high_stress_threshold", 35.0)),
                frost_threshold=float(temp_data.get("frost_threshold", 0.0)),
                max_temperature=float(temp_data.get("max_temperature", 42.0)),
                sterility_risk_threshold=temp_data.get("sterility_risk_threshold")
            )
            
            # Sunshine profile
            sunshine_data = requirements.get("sunshine", {})
            sunshine = SunshineProfile(
                minimum_sunshine_hours=float(sunshine_data.get("minimum_sunshine_hours", 0.0)),
                target_sunshine_hours=float(sunshine_data.get("target_sunshine_hours", 0.0))
            )
            
            # Thermal requirement
            thermal_data = requirements.get("thermal", {})
            thermal = ThermalRequirement(
                required_gdd=float(thermal_data.get("required_gdd", 0.0))
            )
            
            stage_requirement = StageRequirement(
                stage=stage,
                temperature=temperature,
                sunshine=sunshine,
                thermal=thermal
            )
            stage_requirements.append(stage_requirement)
        
        # Step 4: Extract crop economics
        economics = await self.llm_repository.extract_crop_economics(crop_name, variety)
        area_per_unit = float(economics.get("area_per_unit", 0.25))
        revenue_per_area = float(economics.get("revenue_per_area", 5000.0))
        
        # Step 5: Extract crop family
        family_data = await self.llm_repository.extract_crop_family(crop_name, variety)
        family_scientific = family_data.get("family_scientific", "")
        
        # Create crop entity
        crop = Crop(
            crop_id=crop_name.lower().replace(" ", "_"),
            name=crop_name,
            variety=variety,
            area_per_unit=area_per_unit,
            revenue_per_area=revenue_per_area,
            max_revenue=revenue_per_area * 100,  # Default max revenue
            groups=[family_scientific] if family_scientific else []
        )
        
        # Create crop profile
        crop_profile = CropProfile(
            crop=crop,
            stage_requirements=stage_requirements
        )
        
        return crop_profile

