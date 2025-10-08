"""Optimization intermediate result scheduling input port.

Defines the interface for the optimization intermediate result scheduling use case.
This use case finds the minimum cost combination of non-overlapping cultivation periods
using weighted interval scheduling algorithm.
"""

from abc import ABC, abstractmethod
from typing import Optional

from agrr_core.usecase.dto.optimization_intermediate_result_schedule_request_dto import (
    OptimizationIntermediateResultScheduleRequestDTO,
)
from agrr_core.usecase.dto.optimization_intermediate_result_schedule_response_dto import (
    OptimizationIntermediateResultScheduleResponseDTO,
)


class OptimizationIntermediateResultScheduleInputPort(ABC):
    """Input port for optimization intermediate result scheduling use case."""

    @abstractmethod
    async def execute(
        self, 
        request: OptimizationIntermediateResultScheduleRequestDTO,
        schedule_id: Optional[str] = None
    ) -> OptimizationIntermediateResultScheduleResponseDTO:
        """Execute the optimization intermediate result scheduling use case.

        Args:
            request: Request DTO containing list of optimization intermediate results
            schedule_id: Optional ID to save the schedule result in gateway

        Returns:
            Response DTO containing total cost and selected non-overlapping results
        """
        pass

