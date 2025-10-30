"""Optimal growth period calculation input port.

Defines the interface for the optimal growth period calculation use case.
"""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
)

class GrowthPeriodOptimizeInputPort(ABC):
    """Input port for optimal growth period calculation use case."""

    @abstractmethod
    def execute(
        self, request: OptimalGrowthPeriodRequestDTO
    ) -> OptimalGrowthPeriodResponseDTO:
        """Execute the optimal growth period calculation use case.

        Args:
            request: Request DTO containing crop info, candidate dates, and cost parameters

        Returns:
            Response DTO containing optimal period and all candidate evaluations
        """
        pass

