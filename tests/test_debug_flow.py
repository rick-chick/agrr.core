"""Debug test for the 3-step crop requirement flow."""

import pytest
import asyncio
import os
from unittest.mock import patch

from agrr_core.framework.services.llm_client_impl import FrameworkLLMClient


@pytest.mark.asyncio
async def test_debug_flow():
    """Test the 3-step flow with debug output enabled."""
    # Enable debug mode
    with patch.dict(os.environ, {"AGRRCORE_DEBUG": "true"}):
        client = FrameworkLLMClient()
        
        # Test with a simple crop
        result = await client.execute_crop_requirement_flow("かぶ")
        
        # Check that we get a result
        assert result is not None
        assert "crop_info" in result
        assert "stages" in result
        
        print(f"\nFinal result: {result}")
        
        # Check crop info
        crop_info = result["crop_info"]
        assert crop_info["name"] == "かぶ"
        
        # Check stages
        stages = result["stages"]
        assert len(stages) > 0
        
        # Print stage names for debugging
        print("\nStage names:")
        for i, stage in enumerate(stages):
            stage_name = stage.get("name", "Unknown")
            print(f"  Stage {i+1}: {stage_name}")


if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_debug_flow())
