"""Gateway interface for crafting crop stage requirements (LLM-backed)."""

from abc import ABC, abstractmethod
from typing import Protocol

from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import (
    CropRequirementCraftRequestDTO,
)


class CropRequirementGateway(ABC):
    """Gateway for inferring crop requirements from external services/LLMs."""

    @abstractmethod
    async def craft(self, request: CropRequirementCraftRequestDTO) -> CropRequirementAggregate:
        """Infer and assemble a CropRequirementAggregate from the request."""
        pass


