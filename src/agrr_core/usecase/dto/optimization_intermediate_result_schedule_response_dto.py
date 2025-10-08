"""Optimization intermediate result scheduling response DTO.

This DTO carries the output of the weighted interval scheduling algorithm,
containing the optimal selection of non-overlapping cultivation periods with minimum cost.

Fields
- total_cost: Total cost of selected results
- selected_results: List of selected OptimizationIntermediateResult entities (non-overlapping)

The selected_results are ordered by start_date for easy interpretation.
"""

from dataclasses import dataclass
from typing import List

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)


@dataclass
class OptimizationIntermediateResultScheduleResponseDTO:
    """Response DTO for optimization intermediate result scheduling use case."""

    total_cost: float
    selected_results: List[OptimizationIntermediateResult]

    def __post_init__(self):
        """Validate output."""
        if self.total_cost < 0:
            raise ValueError(
                f"total_cost must be non-negative, got {self.total_cost}"
            )
        
        if not isinstance(self.selected_results, list):
            raise TypeError(
                f"selected_results must be a list, got {type(self.selected_results).__name__}"
            )

