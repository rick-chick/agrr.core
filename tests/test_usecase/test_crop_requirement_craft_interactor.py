import pytest

from agrr_core.usecase.interactors.crop_requirement_craft_interactor import (
    CropRequirementCraftInteractor,
)
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
    CropRequirementCraftRequestDTO,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_success(gateway_crop_requirement, output_port_crop_requirement):
    interactor = CropRequirementCraftInteractor(
        gateway=gateway_crop_requirement,
        presenter=output_port_crop_requirement,
    )

    req = CropRequirementCraftRequestDTO(crop_query="トマト")
    result = await interactor.execute(req)

    assert result["success"] is True
    data = result["data"]
    assert data["crop_id"] == "tomato"
    assert data["crop_name"] == "Tomato"
    assert data["variety"] is None  # "default" is converted to None
    assert isinstance(data["stages"], list)
    assert data["stages"][0]["name"] == "Vegetative"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_empty_query_returns_error(gateway_crop_requirement, output_port_crop_requirement):
    interactor = CropRequirementCraftInteractor(
        gateway=gateway_crop_requirement,
        presenter=output_port_crop_requirement,
    )

    req = CropRequirementCraftRequestDTO(crop_query="   ")
    result = await interactor.execute(req)

    assert result["success"] is False
    assert "Empty crop query" in result["error"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_gateway_exception_returns_error(gateway_crop_requirement, output_port_crop_requirement):
    # Configure gateway to raise on any step
    gateway_crop_requirement.extract_crop_variety.side_effect = RuntimeError("llm error")

    interactor = CropRequirementCraftInteractor(
        gateway=gateway_crop_requirement,
        presenter=output_port_crop_requirement,
    )

    req = CropRequirementCraftRequestDTO(crop_query="トマト")
    result = await interactor.execute(req)

    assert result["success"] is False
    assert "Crafting failed" in result["error"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_includes_family_in_groups(gateway_crop_requirement, output_port_crop_requirement):
    """Test that crop family is extracted and added to groups."""
    interactor = CropRequirementCraftInteractor(
        gateway=gateway_crop_requirement,
        presenter=output_port_crop_requirement,
    )

    req = CropRequirementCraftRequestDTO(crop_query="トマト")
    result = await interactor.execute(req)

    assert result["success"] is True
    data = result["data"]
    
    # Check that groups field exists and contains the family
    assert "groups" in data
    assert data["groups"] is not None
    assert isinstance(data["groups"], list)
    assert len(data["groups"]) > 0
    # The scientific name should be the first element
    assert data["groups"][0] == "Solanaceae"
    
    # Verify that extract_crop_family was called
    gateway_crop_requirement.extract_crop_family.assert_called_once()


