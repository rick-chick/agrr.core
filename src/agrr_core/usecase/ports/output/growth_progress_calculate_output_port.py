"""Growth progress calculation output port.

Defines the interface for presenting growth progress calculation results.
"""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.growth_progress_calculate_response_dto import (
    GrowthProgressCalculateResponseDTO,
)

class GrowthProgressCalculateOutputPort(ABC):
    """Output port for growth progress calculation results."""

    @abstractmethod
    def present(self, response: GrowthProgressCalculateResponseDTO) -> None:
        """Present the growth progress calculation results.

        Args:
            response: Response DTO containing growth progress timeline
        """
        pass

