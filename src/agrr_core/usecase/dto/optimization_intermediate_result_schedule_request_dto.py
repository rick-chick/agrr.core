"""Optimization intermediate result scheduling request DTO.

This DTO carries the input parameters for finding the minimum cost combination
of non-overlapping optimization intermediate results using weighted interval scheduling.

The algorithm finds the optimal subset of results where:
1. No two selected results have overlapping cultivation periods
2. Total cost is minimized

Fields
- results: List of OptimizationIntermediateResult entities to schedule

Example:
    Given 4 cultivation periods:
    - Period A: Jan 1-10, cost 1000
    - Period B: Jan 5-15, cost 800 (overlaps with A)
    - Period C: Jan 11-20, cost 600 (compatible with A)
    - Period D: Jan 21-30, cost 700 (compatible with all)
    
    Algorithm will find minimum cost non-overlapping combination,
    which might be B+D (1500) instead of A+C+D (2300).
"""

from dataclasses import dataclass
from typing import List

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)

@dataclass
class OptimizationIntermediateResultScheduleRequestDTO:
    """Request DTO for optimization intermediate result scheduling use case."""

    results: List[OptimizationIntermediateResult]

    def __post_init__(self):
        """Validate input parameters."""
        if not isinstance(self.results, list):
            raise TypeError(
                f"results must be a list, got {type(self.results).__name__}"
            )

