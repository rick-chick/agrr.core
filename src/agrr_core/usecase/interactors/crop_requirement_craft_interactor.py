"""Use case interactor for crafting crop stage requirements via LLM gateway."""

from agrr_core.usecase.ports.input.crop_requirement_craft_input_port import (
    CropRequirementCraftInputPort,
)
from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
from agrr_core.usecase.ports.output.crop_requirement_craft_output_port import (
    CropRequirementCraftOutputPort,
)
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
    CropRequirementCraftRequestDTO,
)
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
from agrr_core.adapter.mappers.llm_response_normalizer import LLMResponseNormalizer
from agrr_core.adapter.mappers.crop_requirement_mapper import CropRequirementMapper


class CropRequirementCraftInteractor(CropRequirementCraftInputPort):
    """Interactor: orchestrates gateway and presenter to craft requirements."""

    def __init__(self, gateway: CropRequirementGateway, presenter: CropRequirementCraftOutputPort):
        self.gateway = gateway
        self.presenter = presenter

    async def execute(self, request: CropRequirementCraftRequestDTO) -> dict:
        """Craft crop stage requirements from a minimal crop query.
        
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

            # Step 3: Research requirements for each stage and build entities
            crop = Crop(
                crop_id=crop_name.lower(),
                name=crop_name,
                area_per_unit=area_per_unit,
                variety=variety if variety and variety != "default" else None,
                revenue_per_area=revenue_per_area,
                max_revenue=max_revenue
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
            
            # Build aggregate
            aggregate = CropRequirementAggregate(crop=crop, stage_requirements=stage_requirements)
            
            # Convert aggregate to payload (Phase 2: use Mapper)
            payload = CropRequirementMapper.aggregate_to_payload(aggregate)
            
            return self.presenter.format_success(payload)
        except Exception as e:
            return self.presenter.format_error(f"Crafting failed: {e}")


