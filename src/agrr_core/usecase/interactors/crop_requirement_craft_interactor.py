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
            
            # Handle various field names from Step 2
            growth_stages = (
                growth_stages_data.get("growth_periods") or
                growth_stages_data.get("management_stages") or
                growth_stages_data.get("管理ステージ構成") or
                growth_stages_data.get("管理ステージ") or
                growth_stages_data.get("growth_stages") or
                []
            )

            # Step 3: Research requirements for each stage and build entities
            crop = Crop(
                crop_id=crop_name.lower(),
                name=crop_name,
                area_per_unit=0.25,  # Default area per unit in m²
                variety=variety if variety and variety != "default" else None
            )
            stage_requirements = []
            
            for i, stage in enumerate(growth_stages):
                # Handle different response structures from Step 2
                stage_name = (
                    stage.get("period_name") or
                    stage.get("stage_name") or
                    stage.get("ステージ名") or
                    stage.get("stage") or
                    "Unknown Stage"
                )
                stage_description = (
                    stage.get("period_description") or
                    stage.get("description") or
                    stage.get("management_focus") or
                    stage.get("管理の重点") or
                    stage.get("management_transition_point") or
                    stage.get("管理転換点") or
                    stage.get("start_condition") or
                    ""
                )
                
                stage_requirement_data = await self.gateway.research_stage_requirements(
                    crop_name, variety, stage_name, stage_description
                )
                
                # Build entities from the data
                growth_stage = GrowthStage(name=stage_name, order=i + 1)
                
                temp_data = stage_requirement_data.get("temperature", {})
                temperature = TemperatureProfile(
                    base_temperature=temp_data.get("base_temperature", 10.0),
                    optimal_min=temp_data.get("optimal_min", 20.0),
                    optimal_max=temp_data.get("optimal_max", 26.0),
                    low_stress_threshold=temp_data.get("low_stress_threshold", 12.0),
                    high_stress_threshold=temp_data.get("high_stress_threshold", 32.0),
                    frost_threshold=temp_data.get("frost_threshold", 0.0),
                    sterility_risk_threshold=temp_data.get("sterility_risk_threshold", 35.0)
                )
                
                sun_data = stage_requirement_data.get("sunshine", {})
                sunshine = SunshineProfile(
                    minimum_sunshine_hours=sun_data.get("minimum_sunshine_hours", 3.0),
                    target_sunshine_hours=sun_data.get("target_sunshine_hours", 6.0)
                )
                
                thermal_data = stage_requirement_data.get("thermal", {})
                thermal = ThermalRequirement(
                    required_gdd=thermal_data.get("required_gdd", 400.0)
                )
                
                stage_req = StageRequirement(
                    stage=growth_stage,
                    temperature=temperature,
                    sunshine=sunshine,
                    thermal=thermal
                )
                stage_requirements.append(stage_req)
            
            # Build aggregate
            aggregate = CropRequirementAggregate(crop=crop, stage_requirements=stage_requirements)
            
            # Minimal payload handed to presenter; mapping can be done here or by an adapter
            payload = {
                "crop_id": aggregate.crop.crop_id,
                "crop_name": aggregate.crop.name,
                "variety": aggregate.crop.variety,
                "stages": [
                    {
                        "name": sr.stage.name,
                        "order": sr.stage.order,
                        "temperature": {
                            "base_temperature": sr.temperature.base_temperature,
                            "optimal_min": sr.temperature.optimal_min,
                            "optimal_max": sr.temperature.optimal_max,
                            "low_stress_threshold": sr.temperature.low_stress_threshold,
                            "high_stress_threshold": sr.temperature.high_stress_threshold,
                            "frost_threshold": sr.temperature.frost_threshold,
                            "sterility_risk_threshold": sr.temperature.sterility_risk_threshold,
                        },
                        "sunshine": {
                            "minimum_sunshine_hours": sr.sunshine.minimum_sunshine_hours,
                            "target_sunshine_hours": sr.sunshine.target_sunshine_hours,
                        },
                        "thermal": {
                            "required_gdd": sr.thermal.required_gdd,
                        },
                    }
                    for sr in aggregate.stage_requirements
                ],
            }
            return self.presenter.format_success(payload)
        except Exception as e:
            return self.presenter.format_error(f"Crafting failed: {e}")


