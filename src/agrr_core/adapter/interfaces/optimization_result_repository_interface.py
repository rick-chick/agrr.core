"""Optimization result repository interface for adapter layer.

This interface defines the contract for optimization result data storage,
allowing different implementations (in-memory, file-based, database, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)


class OptimizationResultRepositoryInterface(ABC):
    """Abstract interface for optimization result repository.
    
    Implementations can be:
    - InMemoryOptimizationResultRepository (for testing/runtime storage)
    - FileOptimizationResultRepository (for persistent storage)
    - DatabaseOptimizationResultRepository (for production use)
    """
    
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
            List of OptimizationSchedule entities
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
    
    @abstractmethod
    async def clear_schedules(self) -> None:
        """Clear all stored optimization schedules."""
        pass

