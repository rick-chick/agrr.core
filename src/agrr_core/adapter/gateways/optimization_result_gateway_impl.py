"""Optimization result gateway implementation.

This gateway implementation provides access to optimization intermediate results
through a repository interface (e.g., InMemoryRepository).
"""

from typing import List, Optional, Tuple

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)
from agrr_core.usecase.gateways.optimization_result_gateway import (
    OptimizationResultGateway,
)


class OptimizationResultGatewayImpl(OptimizationResultGateway):
    """Implementation of optimization result gateway."""

    def __init__(self, repository):
        """Initialize optimization result gateway.
        
        Args:
            repository: Repository implementation with save/get/delete/clear methods
        """
        self.repository = repository

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
        await self.repository.save(optimization_id, results, total_cost)

    async def get(
        self, 
        optimization_id: str
    ) -> Optional[OptimizationSchedule]:
        """Retrieve optimization results by ID.
        
        Returns a unified OptimizationSchedule entity.
        
        Args:
            optimization_id: Unique identifier for the optimization run
            
        Returns:
            OptimizationSchedule entity, or None if not found
        """
        return await self.repository.get(optimization_id)

    async def get_all(self) -> List[OptimizationSchedule]:
        """Retrieve all stored optimization results.
        
        Returns:
            List of OptimizationSchedule entities
        """
        return await self.repository.get_all()

    async def delete(self, optimization_id: str) -> bool:
        """Delete optimization intermediate results by ID.
        
        Args:
            optimization_id: Unique identifier for the optimization run
            
        Returns:
            True if deleted, False if not found
        """
        return await self.repository.delete(optimization_id)

    async def clear(self) -> None:
        """Clear all stored optimization results."""
        await self.repository.clear()

    async def clear_schedules(self) -> None:
        """Clear all stored optimization schedules."""
        await self.repository.clear_schedules()

