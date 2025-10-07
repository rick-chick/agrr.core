"""Debug test for stage name normalization."""

from agrr_core.adapter.gateways.crop_requirement_gateway_impl import CropRequirementGatewayImpl


def test_normalize_stage_name():
    """Test the _normalize_stage_name method with various inputs."""
    
    gateway = CropRequirementGatewayImpl(llm_client=None)
    
    # Test cases from Step 2
    test_cases = [
        {"stage_name": "播種期", "expected": "播種期"},
        {"ステージ名": "生育期", "expected": "生育期"},
        {"stage": "収穫期", "expected": "収穫期"},
        {"name": "発芽期", "expected": "発芽期"},
        {}, # No stage name
    ]
    
    print("Testing _normalize_stage_name:")
    for i, test_case in enumerate(test_cases):
        result = gateway._normalize_stage_name(test_case)
        expected = test_case.get("expected", "Unknown Stage")
        status = "✅" if result == expected else "❌"
        print(f"  Test {i+1}: {status} Input: {test_case} -> Output: '{result}' (Expected: '{expected}')")
        
        if result != expected:
            print(f"    FAILED: Got '{result}' but expected '{expected}'")


def test_normalize_with_nested_stage():
    """Test normalization with nested 'stage' structure from Step 3."""
    
    gateway = CropRequirementGatewayImpl(llm_client=None)
    
    # Step 3 structure
    test_case = {
        "stage": {
            "name": "播種",
            "temperature_requirements": {}
        }
    }
    
    print("\nTesting nested stage structure:")
    print(f"  Input: {test_case}")
    
    # This should extract from nested structure
    if "stage" in test_case and isinstance(test_case["stage"], dict):
        stage_info = test_case["stage"]
        result = gateway._normalize_stage_name(stage_info)
        print(f"  Output: '{result}'")
        print(f"  Expected: '播種'")
        print(f"  Status: {'✅' if result == '播種' else '❌'}")
    else:
        result = gateway._normalize_stage_name(test_case)
        print(f"  Output: '{result}'")
        print(f"  Status: ❌ (should have been handled as nested structure)")


if __name__ == "__main__":
    test_normalize_stage_name()
    test_normalize_with_nested_stage()

