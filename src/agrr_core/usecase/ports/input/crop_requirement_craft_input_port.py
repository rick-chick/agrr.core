"""Input port for Crop Requirement Crafter use case.

This input port defines the contract for orchestrating an LLM-backed process
that proposes stage-specific requirement profiles for a given crop.

Action name: craft_stage_requirements

Expected request payload (via DTO, referenced under TYPE_CHECKING):
- crop_id (str): Stable identifier (e.g., "tomato").
- name (str): Human-readable crop name.
- variety (Optional[str]): Variety/cultivar label.
- stages (Optional[List[str]]): Target growth stage names to craft (if None, craft defaults).
- hints (Optional[dict]): Optional metadata/prompts to steer LLM (region, season, protected/open field, etc.).

The interactor should validate inputs, call the gateway(s) that drive the LLM
to infer thresholds for TemperatureProfile, SunshineProfile, and ThermalRequirement
per stage, and return those via an output port as a `CropRequirementAggregate`.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid runtime dependency until DTO is introduced
    from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
        CropRequirementCraftRequestDTO,
    )


class CropRequirementCraftInputPort(ABC):
    """Interface for crafting crop stage requirement profiles (LLM-backed)."""

    @abstractmethod
    async def execute(self, request: "CropRequirementCraftRequestDTO") -> None:
        """Craft stage requirements for the specified crop.

        The implementing interactor should pass the result to its output port.
        """
        pass


