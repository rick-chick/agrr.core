import pytest

from agrr_core.usecase.interactors.crop_requirement_craft_interactor import (
    CropRequirementCraftInteractor,
)
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
    CropRequirementCraftRequestDTO,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_success(mock_crop_requirement_gateway, mock_crop_requirement_output_port):
    interactor = CropRequirementCraftInteractor(
        gateway=mock_crop_requirement_gateway,
        presenter=mock_crop_requirement_output_port,
    )

    req = CropRequirementCraftRequestDTO(crop_query="トマト")
    result = await interactor.execute(req)

    assert result["success"] is True
    data = result["data"]
    assert data["crop_id"] == "tomato"
    assert data["crop_name"] == "Tomato"
    assert data["variety"] is None  # "default" is converted to None
    assert data["area_per_unit"] == 0.5  # From mock
    assert data["revenue_per_area"] == 2000.0  # From mock
    assert isinstance(data["stages"], list)
    assert data["stages"][0]["name"] == "Vegetative"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_empty_query_returns_error(mock_crop_requirement_gateway, mock_crop_requirement_output_port):
    interactor = CropRequirementCraftInteractor(
        gateway=mock_crop_requirement_gateway,
        presenter=mock_crop_requirement_output_port,
    )

    req = CropRequirementCraftRequestDTO(crop_query="   ")
    result = await interactor.execute(req)

    assert result["success"] is False
    assert "Empty crop query" in result["error"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_craft_gateway_exception_returns_error(mock_crop_requirement_gateway, mock_crop_requirement_output_port):
    # Configure gateway to raise on any step
    mock_crop_requirement_gateway.extract_crop_variety.side_effect = RuntimeError("llm error")

    interactor = CropRequirementCraftInteractor(
        gateway=mock_crop_requirement_gateway,
        presenter=mock_crop_requirement_output_port,
    )

    req = CropRequirementCraftRequestDTO(crop_query="トマト")
    result = await interactor.execute(req)

    assert result["success"] is False
    assert "Crafting failed" in result["error"]


