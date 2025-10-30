"""Allocation result gateway interface.

Gateway for loading existing multi-field allocation results.
Used in allocation adjustment use case to load the current allocation state.

Note:
    Source configuration (file path, database connection, etc.) is provided
    at initialization time, not at method call time.
"""

from abc import ABC, abstractmethod
from typing import Optional

from agrr_core.entity.entities.multi_field_optimization_result_entity import (
    MultiFieldOptimizationResult,
)

class AllocationResultGateway(ABC):
    """Gateway interface for allocation result operations."""
    
    @abstractmethod
    def get_by_id(self, optimization_id: str) -> Optional[MultiFieldOptimizationResult]:
        """Get allocation result by ID.
        
        Args:
            optimization_id: Unique identifier of the allocation result
            
        Returns:
            Allocation result entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get(self) -> Optional[MultiFieldOptimizationResult]:
        """Get allocation result from configured source.
        
        Returns:
            Allocation result entity if found, None otherwise
            
        Note:
            Source is configured at gateway initialization (file, database, API, etc.)
        """
        pass

