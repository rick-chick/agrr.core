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

    def __init__(self, llm_client: Optional[LLMClient] = None, file_repository=None):
        """Initialize with an optional LLM client (DI) and file repository.

        The client is expected to expose an async `generate(prompt: str) -> str`-like
        API. We do not enforce a strict protocol here to avoid tight coupling.
        
        Args:
            llm_client: Optional LLM client for generating requirements
            file_repository: Optional file repository for loading requirements from files
        """
        self.llm_client = llm_client
        self.file_repository = file_repository

    async def craft(self, request: CropRequirementCraftRequestDTO) -> CropRequirementAggregate:
        crop_query = (request.crop_query or "").strip()
        
        # Step 1: Extract crop and variety
        step1_result = await self.extract_crop_variety(crop_query)
        crop_name = step1_result.get("crop_name", crop_query)
        variety = step1_result.get("variety", "default")
        
        # Step 2: Define growth periods
        step2_result = await self.define_growth_stages(crop_name, variety)
        growth_periods = step2_result.get("growth_periods", [])
        
        # Step 3: Research requirements for each period
        stage_requirements = []
        for period in growth_periods:
            period_name = period.get("period_name", "Unknown")
            period_desc = period.get("period_description", "")
            order = period.get("order", len(stage_requirements) + 1)
            
            step3_result = await self.research_stage_requirements(
                crop_name, variety, period_name, period_desc
            )
            
            # Parse step3 result into entities
            temp_data = step3_result.get("temperature", {})
            temp = TemperatureProfile(
                base_temperature=temp_data.get("base_temperature", 10.0),
                optimal_min=temp_data.get("optimal_min", 20.0),
                optimal_max=temp_data.get("optimal_max", 26.0),
                low_stress_threshold=temp_data.get("low_stress_threshold", 12.0),
                high_stress_threshold=temp_data.get("high_stress_threshold", 32.0),
                frost_threshold=temp_data.get("frost_threshold", 0.0),
                sterility_risk_threshold=temp_data.get("sterility_risk_threshold"),
            )
            
            sun_data = step3_result.get("sunshine", {})
            sun = SunshineProfile(
                minimum_sunshine_hours=sun_data.get("minimum_sunshine_hours", 3.0),
                target_sunshine_hours=sun_data.get("target_sunshine_hours", 6.0)
            )
            
            thermal_data = step3_result.get("thermal", {})
            thermal = ThermalRequirement(
                required_gdd=thermal_data.get("required_gdd", 400.0)
            )
            
            stage = GrowthStage(name=period_name, order=order)
            sr = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
            stage_requirements.append(sr)
        
        # Create crop entity
        crop = Crop(
            crop_id=crop_name.lower(),
            name=crop_name,
            area_per_unit=0.25,  # Default area per unit in m²
            variety=variety if variety and variety != "default" else None
        )
        
        return CropRequirementAggregate(crop=crop, stage_requirements=stage_requirements)

    async def extract_crop_variety(self, crop_query: str) -> Dict[str, Any]:
        """Step 1: Extract crop name and variety from user input."""
        if self.llm_client is not None:
            if hasattr(self.llm_client, 'step1_crop_variety_selection'):
                result = await self.llm_client.step1_crop_variety_selection(crop_query)
                return result.get("data", {})
            else:
                raise RuntimeError("LLM client does not support step1_crop_variety_selection")
        
        # Fallback
        return {"crop_name": crop_query, "variety": "default"}

    async def define_growth_stages(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Step 2: Define growth stages for the crop variety."""
        if self.llm_client is not None:
            if hasattr(self.llm_client, 'step2_growth_stage_definition'):
                result = await self.llm_client.step2_growth_stage_definition(crop_name, variety)
                return result.get("data", {})
            else:
                raise RuntimeError("LLM client does not support step2_growth_stage_definition")
        
        # Fallback
        return {
            "crop_info": {"name": crop_name, "variety": variety},
            "growth_periods": [{"period_name": "Default", "order": 1, "period_description": ""}]
        }

    async def research_stage_requirements(self, crop_name: str, variety: str, 
                                         stage_name: str, stage_description: str) -> Dict[str, Any]:
        """Step 3: Research variety-specific requirements for a specific stage."""
        if self.llm_client is not None:
            if hasattr(self.llm_client, 'step3_variety_specific_research'):
                result = await self.llm_client.step3_variety_specific_research(
                    crop_name, variety, stage_name, stage_description
                )
                return result.get("data", {})
            else:
                raise RuntimeError("LLM client does not support step3_variety_specific_research")
        
        # Fallback
        return {
            "temperature": {
                "base_temperature": 10.0,
                "optimal_min": 20.0,
                "optimal_max": 26.0,
                "low_stress_threshold": 12.0,
                "high_stress_threshold": 32.0,
                "frost_threshold": 0.0,
                "sterility_risk_threshold": 35.0
            },
            "sunshine": {
                "minimum_sunshine_hours": 3.0,
                "target_sunshine_hours": 6.0
            },
            "thermal": {
                "required_gdd": 400.0
            }
        }

    async def extract_crop_economics(self, crop_name: str, variety: str) -> Dict[str, Any]:
        """Extract crop economic information (area per unit and revenue per area).
        
        This is a separate LLM call independent from growth stage information.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            
        Returns:
            Dict containing area_per_unit and revenue_per_area
        """
        if self.llm_client is not None:
            if hasattr(self.llm_client, 'extract_crop_economics'):
                result = await self.llm_client.extract_crop_economics(crop_name, variety)
                return result.get("data", {})
            else:
                raise RuntimeError("LLM client does not support extract_crop_economics")
        
        # Fallback
        return {
            "area_per_unit": 0.25,  # Default 0.25 m² per unit
            "revenue_per_area": None  # No revenue data by default
        }

    async def _infer_with_llm(self, crop_query: str) -> Tuple[Crop, List[StageRequirement]]:
        # Deprecated: This method is now replaced by the 3-step methods above
        # Kept for backward compatibility
        # Stubbed thresholds: keep aligned with entity docstrings
        name = crop_query if crop_query else "Unknown"
        crop = Crop(crop_id=name.lower(), name=name, area_per_unit=0.25, variety=None)
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
            flow_result: Result containing crop_info and stages data
            
        Returns:
            Tuple of Crop and list of StageRequirement entities
        """
        crop_info = flow_result.get("crop_info", {})
        crop_name = crop_info.get("name", "Unknown")
        variety = crop_info.get("variety", "default")
        
        # Create crop entity
        crop = Crop(
            crop_id=crop_name.lower(),
            name=crop_name,
            area_per_unit=0.25,  # Default area per unit in m²
            variety=variety if variety and variety != "default" else None
        )
        
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
    
    async def get(self, file_path: str) -> CropRequirementAggregate:
        """Load crop requirements from JSON file using file repository.
        
        Args:
            file_path: Path to crop requirement JSON file
            
        Returns:
            CropRequirementAggregate loaded from file
            
        Expected JSON format:
        {
            "crop": {"crop_id": "rice", "name": "Rice", "variety": "Koshihikari"},
            "stage_requirements": [
                {
                    "stage": {"name": "Growth", "order": 1},
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 30.0,
                        "low_stress_threshold": 15.0,
                        "high_stress_threshold": 35.0,
                        "frost_threshold": 0.0
                    },
                    "thermal": {"required_gdd": 500.0}
                }
            ]
        }
        """
        if not self.file_repository:
            raise ValueError("File repository not provided. Cannot load from file.")
        
        # Read file using repository
        content = await self.file_repository.read(file_path)
        
        # Parse JSON
        import json
        data = json.loads(content)
        
        # Parse crop info
        crop_data = data['crop']
        crop = Crop(
            crop_id=crop_data['crop_id'],
            name=crop_data['name'],
            area_per_unit=crop_data.get('area_per_unit', 0.25),  # Default 0.25 m² if not specified
            variety=crop_data.get('variety'),
            revenue_per_area=crop_data.get('revenue_per_area')
        )
        
        # Parse stage requirements
        stage_requirements = []
        for stage_req_data in data['stage_requirements']:
            stage = GrowthStage(
                name=stage_req_data['stage']['name'],
                order=stage_req_data['stage']['order']
            )
            
            temp_data = stage_req_data['temperature']
            temperature = TemperatureProfile(
                base_temperature=temp_data['base_temperature'],
                optimal_min=temp_data['optimal_min'],
                optimal_max=temp_data['optimal_max'],
                low_stress_threshold=temp_data['low_stress_threshold'],
                high_stress_threshold=temp_data['high_stress_threshold'],
                frost_threshold=temp_data['frost_threshold']
            )
            
            sunshine = SunshineProfile()  # Use defaults
            
            thermal = ThermalRequirement(
                required_gdd=stage_req_data['thermal']['required_gdd']
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


