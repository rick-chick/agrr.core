"""In-memory repository for optimization intermediate results.

This repository provides in-memory storage for optimization intermediate results
using a dictionary data structure. Data is stored in memory and will be lost
when the application terminates.
"""

from typing import Dict, List, Optional, Tuple

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)


class InMemoryOptimizationResultRepository:
    """In-memory repository for storing optimization intermediate results."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._storage: Dict[str, List[OptimizationIntermediateResult]] = {}

    async def save(
        self, 
        optimization_id: str,
        results: List[OptimizationIntermediateResult]
    ) -> None:
        """Save optimization intermediate results.
        
        Args:
            optimization_id: Unique identifier for this optimization run
            results: List of intermediate results to save
        """
        self._storage[optimization_id] = results

    async def get(
        self, 
        optimization_id: str
    ) -> Optional[List[OptimizationIntermediateResult]]:
        """Retrieve optimization intermediate results by ID.
        
        Args:
            optimization_id: Unique identifier for the optimization run
            
        Returns:
            List of intermediate results, or None if not found
        """
        return self._storage.get(optimization_id)

    async def get_all(self) -> List[Tuple[str, List[OptimizationIntermediateResult]]]:
        """Retrieve all stored optimization results.
        
        Returns:
            List of tuples (optimization_id, results)
        """
        return [(opt_id, results) for opt_id, results in self._storage.items()]

    async def delete(self, optimization_id: str) -> bool:
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

    async def clear(self) -> None:
        """Clear all stored optimization results."""
        self._storage.clear()

