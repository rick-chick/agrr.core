"""Use case interactor for crafting crop profiles via LLM gateway."""

from agrr_core.usecase.ports.input.crop_profile_craft_input_port import (
    CropProfileCraftInputPort,
)
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.ports.output.crop_profile_craft_output_port import (
    CropProfileCraftOutputPort,
)
from agrr_core.usecase.dto.crop_profile_craft_request_dto import (
    CropProfileCraftRequestDTO,
)
from agrr_core.entity import (
    Crop,
    GrowthStage,
    TemperatureProfile,
    SunshineProfile,
    ThermalRequirement,
    StageRequirement,
)
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.adapter.mappers.llm_response_normalizer import LLMResponseNormalizer
from agrr_core.adapter.mappers.crop_profile_mapper import CropProfileMapper


class CropProfileCraftInteractor(CropProfileCraftInputPort):
    """Interactor: orchestrates gateway and presenter to craft crop profiles."""

    def __init__(self, gateway: CropProfileGateway, presenter: CropProfileCraftOutputPort):
        self.gateway = gateway
        self.presenter = presenter

    async def execute(self, request: CropProfileCraftRequestDTO) -> dict:
        """Craft crop profile from a minimal crop query.
        
        This method orchestrates the 3-step flow:
        1. Extract crop variety from query
        2. Define growth stages for the variety
        3. Research detailed requirements for each stage
        """
        crop_query = (request.crop_query or "").strip()
        if not crop_query:
            return self.presenter.format_error("Empty crop query")

        try:
            # Step 1: Extract crop and variety
            crop_variety_data = await self.gateway.extract_crop_variety(crop_query)
            crop_name = crop_variety_data.get("crop_name", "Unknown")
            variety = crop_variety_data.get("variety", "default")

            # Step 2: Define growth stages
            growth_stages_data = await self.gateway.define_growth_stages(crop_name, variety)
            
            # Normalize growth stages field (Phase 2: use Normalizer)
            growth_stages = LLMResponseNormalizer.normalize_growth_stages_field(
                growth_stages_data
            )

            # Extract crop economic information (separate LLM call)
            crop_economics = await self.gateway.extract_crop_economics(crop_name, variety)
            area_per_unit = crop_economics.get("area_per_unit", 0.25)
            revenue_per_area = crop_economics.get("revenue_per_area")
            max_revenue = crop_economics.get("max_revenue")  # Optional market constraint

            # Extract crop family information (separate LLM call)
            crop_family = await self.gateway.extract_crop_family(crop_name, variety)
            family_scientific = crop_family.get("family_scientific")
            
            # Build groups list with family at the beginning
            groups = []
            if family_scientific:
                groups.append(family_scientific)

            # Step 3: Research requirements for each stage and build entities
            crop = Crop(
                crop_id=crop_name.lower(),
                name=crop_name,
                area_per_unit=area_per_unit,
                variety=variety if variety and variety != "default" else None,
                revenue_per_area=revenue_per_area,
                max_revenue=max_revenue,
                groups=groups if groups else None
            )
            stage_requirements = []
            
            for i, stage in enumerate(growth_stages):
                # Normalize field names (Phase 2: use Normalizer)
                stage_name = LLMResponseNormalizer.normalize_stage_name(stage)
                stage_description = LLMResponseNormalizer.normalize_stage_description(stage)
                
                stage_requirement_data = await self.gateway.research_stage_requirements(
                    crop_name, variety, stage_name, stage_description
                )
                
                # Build entities from the data (Phase 2: use Normalizer)
                growth_stage = GrowthStage(name=stage_name, order=i + 1)
                
                # Normalize temperature data
                temp_data = LLMResponseNormalizer.normalize_temperature_field(
                    stage_requirement_data
                )
                temperature = TemperatureProfile(**temp_data)
                
                # Normalize sunshine data
                sun_data = LLMResponseNormalizer.normalize_sunshine_field(
                    stage_requirement_data
                )
                sunshine = SunshineProfile(**sun_data)
                
                # Normalize thermal data
                thermal_data = LLMResponseNormalizer.normalize_thermal_field(
                    stage_requirement_data
                )
                thermal = ThermalRequirement(**thermal_data)
                
                stage_req = StageRequirement(
                    stage=growth_stage,
                    temperature=temperature,
                    sunshine=sunshine,
                    thermal=thermal
                )
                stage_requirements.append(stage_req)
            
            # Build profile
            profile = CropProfile(crop=crop, stage_requirements=stage_requirements)
            
            # Convert profile to standard file format (directly usable by progress/optimize-period)
            crop_profile_data = CropProfileMapper.to_crop_profile_format(profile)
            
            return crop_profile_data
        except Exception as e:
            return self.presenter.format_error(f"Crafting failed: {e}")



