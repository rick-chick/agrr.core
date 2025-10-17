"""Service for checking allocation feasibility.

This service validates whether an allocation solution respects all constraints
such as time overlap and area capacity.
"""

from typing import List, Dict, Optional

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.dto.optimization_config import OptimizationConfig


class AllocationFeasibilityChecker:
    """Check if allocation solutions are feasible.
    
    Responsibilities:
    - Validate time overlap constraints
    - Validate area capacity constraints
    - Provide efficient constraint checking
    
    Design Pattern:
    - Validator Pattern: Validates business rules
    - Future: Strategy Pattern for different checking algorithms (Interval Tree)
    
    Time Complexity:
    - Current: O(n²) for time overlap check
    - Future: O(n log n) with Interval Tree
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        """Initialize the feasibility checker.
        
        Args:
            config: Optimization configuration
        """
        self.config = config or OptimizationConfig()
    
    def is_feasible(self, allocations: List[CropAllocation]) -> bool:
        """Check if solution respects all constraints.
        
        Validates:
        1. Time overlap: No overlapping allocations in same field
        2. Area capacity: Total area does not exceed field capacity
        
        Args:
            allocations: List of allocations to validate
            
        Returns:
            True if solution is feasible, False otherwise
            
        Example:
            >>> checker = AllocationFeasibilityChecker()
            >>> allocations = [alloc1, alloc2, alloc3]
            >>> checker.is_feasible(allocations)
            True
        """
        return (
            self._check_time_constraints(allocations) and
            self._check_area_constraints(allocations)
        )
    
    def _check_time_constraints(
        self,
        allocations: List[CropAllocation]
    ) -> bool:
        """Check that no allocations overlap in time within the same field.
        
        For each field, verify that all allocations have non-overlapping
        time periods.
        
        Time Complexity: O(n²) where n is number of allocations per field
        
        Args:
            allocations: List of allocations to check
            
        Returns:
            True if no time overlaps exist, False otherwise
        """
        # Group allocations by field
        field_allocations: Dict[str, List[CropAllocation]] = {}
        for alloc in allocations:
            field_id = alloc.field.field_id
            if field_id not in field_allocations:
                field_allocations[field_id] = []
            field_allocations[field_id].append(alloc)
        
        # Check for overlaps within each field (including fallow period)
        for field_id, field_allocs in field_allocations.items():
            for i, alloc1 in enumerate(field_allocs):
                for alloc2 in field_allocs[i+1:]:
                    if alloc1.overlaps_with_fallow(alloc2):
                        return False  # Found overlap (considering fallow period)
        
        return True  # No overlaps found
    
    def _check_area_constraints(
        self,
        allocations: List[CropAllocation]
    ) -> bool:
        """Check that total area usage does not exceed field capacity.
        
        Note: This is currently handled implicitly during candidate generation
        and neighbor operations, but an explicit check provides safety.
        
        A small tolerance (1%) is allowed to handle floating point errors.
        
        Args:
            allocations: List of allocations to check
            
        Returns:
            True if all fields respect area capacity, False otherwise
        """
        # Calculate area usage per field
        field_area_usage: Dict[str, Dict[str, float]] = {}
        
        for alloc in allocations:
            field_id = alloc.field.field_id
            if field_id not in field_area_usage:
                field_area_usage[field_id] = {
                    'used': 0.0,
                    'capacity': alloc.field.area
                }
            field_area_usage[field_id]['used'] += alloc.area_used
        
        # Check capacity for each field
        for field_id, usage in field_area_usage.items():
            # Allow 1% tolerance for floating point errors
            if usage['used'] > usage['capacity'] * 1.01:
                return False  # Capacity exceeded
        
        return True  # All fields within capacity

