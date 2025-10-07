"""Debug test for the 3-step crop requirement flow.

Note: execute_crop_requirement_flow has been moved from Framework layer to UseCase layer (Interactor).
This test now uses the Interactor directly to test the full flow.
"""

import pytest
import asyncio
import os
from unittest.mock import patch

from agrr_core.framework.services.llm_client_impl import FrameworkLLMClient
from agrr_core.adapter.gateways.crop_requirement_gateway_impl import CropRequirementGatewayImpl
from agrr_core.adapter.presenters.crop_requirement_craft_presenter import CropRequirementCraftPresenter
from agrr_core.usecase.interactors.crop_requirement_craft_interactor import CropRequirementCraftInteractor
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import CropRequirementCraftRequestDTO


@pytest.mark.asyncio
async def test_debug_flow():
    """Test the 3-step flow with debug output enabled."""
    # Enable debug mode
    with patch.dict(os.environ, {"AGRRCORE_DEBUG": "true"}):
        # Set up the full stack: Framework -> Adapter -> UseCase
        llm_client = FrameworkLLMClient()
        gateway = CropRequirementGatewayImpl(llm_client=llm_client)
        presenter = CropRequirementCraftPresenter()
        interactor = CropRequirementCraftInteractor(gateway=gateway, presenter=presenter)
        
        # Test with a simple crop
        request = CropRequirementCraftRequestDTO(crop_query="かぶ")
        result = await interactor.execute(request)
        
        # Check that we get a result
        assert result is not None
        assert "success" in result
        assert result["success"] is True
        assert "data" in result
        
        print(f"\nFinal result: {result}")
        
        # Check crop info
        data = result["data"]
        assert "crop_name" in data
        
        # Check stages
        stages = data.get("stages", [])
        assert len(stages) > 0
        
        # Print stage names for debugging
        print("\nStage names:")
        for i, stage in enumerate(stages):
            stage_name = stage.get("name", "Unknown")
            print(f"  Stage {i+1}: {stage_name}")


if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_debug_flow())
