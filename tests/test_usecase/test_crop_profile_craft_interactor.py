import pytest

from agrr_core.usecase.interactors.crop_profile_craft_interactor import (
    CropProfileCraftInteractor,
)
from agrr_core.usecase.dto.crop_profile_craft_request_dto import (
    CropProfileCraftRequestDTO,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_success(gateway_crop_profile, output_port_crop_profile):
    interactor = CropProfileCraftInteractor(
        gateway=gateway_crop_profile,
        presenter=output_port_crop_profile,
    )

    req = CropProfileCraftRequestDTO(crop_query="トマト")
    result = await interactor.execute(req)

    # Check new format: {"crop": {...}, "stage_requirements": [...]}
    assert "crop" in result
    assert "stage_requirements" in result
    
    crop = result["crop"]
    assert crop["crop_id"] == "tomato"
    assert crop["name"] == "Tomato"
    assert crop["variety"] is None  # "default" is converted to None
    
    assert isinstance(result["stage_requirements"], list)
    assert result["stage_requirements"][0]["stage"]["name"] == "Vegetative"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_empty_query_returns_error(gateway_crop_profile, output_port_crop_profile):
    interactor = CropProfileCraftInteractor(
        gateway=gateway_crop_profile,
        presenter=output_port_crop_profile,
    )

    req = CropProfileCraftRequestDTO(crop_query="   ")
    result = await interactor.execute(req)

    assert result["success"] is False
    assert "Empty crop query" in result["error"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_gateway_exception_returns_error(gateway_crop_profile, output_port_crop_profile):
    # Configure gateway to raise on any step
    gateway_crop_profile.extract_crop_variety.side_effect = RuntimeError("llm error")

    interactor = CropProfileCraftInteractor(
        gateway=gateway_crop_profile,
        presenter=output_port_crop_profile,
    )

    req = CropProfileCraftRequestDTO(crop_query="トマト")
    result = await interactor.execute(req)

    assert result["success"] is False
    assert "Crafting failed" in result["error"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_includes_family_in_groups(gateway_crop_profile, output_port_crop_profile):
    """Test that crop family is extracted and added to groups."""
    interactor = CropProfileCraftInteractor(
        gateway=gateway_crop_profile,
        presenter=output_port_crop_profile,
    )

    req = CropProfileCraftRequestDTO(crop_query="トマト")
    result = await interactor.execute(req)

    # Check new format
    assert "crop" in result
    crop = result["crop"]
    
    # Check that groups field exists and contains the family
    assert "groups" in crop
    assert crop["groups"] is not None
    assert isinstance(crop["groups"], list)
    assert len(crop["groups"]) > 0
    # The scientific name should be the first element
    assert crop["groups"][0] == "Solanaceae"
    
    # Verify that extract_crop_family was called
    gateway_crop_profile.extract_crop_family.assert_called_once()
    
    # Note: harvest_start_gdd validation is already covered by:
    # - tests/test_entity/test_thermal_requirement_entity.py (14 tests)
    # - tests/test_integration/test_harvest_start_gdd_data_flow.py (4 tests)
    # - tests/test_usecase/test_services/test_llm_response_normalizer.py (2 tests)
    # - tests/test_usecase/test_services/test_crop_profile_mapper.py (3 tests)
    # No need for additional CropProfileCraftInteractor tests


