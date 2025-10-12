"""Period replace operation for local search."""

import uuid
from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)


class PeriodReplaceOperation(NeighborOperation):
    """P4. Period Replace: Replace period with candidate from DP results.
    
    Strategy:
    - Keep field and crop
    - Replace with alternative period from DP candidates
    - Keep same area
    """
    
    @property
    def operation_name(self) -> str:
        return "period_replace"
    
    @property
    def default_weight(self) -> float:
        return 0.1
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by replacing periods."""
        neighbors = []
        candidates = context.get("candidates", [])
        config = context.get("config")
        
        max_alternatives = config.max_period_replace_alternatives if config else 3
        
        for i, alloc in enumerate(solution):
            # Find candidates for the same field and crop
            similar_candidates = [
                c for c in candidates
                if c.field.field_id == alloc.field.field_id and
                   c.crop.crop_id == alloc.crop.crop_id and
                   c.start_date != alloc.start_date
            ]
            
            # Try up to N alternatives
            for candidate in similar_candidates[:max_alternatives]:
                neighbor = solution.copy()
                neighbor[i] = self._candidate_to_allocation_with_area(
                    candidate,
                    area_used=alloc.area_used
                )
                neighbors.append(neighbor)
        
        return neighbors
    
    def _candidate_to_allocation_with_area(
        self,
        candidate: Any,
        area_used: float,
    ) -> CropAllocation:
        """Convert candidate to allocation with specified area."""
        cost = candidate.cost
        
        revenue = None
        if candidate.crop.revenue_per_area is not None:
            revenue = area_used * candidate.crop.revenue_per_area
        
        profit = (revenue - cost) if revenue is not None else None
        
        return CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=candidate.field,
            crop=candidate.crop,
            area_used=area_used,
            start_date=candidate.start_date,
            completion_date=candidate.completion_date,
            growth_days=candidate.growth_days,
            accumulated_gdd=candidate.accumulated_gdd,
            total_cost=cost,
            expected_revenue=revenue,
            profit=profit,
        )

