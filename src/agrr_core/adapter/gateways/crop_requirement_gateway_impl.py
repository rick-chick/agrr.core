"""Adapter: Crop requirement gateway implementation (LLM-injected, stub fallback).

This implementation accepts an LLM client via dependency injection. If the
client is provided, `_infer_with_llm` will attempt to use it; otherwise (or on
errors), it falls back to deterministic defaults. The adapter translates LLM
outputs to domain entities (`CropRequirementAggregate`).
"""

from typing import List, Optional

from agrr_core.usecase.gateways.crop_requirement_gateway import CropRequirementGateway
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
from agrr_core.adapter.interfaces.llm_client import LLMClient
from agrr_core.adapter.utils.llm_struct_schema import (
    build_stage_requirement_structure,
    build_stage_requirement_descriptions,
)


class CropRequirementGatewayImpl(CropRequirementGateway):
    """Gateway that uses an injected LLM client to craft requirements (if present)."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize with an optional LLM client (DI).

        The client is expected to expose an async `generate(prompt: str) -> str`-like
        API. We do not enforce a strict protocol here to avoid tight coupling.
        """
        self.llm_client = llm_client

    async def craft(self, request: CropRequirementCraftRequestDTO) -> CropRequirementAggregate:
        crop_query = (request.crop_query or "").strip()
        crop, stage_requirements = await self._infer_with_llm(crop_query)
        return CropRequirementAggregate(crop=crop, stage_requirements=stage_requirements)

    async def _infer_with_llm(self, crop_query: str) -> tuple[Crop, List[StageRequirement]]:
        # If an LLM client is provided, try to use it (best-effort; ignore parsing for now)
        if self.llm_client is not None:
            try:
                structure = build_stage_requirement_structure()
                descriptions = build_stage_requirement_descriptions()
                instruction = "Return JSON strictly matching this structure. Use null for unknown values."
                _resp = await self.llm_client.struct(
                    query=crop_query,
                    structure=structure,
                    descriptions=descriptions,
                    instruction=instruction,
                )
                # TODO: parse _resp["data"] into profiles in a future iteration
            except Exception:
                # Fallback to defaults
                pass

        # Stubbed thresholds: keep aligned with entity docstrings
        name = crop_query if crop_query else "Unknown"
        crop = Crop(crop_id=name.lower(), name=name)
        stage = GrowthStage(name="Default", order=1)
        temp = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=26.0,
            low_stress_threshold=12.0,
            high_stress_threshold=32.0,
            frost_threshold=0.0,
            sterility_risk_threshold=35.0,
        )
        sun = SunshineProfile(minimum_sunshine_hours=3.0, target_sunshine_hours=6.0)
        thermal = ThermalRequirement(required_gdd=400.0)
        sr = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
        return crop, [sr]


