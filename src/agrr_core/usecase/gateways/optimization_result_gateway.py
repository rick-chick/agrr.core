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


class OptimizationResultGateway(ABC):
    """Gateway interface for optimization result storage operations."""

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_all(self) -> List[Tuple[str, List[OptimizationIntermediateResult]]]:
        """Retrieve all stored optimization results.
        
        Returns:
            List of tuples (optimization_id, results)
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
        """Clear all stored optimization results."""
        pass

