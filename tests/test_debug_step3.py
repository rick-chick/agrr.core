"""Debug test for Step 3 response structure parsing."""

import pytest


def test_step3_response_structure_parsing():
    """Test how we parse the actual Step 3 response structure."""
    
    # Simulate the actual Step 3 response structure from debug output
    mock_step3_response = {
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
    }
    
    print("Testing Step 3 response structure parsing:")
    
    # Test the parsing logic from _parse_flow_result
    stage_data = mock_step3_response
    
    if "stage" in stage_data:
        print("  Found 'stage' key in stage_data")
        stage_info = stage_data["stage"]
        stage_name = stage_info.get("name", "Unknown Stage")
        
        print(f"    Stage name: '{stage_name}'")
        
        # Parse temperature profile
        temp_data = stage_info.get("temperature_requirements") or stage_info.get("temperature", {})
        temp_range = temp_data.get("optimal_temperature_range", {})
        
        print(f"    Temperature data: {temp_data}")
        print(f"    Temperature range: {temp_range}")
        
        base_temp = temp_data.get("base_temperature", 10.0)
        optimal_min = temp_range.get("night") or temp_data.get("optimal_min", 20.0)
        optimal_max = temp_range.get("day") or temp_data.get("optimal_max", 26.0)
        
        print(f"    Parsed values:")
        print(f"      base_temperature: {base_temp}")
        print(f"      optimal_min: {optimal_min}")
        print(f"      optimal_max: {optimal_max}")
        
        # Parse sunshine profile
        sun_data = stage_info.get("sunlight_requirements") or stage_info.get("light_requirements") or stage_info.get("sunshine", {})
        print(f"    Sunshine data: {sun_data}")
        
        min_sun = sun_data.get("minimum_sunlight_hours", 3.0)
        target_sun = sun_data.get("target_sunlight_hours", 6.0)
        
        print(f"      minimum_sunshine_hours: {min_sun}")
        print(f"      target_sunshine_hours: {target_sun}")
        
        # Parse thermal requirement
        thermal_data = stage_info.get("accumulated_temperature") or stage_info.get("growing_degree_days") or stage_info.get("thermal", {})
        print(f"    Thermal data: {thermal_data}")
        
        required_gdd = thermal_data.get("required_gdd", 400.0)
        print(f"      required_gdd: {required_gdd}")
        
        # Assertions
        assert stage_name == "播種"
        assert base_temp == 5.0
        assert optimal_min == 10.0
        assert optimal_max == 15.0
        assert min_sun == 3.0
        assert target_sun == 6.0
        assert required_gdd == 200.0
        
        print("  ✅ All parsing assertions passed!")
    else:
        print("  ❌ No 'stage' key found in stage_data")


def test_step3_expected_vs_actual_structure():
    """Test the difference between expected and actual Step 3 structure."""
    
    # Expected structure (what we defined in the schema)
    expected_structure = {
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
    
    # Actual structure (what LLM returns)
    actual_structure = {
        "stage": {
            "name": "播種",
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
    }
    
    print("\nStep 3 structure comparison:")
    print(f"Expected top-level keys: {list(expected_structure.keys())}")
    print(f"Actual top-level keys: {list(actual_structure.keys())}")
    
    expected_temp_keys = list(expected_structure["temperature"].keys())
    actual_temp_keys = list(actual_structure["stage"]["temperature_requirements"].keys())
    
    print(f"\nExpected temperature keys: {expected_temp_keys}")
    print(f"Actual temperature keys: {actual_temp_keys}")
    
    expected_sun_keys = list(expected_structure["sunshine"].keys())
    actual_sun_keys = list(actual_structure["stage"]["sunlight_requirements"].keys())
    
    print(f"\nExpected sunshine keys: {expected_sun_keys}")
    print(f"Actual sunshine keys: {actual_sun_keys}")


if __name__ == "__main__":
    test_step3_response_structure_parsing()
    test_step3_expected_vs_actual_structure()
