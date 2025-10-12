"""Field swap operation for local search."""

import uuid
from typing import List, Dict, Any, Optional, Tuple

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)


class FieldSwapOperation(NeighborOperation):
    """F2. Field Swap: Swap two allocations between different fields.
    
    Strategy:
    - Select two allocations from different fields
    - Swap their fields while adjusting quantities to maintain area equivalence
    - Check capacity constraints
    """
    
    @property
    def operation_name(self) -> str:
        return "field_swap"
    
    @property
    def default_weight(self) -> float:
        return 0.3  # High weight - effective operation
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by swapping allocations between fields."""
        neighbors = []
        
        for i in range(len(solution)):
            for j in range(i + 1, len(solution)):
                if solution[i].field.field_id != solution[j].field.field_id:
                    swapped = self._swap_allocations_with_area_adjustment(
                        solution[i], solution[j], solution
                    )
                    if swapped is not None:
                        neighbor = solution.copy()
                        neighbor[i], neighbor[j] = swapped
                        neighbors.append(neighbor)
        
        return neighbors
    
    def _swap_allocations_with_area_adjustment(
        self,
        alloc_a: CropAllocation,
        alloc_b: CropAllocation,
        solution: List[CropAllocation],
    ) -> Optional[Tuple[CropAllocation, CropAllocation]]:
        """Swap two allocations between fields with area-equivalent quantity adjustment.
        
        When swapping crops between fields, adjust quantities to maintain equivalent
        area usage based on each crop's area_per_unit.
        
        Args:
            alloc_a: First allocation
            alloc_b: Second allocation
            solution: Complete solution (to check capacity with other allocations)
            
        Returns:
            Tuple of (new_alloc_a, new_alloc_b) if swap is valid, None otherwise
        """
        # Calculate area-equivalent quantities
        area_a = alloc_a.quantity * alloc_a.crop.area_per_unit
        area_b = alloc_b.quantity * alloc_b.crop.area_per_unit
        
        # Check if area_per_unit is valid
        if alloc_a.crop.area_per_unit <= 0 or alloc_b.crop.area_per_unit <= 0:
            return None
        
        # Calculate new quantities to maintain equivalent area usage
        new_quantity_a = area_b / alloc_a.crop.area_per_unit
        new_quantity_b = area_a / alloc_b.crop.area_per_unit
        
        new_area_a_in_field_b = new_quantity_a * alloc_a.crop.area_per_unit
        new_area_b_in_field_a = new_quantity_b * alloc_b.crop.area_per_unit
        
        # Calculate used area in each field (excluding the allocations being swapped)
        used_area_in_field_a = sum(
            alloc.area_used 
            for alloc in solution 
            if alloc.field.field_id == alloc_a.field.field_id 
            and alloc.allocation_id != alloc_a.allocation_id
        )
        
        used_area_in_field_b = sum(
            alloc.area_used 
            for alloc in solution 
            if alloc.field.field_id == alloc_b.field.field_id 
            and alloc.allocation_id != alloc_b.allocation_id
        )
        
        # Check if new allocations fit within available capacity
        available_in_field_a = alloc_a.field.area - used_area_in_field_a
        available_in_field_b = alloc_b.field.area - used_area_in_field_b
        
        if new_area_b_in_field_a > available_in_field_a:
            return None
        
        if new_area_a_in_field_b > available_in_field_b:
            return None
        
        # Calculate new costs and revenues
        cost_a_in_field_b = alloc_a.growth_days * alloc_b.field.daily_fixed_cost
        cost_b_in_field_a = alloc_b.growth_days * alloc_a.field.daily_fixed_cost
        
        revenue_a_in_field_b = None
        if alloc_a.crop.revenue_per_area is not None:
            revenue_a_in_field_b = new_quantity_a * alloc_a.crop.revenue_per_area * alloc_a.crop.area_per_unit
        
        revenue_b_in_field_a = None
        if alloc_b.crop.revenue_per_area is not None:
            revenue_b_in_field_a = new_quantity_b * alloc_b.crop.revenue_per_area * alloc_b.crop.area_per_unit
        
        # Calculate profits
        profit_a_in_field_b = (revenue_a_in_field_b - cost_a_in_field_b) if revenue_a_in_field_b is not None else None
        profit_b_in_field_a = (revenue_b_in_field_a - cost_b_in_field_a) if revenue_b_in_field_a is not None else None
        
        # Create swapped allocations
        new_alloc_a = CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=alloc_b.field,
            crop=alloc_a.crop,
            quantity=new_quantity_a,
            start_date=alloc_a.start_date,
            completion_date=alloc_a.completion_date,
            growth_days=alloc_a.growth_days,
            accumulated_gdd=alloc_a.accumulated_gdd,
            total_cost=cost_a_in_field_b,
            expected_revenue=revenue_a_in_field_b,
            profit=profit_a_in_field_b,
            area_used=new_area_a_in_field_b,
        )
        
        new_alloc_b = CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=alloc_a.field,
            crop=alloc_b.crop,
            quantity=new_quantity_b,
            start_date=alloc_b.start_date,
            completion_date=alloc_b.completion_date,
            growth_days=alloc_b.growth_days,
            accumulated_gdd=alloc_b.accumulated_gdd,
            total_cost=cost_b_in_field_a,
            expected_revenue=revenue_b_in_field_a,
            profit=profit_b_in_field_a,
            area_used=new_area_b_in_field_a,
        )
        
        return (new_alloc_a, new_alloc_b)

