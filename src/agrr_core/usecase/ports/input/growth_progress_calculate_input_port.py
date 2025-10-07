"""Growth progress calculation input port.

Defines the interface for the growth progress calculation use case.
"""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.growth_progress_calculate_request_dto import (
    GrowthProgressCalculateRequestDTO,
)
from agrr_core.usecase.dto.growth_progress_calculate_response_dto import (
    GrowthProgressCalculateResponseDTO,
)


class GrowthProgressCalculateInputPort(ABC):
    """Input port for growth progress calculation use case."""

    @abstractmethod
    async def execute(
        self, request: GrowthProgressCalculateRequestDTO
    ) -> GrowthProgressCalculateResponseDTO:
        """Execute the growth progress calculation use case.

        Args:
            request: Request DTO containing crop info, location, and date range

        Returns:
            Response DTO containing daily growth progress records
        """
        pass

