"""Debug test for Gateway _parse_flow_result method."""

import pytest
from unittest.mock import Mock

from agrr_core.adapter.gateways.crop_requirement_gateway_impl import CropRequirementGatewayImpl
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement


def test_gateway_parse_flow_result():
    """Test the Gateway _parse_flow_result method with actual data."""
    
    # Create a mock gateway instance
    gateway = CropRequirementGatewayImpl(llm_client=None)
    
    # Simulate the actual flow result from debug output
    mock_flow_result = {
        "crop_info": {
            "name": "かぶ",
            "variety": "default"
        },
        "stages": [
            {
                "stage": {
                    "name": "播種",
                    "characteristics": "種子を土壌に播く",
                    "temperature_requirements": {
                        "optimal_temperature_range": {"day": 15.0, "night": 10.0},
                        "base_temperature": 5.0,
                        "low_temperature_stress_threshold": 0.0,
                        "high_temperature_stress_threshold": 30.0,
                        "frost_damage_risk_temperature": 0.0,
                        "high_temperature_damage_threshold": 25.0
                    },
                    "sunlight_requirements": {
                        "minimum_sunlight_hours": 3.0,
                        "target_sunlight_hours": 6.0
                    },
                    "accumulated_temperature": {
                        "required_gdd": 200.0
                    }
                }
            },
            {
                "stage": {
                    "name": "苗期",
                    "characteristics": "発芽が完了し、葉が展開し始める",
                    "temperature_requirements": {
                        "optimal_temperature_range": {"day": 20.0, "night": 15.0},
                        "base_temperature": 5.0,
                        "low_temperature_stress_threshold": 0.0,
                        "high_temperature_stress_threshold": 30.0,
                        "frost_damage_risk_temperature": 0.0,
                        "high_temperature_damage_threshold": 35.0
                    },
                    "light_requirements": {
                        "minimum_sunlight_hours": 3.0,
                        "target_sunlight_hours": 6.0
                    },
                    "growing_degree_days": {
                        "required_gdd": None
                    }
                }
            }
        ],
        "flow_status": "completed"
    }
    
    print("Testing Gateway _parse_flow_result method:")
    print(f"Input flow result: {mock_flow_result}")
    
    # Call the method
    crop, stage_requirements = gateway._parse_flow_result(mock_flow_result)
    
    print(f"\nParsed result:")
    print(f"Crop: {crop}")
    print(f"Number of stage requirements: {len(stage_requirements)}")
    
    for i, sr in enumerate(stage_requirements):
        print(f"\nStage {i+1}:")
        print(f"  Stage name: '{sr.stage.name}'")
        print(f"  Stage order: {sr.stage.order}")
        print(f"  Temperature base: {sr.temperature.base_temperature}")
        print(f"  Temperature optimal_min: {sr.temperature.optimal_min}")
        print(f"  Temperature optimal_max: {sr.temperature.optimal_max}")
        print(f"  Sunshine minimum: {sr.sunshine.minimum_sunshine_hours}")
        print(f"  Sunshine target: {sr.sunshine.target_sunshine_hours}")
        print(f"  Thermal GDD: {sr.thermal.required_gdd}")
    
    # Assertions
    assert isinstance(crop, Crop)
    assert crop.name == "かぶ"
    assert crop.crop_id == "かぶ_default"
    
    assert len(stage_requirements) == 2
    
    # Test first stage
    stage1 = stage_requirements[0]
    assert isinstance(stage1, StageRequirement)
    assert stage1.stage.name == "播種"
    assert stage1.stage.order == 1
    assert stage1.temperature.base_temperature == 5.0
    assert stage1.temperature.optimal_min == 10.0  # night temperature
    assert stage1.temperature.optimal_max == 15.0  # day temperature
    assert stage1.sunshine.minimum_sunshine_hours == 3.0
    assert stage1.sunshine.target_sunshine_hours == 6.0
    assert stage1.thermal.required_gdd == 200.0
    
    # Test second stage
    stage2 = stage_requirements[1]
    assert stage2.stage.name == "苗期"
    assert stage2.stage.order == 2
    assert stage2.temperature.optimal_min == 15.0  # night temperature
    assert stage2.temperature.optimal_max == 20.0  # day temperature
    assert stage2.thermal.required_gdd == 400.0  # default value when None
    
    print("\n✅ All Gateway parsing assertions passed!")


def test_gateway_with_old_structure():
    """Test Gateway with the old expected structure (fallback)."""
    
    gateway = CropRequirementGatewayImpl(llm_client=None)
    
    # Old structure (what we originally expected)
    old_flow_result = {
        "crop_info": {
            "name": "かぶ",
            "variety": "default"
        },
        "stages": [
            {
                "stage_name": "播種",
                "temperature": {
                    "base_temperature": 5.0,
                    "optimal_min": 10.0,
                    "optimal_max": 15.0,
                    "low_stress_threshold": 0.0,
                    "high_stress_threshold": 30.0,
                    "frost_threshold": 0.0,
                    "sterility_risk_threshold": 25.0
                },
                "sunshine": {
                    "minimum_sunshine_hours": 3.0,
                    "target_sunshine_hours": 6.0
                },
                "thermal": {
                    "required_gdd": 200.0
                }
            }
        ],
        "flow_status": "completed"
    }
    
    print("\nTesting Gateway with old structure:")
    crop, stage_requirements = gateway._parse_flow_result(old_flow_result)
    
    print(f"Parsed result with old structure:")
    print(f"Crop: {crop}")
    print(f"Stage 1 name: '{stage_requirements[0].stage.name}'")
    
    assert stage_requirements[0].stage.name == "播種"
    assert stage_requirements[0].temperature.base_temperature == 5.0
    
    print("✅ Old structure fallback works correctly!")


if __name__ == "__main__":
    test_gateway_parse_flow_result()
    test_gateway_with_old_structure()
