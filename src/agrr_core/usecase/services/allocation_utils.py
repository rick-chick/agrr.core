"""Shared utility functions for allocation optimization.

This module provides common functionality used by both Local Search
and ALNS optimization algorithms.

Design Pattern: Utility Class (Static Methods)
Purpose: DRY (Don't Repeat Yourself) - Eliminate code duplication
"""

import uuid
from typing import List, Dict, Any
from datetime import datetime

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation

class AllocationUtils:
    """Shared utility methods for allocation optimization.
    
    Used by:
    - Local Search (Hill Climbing) neighbor operations
    - ALNS destroy and repair operators
    - Multi-field allocation interactor
    
    Benefits:
    - Eliminates code duplication (200-300 lines saved)
    - Ensures consistency across all operations
    - Simplifies testing (test once, use everywhere)
    - Easy to maintain and extend
    """
    
    @staticmethod
    def time_overlaps(
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> bool:
        """Check if two time periods overlap.
        
        Two periods overlap if one starts before the other ends.
        
        Args:
            start1: Start time of period 1
            end1: End time of period 1
            start2: Start time of period 2
            end2: End time of period 2
            
        Returns:
            True if periods overlap, False otherwise
            
        Examples:
            >>> start1 = datetime(2025, 1, 1)
            >>> end1 = datetime(2025, 3, 1)
            >>> start2 = datetime(2025, 2, 1)
            >>> end2 = datetime(2025, 4, 1)
            >>> AllocationUtils.time_overlaps(start1, end1, start2, end2)
            True
            
            >>> start2 = datetime(2025, 3, 2)
            >>> AllocationUtils.time_overlaps(start1, end1, start2, end2)
            False
        """
        return not (end1 < start2 or end2 < start1)
    
    @staticmethod
    def allocation_overlaps(
        alloc1: CropAllocation,
        alloc2: CropAllocation
    ) -> bool:
        """Check if two allocations overlap in time.
        
        Args:
            alloc1: First allocation
            alloc2: Second allocation
            
        Returns:
            True if allocations overlap, False otherwise
        """
        return AllocationUtils.time_overlaps(
            alloc1.start_date,
            alloc1.completion_date,
            alloc2.start_date,
            alloc2.completion_date
        )
    
    @staticmethod
    def is_feasible_to_add(
        current_solution: List[CropAllocation],
        new_allocation: CropAllocation,
        check_area: bool = False,
        max_area: float = None
    ) -> bool:
        """Check if adding a new allocation is feasible.
        
        Checks:
        1. Time overlap: No overlap in same field
        2. Area constraint (optional): Total area doesn't exceed max
        
        Args:
            current_solution: Current allocation solution
            new_allocation: New allocation to add
            check_area: If True, also check area constraints
            max_area: Maximum area per field (required if check_area=True)
            
        Returns:
            True if feasible, False otherwise
            
        Examples:
            >>> solution = [alloc1, alloc2]
            >>> new_alloc = alloc3
            >>> AllocationUtils.is_feasible_to_add(solution, new_alloc)
            True  # if no overlap
        """
        # Check time overlap in same field
        for existing in current_solution:
            if existing.field.field_id == new_allocation.field.field_id:
                if AllocationUtils.allocation_overlaps(existing, new_allocation):
                    return False
        
        # Check area constraint
        if check_area and max_area is not None:
            field_id = new_allocation.field.field_id
            used_area = sum(
                a.area_used for a in current_solution
                if a.field.field_id == field_id
            )
            if used_area + new_allocation.area_used > max_area:
                return False
        
        return True
    
    @staticmethod
    def candidate_to_allocation(candidate: Any) -> CropAllocation:
        """Convert AllocationCandidate to CropAllocation.
        
        This is used when converting optimization candidates (DP results)
        to actual allocation entities.
        
        Args:
            candidate: AllocationCandidate object
            
        Returns:
            CropAllocation entity with new UUID
            
        Note:
            Creates a new allocation_id (UUID) for each conversion.
        """
        return CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=candidate.field,
            crop=candidate.crop,
            area_used=candidate.area_used,
            start_date=candidate.start_date,
            completion_date=candidate.completion_date,
            growth_days=candidate.growth_days,
            accumulated_gdd=candidate.accumulated_gdd,
            total_cost=candidate.cost,
            expected_revenue=candidate.revenue,
            profit=candidate.profit,
        )
    
    @staticmethod
    def calculate_field_usage(
        solution: List[CropAllocation]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate area usage and allocations per field.
        
        Useful for:
        - Checking area constraints
        - Analyzing field utilization
        - Validating solutions
        
        Args:
            solution: Current allocation solution
            
        Returns:
            Dictionary mapping field_id to usage info:
            {
                'field_id': {
                    'allocations': List[CropAllocation],
                    'used_area': float,
                    'allocation_count': int
                }
            }
            
        Examples:
            >>> usage = AllocationUtils.calculate_field_usage(solution)
            >>> usage['field1']['used_area']
            500.0
            >>> usage['field1']['allocation_count']
            3
        """
        field_usage = {}
        
        for alloc in solution:
            field_id = alloc.field.field_id
            
            if field_id not in field_usage:
                field_usage[field_id] = {
                    'allocations': [],
                    'used_area': 0.0,
                    'allocation_count': 0
                }
            
            field_usage[field_id]['allocations'].append(alloc)
            field_usage[field_id]['used_area'] += alloc.area_used
            field_usage[field_id]['allocation_count'] += 1
        
        return field_usage
    
    @staticmethod
    def remove_allocations(
        solution: List[CropAllocation],
        to_remove: List[CropAllocation]
    ) -> List[CropAllocation]:
        """Remove specific allocations from solution.
        
        Uses allocation_id for matching, so works correctly even if
        the allocation objects are different instances.
        
        Args:
            solution: Current solution
            to_remove: Allocations to remove
            
        Returns:
            New solution without removed allocations
            
        Examples:
            >>> remaining = AllocationUtils.remove_allocations(solution, [alloc1, alloc2])
            >>> len(remaining) == len(solution) - 2
            True
        """
        remove_ids = {a.allocation_id for a in to_remove}
        return [a for a in solution if a.allocation_id not in remove_ids]
    
    @staticmethod
    def calculate_total_profit(solution: List[CropAllocation]) -> float:
        """Calculate total profit of solution.
        
        Args:
            solution: Allocation solution
            
        Returns:
            Total profit (sum of all allocation profits)
            
        Examples:
            >>> profit = AllocationUtils.calculate_total_profit(solution)
            >>> profit
            15000000.0
        """
        return sum(a.profit for a in solution if a.profit is not None)
    
    @staticmethod
    def calculate_total_cost(solution: List[CropAllocation]) -> float:
        """Calculate total cost of solution.
        
        Args:
            solution: Allocation solution
            
        Returns:
            Total cost (sum of all allocation costs)
        """
        return sum(a.total_cost for a in solution if a.total_cost is not None)
    
    @staticmethod
    def calculate_total_revenue(solution: List[CropAllocation]) -> float:
        """Calculate total revenue of solution.
        
        Args:
            solution: Allocation solution
            
        Returns:
            Total revenue (sum of all allocation revenues)
        """
        return sum(a.expected_revenue for a in solution if a.expected_revenue is not None)
    
    @staticmethod
    def get_allocations_by_field(
        solution: List[CropAllocation],
        field_id: str
    ) -> List[CropAllocation]:
        """Get all allocations for a specific field.
        
        Args:
            solution: Allocation solution
            field_id: Field ID to filter by
            
        Returns:
            List of allocations for the specified field
        """
        return [a for a in solution if a.field.field_id == field_id]
    
    @staticmethod
    def get_allocations_by_crop(
        solution: List[CropAllocation],
        crop_id: str
    ) -> List[CropAllocation]:
        """Get all allocations for a specific crop.
        
        Args:
            solution: Allocation solution
            crop_id: Crop ID to filter by
            
        Returns:
            List of allocations for the specified crop
        """
        return [a for a in solution if a.crop.crop_id == crop_id]
    
    @staticmethod
    def sort_by_profit_rate(
        allocations: List[CropAllocation],
        descending: bool = True
    ) -> List[CropAllocation]:
        """Sort allocations by profit rate.
        
        Args:
            allocations: List of allocations
            descending: If True, sort in descending order (highest first)
            
        Returns:
            Sorted list of allocations
        """
        return sorted(
            allocations,
            key=lambda a: a.profit_rate,
            reverse=descending
        )
    
    @staticmethod
    def sort_by_profit(
        allocations: List[CropAllocation],
        descending: bool = True
    ) -> List[CropAllocation]:
        """Sort allocations by absolute profit.
        
        Args:
            allocations: List of allocations
            descending: If True, sort in descending order (highest first)
            
        Returns:
            Sorted list of allocations
        """
        return sorted(
            allocations,
            key=lambda a: a.profit if a.profit is not None else float('-inf'),
            reverse=descending
        )
    
    @staticmethod
    def sort_by_start_date(
        allocations: List[CropAllocation],
        ascending: bool = True
    ) -> List[CropAllocation]:
        """Sort allocations by start date.
        
        Args:
            allocations: List of allocations
            ascending: If True, sort in ascending order (earliest first)
            
        Returns:
            Sorted list of allocations
        """
        return sorted(
            allocations,
            key=lambda a: a.start_date,
            reverse=not ascending
        )

