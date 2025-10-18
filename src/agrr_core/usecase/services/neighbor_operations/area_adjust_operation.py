"""Area adjust operation for local search."""

import uuid
from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)


class AreaAdjustOperation(NeighborOperation):
    """A1. Area Adjust: Increase or decrease area by ±10%, ±20%.
    
    Strategy:
    - Adjust area by predefined multipliers
    - Check area constraints
    - Recalculate revenue and profit
    """
    
    @property
    def operation_name(self) -> str:
        return "area_adjust"
    
    @property
    def default_weight(self) -> float:
        return 0.1
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by adjusting areas."""
        neighbors = []
        config = context.get("config")
        
        multipliers = config.area_adjustment_multipliers if config else [0.8, 0.9, 1.1, 1.2]
        
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
                new_area = alloc.area_used * multiplier
                
                # Check capacity
                if new_area > available_area:
                    continue
                
                # Skip if area becomes too small
                if new_area < 0.1 * alloc.area_used:
                    continue
                
                # Note: revenue/profit will be recalculated by OptimizationMetrics later
                # with full context (soil recovery, interaction, etc.)
                
                # Create adjusted allocation
                # Revenue/profit set to None - will be recalculated with full context
                adjusted_alloc = CropAllocation(
                    allocation_id=str(uuid.uuid4()),
                    field=alloc.field,
                    crop=alloc.crop,
                    area_used=new_area,
                    start_date=alloc.start_date,
                    completion_date=alloc.completion_date,
                    growth_days=alloc.growth_days,
                    accumulated_gdd=alloc.accumulated_gdd,
                    total_cost=alloc.total_cost,
                    expected_revenue=None,  # Recalculated later
                    profit=None,  # Recalculated later
                )
                
                neighbor = solution.copy()
                neighbor[i] = adjusted_alloc
                neighbors.append(neighbor)
        
        return neighbors

