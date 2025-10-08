"""Gateway interface for optimization intermediate results.

This gateway defines the contract for storing and retrieving optimization
intermediate results. Implementations should provide storage mechanisms
(e.g., in-memory, database, file system) for these results.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)


class OptimizationResultGateway(ABC):
    """Gateway interface for optimization result storage operations."""

    @abstractmethod
    async def save(
        self, 
        optimization_id: str,
        results: List[OptimizationIntermediateResult],
        total_cost: Optional[float] = None
    ) -> None:
        """Save optimization intermediate results.
        
        Args:
            optimization_id: Unique identifier for this optimization run
            results: List of intermediate results to save
            total_cost: Optional total cost metadata (used for schedules)
        """
        pass

    @abstractmethod
    async def get(
        self, 
        optimization_id: str
    ) -> Optional[OptimizationSchedule]:
        """Retrieve optimization results by ID.
        
        Returns a unified OptimizationSchedule entity that can represent:
        - Intermediate results (total_cost = None)
        - Scheduled results (total_cost = float)
        
        Args:
            optimization_id: Unique identifier for the optimization run
            
        Returns:
            OptimizationSchedule entity, or None if not found
        """
        pass

    @abstractmethod
    async def get_all(self) -> List[OptimizationSchedule]:
        """Retrieve all stored optimization results.
        
        Returns:
            List of OptimizationSchedule entities (includes both intermediate results and schedules)
        """
        pass

    @abstractmethod
    async def delete(self, optimization_id: str) -> bool:
        """Delete optimization intermediate results by ID.
        
        Args:
            optimization_id: Unique identifier for the optimization run
            
        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all stored optimization results (both intermediate results and schedules)."""
        pass

    @abstractmethod
    async def clear_schedules(self) -> None:
        """Clear only scheduled results (where total_cost is not None).
        
        Preserves intermediate optimization results without total_cost.
        """
        pass

