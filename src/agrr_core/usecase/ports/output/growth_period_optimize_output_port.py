"""Optimal growth period calculation output port.

Defines the interface for presenting optimal growth period calculation results.
"""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
)

class GrowthPeriodOptimizeOutputPort(ABC):
    """Output port for optimal growth period calculation use case."""

    @abstractmethod
    def present(self, response: OptimalGrowthPeriodResponseDTO) -> None:
        """Present the optimal growth period calculation results.

        Args:
            response: Response DTO containing optimal period and candidate comparisons
        """
        pass

