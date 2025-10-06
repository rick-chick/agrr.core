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


class CropRequirementCraftInteractor(CropRequirementCraftInputPort):
    """Interactor: orchestrates gateway and presenter to craft requirements."""

    def __init__(self, gateway: CropRequirementGateway, presenter: CropRequirementCraftOutputPort):
        self.gateway = gateway
        self.presenter = presenter

    async def execute(self, request: CropRequirementCraftRequestDTO) -> dict:
        """Craft crop stage requirements from a minimal crop query."""
        crop_query = (request.crop_query or "").strip()
        if not crop_query:
            return self.presenter.format_error("Empty crop query")

        try:
            aggregate = await self.gateway.craft(request)
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


