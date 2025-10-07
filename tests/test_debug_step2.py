"""Debug test for Step 2 response structure parsing."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_step2_response_structure_parsing():
    """Test how we parse the actual Step 2 response structure."""
    
    # Simulate the actual Step 2 response structure from debug output
    mock_step2_response = {
        "crop": "かぶ",
        "growth_stages": [
            {
                "stage": "播種",
                "start_condition": "種子を土壌に播く",
                "end_condition": "発芽が始まる",
                "characteristics": {
                    "main_growth_process": "種子の発芽",
                    "morphological_changes": "根が土壌に伸び始める",
                    "physiological_changes": "水分吸収が始まる",
                    "management_points": "土壌の湿度管理、播種深さの確認"
                }
            },
            {
                "stage": "苗期",
                "start_condition": "発芽が完了し、葉が展開し始める",
                "end_condition": "本葉が数枚展開する",
                "characteristics": {
                    "main_growth_process": "葉の成長と根の発達",
                    "morphological_changes": "本葉の展開",
                    "physiological_changes": "光合成の開始",
                    "management_points": "肥料の施用、病害虫の監視"
                }
            }
        ]
    }
    
    # Test the parsing logic from llm_client_impl.py
    growth_stages = mock_step2_response.get("growth_stages", [])
    
    print("Testing Step 2 response structure parsing:")
    for i, stage in enumerate(growth_stages):
        # Current parsing logic from execute_crop_requirement_flow
        stage_name = stage.get("stage_name") or stage.get("stage", "Unknown Stage")
        stage_description = stage.get("description") or stage.get("start_condition", "")
        
        print(f"  Stage {i+1}:")
        print(f"    Raw stage data: {stage}")
        print(f"    Parsed stage_name: '{stage_name}'")
        print(f"    Parsed stage_description: '{stage_description}'")
        print(f"    Has 'stage_name' field: {'stage_name' in stage}")
        print(f"    Has 'stage' field: {'stage' in stage}")
        print(f"    Has 'description' field: {'description' in stage}")
        print(f"    Has 'start_condition' field: {'start_condition' in stage}")
        print()
        
        # Assertions
        assert stage_name == stage["stage"], f"Expected '{stage['stage']}', got '{stage_name}'"
        assert stage_description == stage["start_condition"], f"Expected '{stage['start_condition']}', got '{stage_description}'"


@pytest.mark.asyncio
async def test_step2_expected_vs_actual_structure():
    """Test the difference between expected and actual Step 2 structure."""
    
    # Expected structure (what we defined in the schema)
    expected_structure = {
        "crop_name": "かぶ",
        "growth_stages": [
            {
                "stage_name": "播種",
                "description": "種子を土壌に播く"
            }
        ]
    }
    
    # Actual structure (what LLM returns)
    actual_structure = {
        "crop": "かぶ",
        "growth_stages": [
            {
                "stage": "播種",
                "start_condition": "種子を土壌に播く",
                "end_condition": "発芽が始まる",
                "characteristics": {...}
            }
        ]
    }
    
    print("Structure comparison:")
    print(f"Expected: {expected_structure}")
    print(f"Actual: {actual_structure}")
    
    # Test field access
    expected_stage = expected_structure["growth_stages"][0]
    actual_stage = actual_structure["growth_stages"][0]
    
    print(f"\nExpected stage fields: {list(expected_stage.keys())}")
    print(f"Actual stage fields: {list(actual_stage.keys())}")
    
    # Test the current parsing logic
    stage_name_from_expected = expected_stage.get("stage_name", "Unknown Stage")
    stage_name_from_actual = actual_stage.get("stage_name") or actual_stage.get("stage", "Unknown Stage")
    
    print(f"\nStage name from expected structure: '{stage_name_from_expected}'")
    print(f"Stage name from actual structure: '{stage_name_from_actual}'")
    
    assert stage_name_from_expected == "播種"
    assert stage_name_from_actual == "播種"


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_step2_response_structure_parsing())
    asyncio.run(test_step2_expected_vs_actual_structure())
