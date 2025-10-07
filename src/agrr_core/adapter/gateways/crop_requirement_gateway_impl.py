"""Adapter: Crop requirement gateway implementation (LLM-injected, stub fallback).

This implementation accepts an LLM client via dependency injection. If the
client is provided, `_infer_with_llm` will attempt to use it; otherwise (or on
errors), it falls back to deterministic defaults. The adapter translates LLM
outputs to domain entities (`CropRequirementAggregate`).
"""

from typing import List, Optional, Dict, Any, Tuple

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

    async def _infer_with_llm(self, crop_query: str) -> Tuple[Crop, List[StageRequirement]]:
        # Use the new 3-step flow if LLM client is available
        if self.llm_client is not None:
            if hasattr(self.llm_client, 'execute_crop_requirement_flow'):
                flow_result = await self.llm_client.execute_crop_requirement_flow(crop_query)
                if flow_result.get("flow_status") == "completed":
                    return self._parse_flow_result(flow_result)
                else:
                    raise RuntimeError(f"3-step flow failed: {flow_result.get('error', 'Unknown error')}")
            else:
                raise RuntimeError("LLM client does not support the required 3-step flow")

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

    def _normalize_stage_name(self, stage_data: Dict[str, Any]) -> str:
        """Normalize stage name from various possible field names.
        
        Step 2 formats: stage_name, ステージ名, stage
        Step 3 formats: name, stage_name
        """
        # Try various field names for stage name
        return (
            stage_data.get("stage_name") or
            stage_data.get("ステージ名") or
            stage_data.get("stage") or
            stage_data.get("name") or
            "Unknown Stage"
        )
    
    def _parse_flow_result(self, flow_result: Dict[str, Any]) -> Tuple[Crop, List[StageRequirement]]:
        """Parse the 3-step flow result into domain entities.
        
        Handles different field names from Step 2 and Step 3:
        - Step 2: stage_name/ステージ名/stage, management_focus/管理の重点, management_boundary/管理転換点
        - Step 3: name, temperature_requirements, sunlight_requirements, accumulated_temperature
        
        Args:
            flow_result: Result from execute_crop_requirement_flow
            
        Returns:
            Tuple of Crop and list of StageRequirement entities
        """
        crop_info = flow_result.get("crop_info", {})
        crop_name = crop_info.get("name", "Unknown")
        variety = crop_info.get("variety", "default")
        
        # Create crop entity
        crop = Crop(crop_id=f"{crop_name.lower()}_{variety.lower()}", name=crop_name)
        
        # Parse stage requirements
        stage_requirements = []
        stages_data = flow_result.get("stages", [])
        
        for i, stage_data in enumerate(stages_data):
            # Determine if this is a Step 3 result (nested "stage" key) or Step 2 result (flat structure)
            if "stage" in stage_data and isinstance(stage_data["stage"], dict):
                # Step 3 structure: {"stage": {"name": ..., "temperature_requirements": ...}}
                stage_info = stage_data["stage"]
                stage_name = self._normalize_stage_name(stage_info)
                
                # Parse temperature profile (Step 3 field names)
                temp_data = stage_info.get("temperature_requirements") or stage_info.get("temperature", {})
                temp_range = temp_data.get("optimal_temperature_range", {})
                temp = TemperatureProfile(
                    base_temperature=temp_data.get("base_temperature", 10.0),
                    optimal_min=temp_range.get("night") or temp_data.get("optimal_min", 20.0),
                    optimal_max=temp_range.get("day") or temp_data.get("optimal_max", 26.0),
                    low_stress_threshold=(
                        temp_data.get("low_temperature_stress_threshold") or 
                        temp_data.get("low_stress_threshold", 12.0)
                    ),
                    high_stress_threshold=(
                        temp_data.get("high_temperature_stress_threshold") or 
                        temp_data.get("high_stress_threshold", 32.0)
                    ),
                    frost_threshold=(
                        temp_data.get("frost_damage_risk_temperature") or 
                        temp_data.get("frost_threshold", 0.0)
                    ),
                    sterility_risk_threshold=(
                        temp_data.get("high_temperature_damage_threshold") or
                        temp_data.get("high_temperature_disability_threshold") or
                        temp_data.get("high_temperature_disability_risk_temperature") or
                        temp_data.get("sterility_risk_threshold") or
                        (temp_data.get("high_temperature_damage", {}) or {}).get("infertility_risk_temperature")
                    ),
                )
                
                # Parse sunshine profile (Step 3 field names)
                sun_data = (
                    stage_info.get("sunlight_requirements") or 
                    stage_info.get("light_requirements") or 
                    stage_info.get("sunshine") or
                    {}
                )
                sun = SunshineProfile(
                    minimum_sunshine_hours=sun_data.get("minimum_sunlight_hours", sun_data.get("minimum_sunshine_hours", 3.0)),
                    target_sunshine_hours=sun_data.get("target_sunlight_hours", sun_data.get("target_sunshine_hours", 6.0))
                )
                
                # Parse thermal requirement (Step 3 field names)
                thermal_data = (
                    stage_info.get("accumulated_temperature") or 
                    stage_info.get("growing_degree_days") or
                    stage_info.get("gdd_requirements") or
                    stage_info.get("thermal") or
                    {}
                )
            else:
                # Step 2 structure (flat): {"stage_name"/"ステージ名"/"stage": ..., "management_focus": ...}
                # Or old fallback structure
                stage_name = self._normalize_stage_name(stage_data)
                
                # Step 2 doesn't have temperature/sunshine/thermal data yet
                # Use defaults for now (will be populated by Step 3)
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
                thermal_data = {}
            
            # Create stage entity
            stage = GrowthStage(name=stage_name, order=i+1)
            
            # Parse thermal requirement
            required_gdd = thermal_data.get("required_gdd") if thermal_data else None
            if required_gdd is None:
                required_gdd = 400.0
            thermal = ThermalRequirement(required_gdd=required_gdd)
            
            # Create stage requirement
            sr = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
            stage_requirements.append(sr)
        
        return crop, stage_requirements


