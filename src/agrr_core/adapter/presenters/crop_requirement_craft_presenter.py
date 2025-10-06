"""Adapter: Presenter for crop requirement crafting responses."""

from typing import Dict, Any

from agrr_core.usecase.ports.output.crop_requirement_craft_output_port import (
    CropRequirementCraftOutputPort,
)


class CropRequirementCraftPresenter(CropRequirementCraftOutputPort):
    """Thin presenter that wraps success/error payloads."""

    def format_error(self, error_message: str, error_code: str = "CROP_REQUIREMENT_ERROR") -> Dict[str, Any]:
        return {"success": False, "error": error_message, "code": error_code}

    def format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data": data}


