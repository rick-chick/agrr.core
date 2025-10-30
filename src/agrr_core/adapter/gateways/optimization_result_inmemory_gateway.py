"""In-memory optimization result gateway implementation.

This gateway directly implements OptimizationResultGateway interface for in-memory optimization result storage.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)
from agrr_core.usecase.gateways.optimization_result_gateway import OptimizationResultGateway

@dataclass
class StoredOptimizationResult:
    """Container for stored optimization results with optional metadata."""
    results: List[OptimizationIntermediateResult]
    total_cost: Optional[float] = None

class OptimizationResultInMemoryGateway(OptimizationResultGateway):
    """In-memory gateway for storing optimization intermediate results.
    
    Directly implements OptimizationResultGateway interface without intermediate layers.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._storage: Dict[str, StoredOptimizationResult] = {}

    def save(
        self, 
        optimization_id: str,
        results: List[OptimizationIntermediateResult],
        total_cost: Optional[float] = None
    ) -> None:
        """Save optimization intermediate results.
        
        Args:
            optimization_id: Unique identifier for this optimization run
            results: List of intermediate results to save
            total_cost: Optional total cost (used for schedules)
        """
        self._storage[optimization_id] = StoredOptimizationResult(
            results=results,
            total_cost=total_cost
        )

    def get(
        self, 
        optimization_id: str
    ) -> Optional[OptimizationSchedule]:
        """Retrieve optimization results by ID.
        
        Args:
            optimization_id: Unique identifier for the optimization run
            
        Returns:
            OptimizationSchedule entity, or None if not found
        """
        stored = self._storage.get(optimization_id)
        if stored:
            return OptimizationSchedule(
                schedule_id=optimization_id,
                selected_results=stored.results,
                total_cost=stored.total_cost
            )
        return None

    def get_all(self) -> List[OptimizationSchedule]:
        """Retrieve all stored optimization results.
        
        Returns:
            List of OptimizationSchedule entities
        """
        return [
            OptimizationSchedule(
                schedule_id=opt_id,
                selected_results=stored.results,
                total_cost=stored.total_cost
            )
            for opt_id, stored in self._storage.items()
        ]

    def delete(self, optimization_id: str) -> bool:
        """Delete optimization intermediate results by ID.
        
        Args:
            optimization_id: Unique identifier for the optimization run
            
        Returns:
            True if deleted, False if not found
        """
        if optimization_id in self._storage:
            del self._storage[optimization_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all stored optimization results."""
        self._storage.clear()

    def clear_schedules(self) -> None:
        """Clear all stored optimization schedules.
        
        Only clears entries with total_cost (schedules), preserves regular results.
        """
        schedule_ids = [
            opt_id for opt_id, stored in self._storage.items()
            if stored.total_cost is not None
        ]
        for schedule_id in schedule_ids:
            del self._storage[schedule_id]

