"""Quantity adjust operation for local search."""

import uuid
from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)


class QuantityAdjustOperation(NeighborOperation):
    """Q1. Quantity Adjust: Increase or decrease quantity by ±10%, ±20%.
    
    Strategy:
    - Adjust quantity by predefined multipliers
    - Check area constraints
    - Recalculate revenue and profit
    """
    
    @property
    def operation_name(self) -> str:
        return "quantity_adjust"
    
    @property
    def default_weight(self) -> float:
        return 0.1
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by adjusting quantities."""
        neighbors = []
        config = context.get("config")
        
        multipliers = config.quantity_adjustment_multipliers if config else [0.8, 0.9, 1.1, 1.2]
        
        for i, alloc in enumerate(solution):
            # Calculate available area in field
            used_area_in_field = sum(
                a.area_used 
                for a in solution 
                if a.field.field_id == alloc.field.field_id and
                   a.allocation_id != alloc.allocation_id
            )
            available_area = alloc.field.area - used_area_in_field
            
            for multiplier in multipliers:
                new_quantity = alloc.quantity * multiplier
                new_area = new_quantity * alloc.crop.area_per_unit
                
                # Check capacity
                if new_area > available_area:
                    continue
                
                # Skip if quantity becomes too small
                if new_quantity < 0.1 * alloc.quantity:
                    continue
                
                # Recalculate revenue and profit
                new_revenue = None
                if alloc.crop.revenue_per_area is not None:
                    new_revenue = new_quantity * alloc.crop.revenue_per_area * alloc.crop.area_per_unit
                
                new_profit = (new_revenue - alloc.total_cost) if new_revenue is not None else None
                
                # Create adjusted allocation
                adjusted_alloc = CropAllocation(
                    allocation_id=str(uuid.uuid4()),
                    field=alloc.field,
                    crop=alloc.crop,
                    quantity=new_quantity,
                    start_date=alloc.start_date,
                    completion_date=alloc.completion_date,
                    growth_days=alloc.growth_days,
                    accumulated_gdd=alloc.accumulated_gdd,
                    total_cost=alloc.total_cost,
                    expected_revenue=new_revenue,
                    profit=new_profit,
                    area_used=new_area,
                )
                
                neighbor = solution.copy()
                neighbor[i] = adjusted_alloc
                neighbors.append(neighbor)
        
        return neighbors

