"""Optimization intermediate result scheduling interactor.

This interactor implements the weighted interval scheduling algorithm to find
the maximum profit (or minimum cost) combination of non-overlapping cultivation periods.

Algorithm Overview:
1. Filter valid results (completion_date and total_cost must be present)
2. Sort results by completion_date (ascending)
3. Use dynamic programming to find optimal selection:
   - dp[i] = (max_profit, selected_indices) for first i results
   - For each result i, choose between:
     a) Don't select: dp[i+1] = dp[i]
     b) Select: Find last non-overlapping result j, dp[i+1] = dp[j+1] + profit[i]

Time Complexity: O(n²) where n is number of valid results
Space Complexity: O(n)

The algorithm can be improved to O(n log n) using binary search for finding
the last non-overlapping result, but O(n²) is sufficient for typical use cases.
"""

from typing import List, Tuple, Optional

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.usecase.dto.optimization_intermediate_result_schedule_request_dto import (
    OptimizationIntermediateResultScheduleRequestDTO,
)
from agrr_core.usecase.dto.optimization_intermediate_result_schedule_response_dto import (
    OptimizationIntermediateResultScheduleResponseDTO,
)
from agrr_core.usecase.ports.input.optimization_intermediate_result_schedule_input_port import (
    OptimizationIntermediateResultScheduleInputPort,
)
from agrr_core.usecase.gateways.optimization_result_gateway import (
    OptimizationResultGateway,
)
from agrr_core.usecase.interactors.base_optimizer import BaseOptimizer

class OptimizationIntermediateResultScheduleInteractor(
    BaseOptimizer[OptimizationIntermediateResult],
    OptimizationIntermediateResultScheduleInputPort
):
    """Interactor for finding optimal non-overlapping cultivation schedule using unified objective."""

    def __init__(
        self,
        optimization_result_gateway: Optional[OptimizationResultGateway] = None
    ):
        """Initialize the interactor.
        
        Args:
            optimization_result_gateway: Optional gateway for saving schedule results
        """
        super().__init__()  # Initialize BaseOptimizer
        self.optimization_result_gateway = optimization_result_gateway

    def execute(
        self, request: OptimizationIntermediateResultScheduleRequestDTO,
        schedule_id: Optional[str] = None
    ) -> OptimizationIntermediateResultScheduleResponseDTO:
        """Execute the scheduling algorithm.

        Args:
            request: Request DTO containing list of optimization intermediate results

        Returns:
            Response DTO containing total cost and selected non-overlapping results
        """
        # Filter valid results (must have completion_date, growth_days, and field for cost calculation)
        valid_results = [
            r
            for r in request.results
            if r.completion_date is not None and r.growth_days is not None and r.field is not None
        ]

        # Handle empty case
        if not valid_results:
            return OptimizationIntermediateResultScheduleResponseDTO(
                total_cost=0.0, selected_results=[]
            )

        # Sort by completion_date (ascending)
        sorted_results = sorted(valid_results, key=lambda x: x.completion_date)

        # Run dynamic programming algorithm (unified objective: maximize profit)
        max_profit, selected_indices = self._find_optimal_schedule(sorted_results)

        # Build selected results list
        selected_results = [sorted_results[i] for i in selected_indices]
        
        # Calculate total cost for compatibility
        total_cost = sum(r.total_cost for r in selected_results)

        # Save schedule if gateway is available and schedule_id is provided
        if self.optimization_result_gateway and schedule_id:
            self.optimization_result_gateway.save(
                optimization_id=schedule_id,
                results=selected_results,
                total_cost=total_cost
            )

        return OptimizationIntermediateResultScheduleResponseDTO(
            total_cost=total_cost, selected_results=selected_results
        )

    def _find_optimal_schedule(
        self, sorted_results: List[OptimizationIntermediateResult]
    ) -> Tuple[float, List[int]]:
        """Find optimal schedule using dynamic programming (unified objective).

        Goal: Select as many non-overlapping intervals as possible,
        then maximize total profit (minimize cost if revenue is unknown).

        Strategy:
        1. Prioritize number of intervals (maximize coverage)
        2. Among solutions with same count, maximize total profit

        Args:
            sorted_results: Results sorted by completion_date

        Returns:
            Tuple of (maximum total profit, list of selected indices)
        """
        n = len(sorted_results)

        # dp[i] = (count, total_profit, selected_indices) for considering results 0..i-1
        # Prioritize: max count (coverage), then max profit
        dp: List[Tuple[int, float, List[int]]] = [(0, 0.0, [])] + [(0, float("-inf"), []) for _ in range(n)]

        for i in range(n):
            # Option 1: Don't select result i (inherit previous state)
            if dp[i][0] > dp[i + 1][0] or (dp[i][0] == dp[i + 1][0] and dp[i][1] > dp[i + 1][1]):
                dp[i + 1] = dp[i]
            
            # Option 2: Select result i
            last_non_overlapping = self._find_last_non_overlapping(sorted_results, i)
            
            prev_count, prev_profit, prev_indices = dp[last_non_overlapping + 1]
            
            # Calculate profit for this result using unified objective (BaseOptimizer)
            result_profit = self.calculate_value(sorted_results[i])
            
            new_count = prev_count + 1
            new_profit = prev_profit + result_profit
            new_indices = prev_indices[:] + [i]

            # Update if selecting gives better solution
            # Better = more intervals, or same intervals but higher profit
            if (new_count > dp[i + 1][0] or 
                (new_count == dp[i + 1][0] and new_profit > dp[i + 1][1])):
                dp[i + 1] = (new_count, new_profit, new_indices)

        # Return the best solution
        best_count, best_profit, best_indices = dp[n]
        return (best_profit, best_indices)

    def _find_last_non_overlapping(
        self, sorted_results: List[OptimizationIntermediateResult], current_idx: int
    ) -> int:
        """Find the last result that doesn't overlap with current result.

        Two results don't overlap if:
        earlier_result.completion_date <= later_result.start_date

        Args:
            sorted_results: Results sorted by completion_date
            current_idx: Index of current result

        Returns:
            Index of last non-overlapping result, or -1 if none found
        """
        current_result = sorted_results[current_idx]

        # Search backwards from current_idx - 1
        for j in range(current_idx - 1, -1, -1):
            if sorted_results[j].completion_date <= current_result.start_date:
                return j

        return -1

