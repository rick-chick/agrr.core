"""Crop change operation for local search."""

import uuid
from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)


class CropChangeOperation(NeighborOperation):
    """C1. Crop Change: Change crop while keeping field and approximate period.
    
    Strategy:
    - Replace crop in an allocation
    - Find similar candidate (same field, different crop, similar timing)
    - Keep same area
    """
    
    @property
    def operation_name(self) -> str:
        return "crop_change"
    
    @property
    def default_weight(self) -> float:
        return 0.1
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by changing crops.
        
        CRITICAL: This method now checks fallow period constraints to ensure
        the new crop's period doesn't violate fallow period with other allocations.
        """
        neighbors = []
        candidates = context.get("candidates", [])
        crops = context.get("crops", [])
        
        for i, alloc in enumerate(solution):
            for new_crop in crops:
                # Skip if same crop
                if new_crop.crop_id == alloc.crop.crop_id:
                    continue
                
                # Find similar candidates (same field, new crop, similar timing)
                similar_candidates = [
                    c for c in candidates
                    if c.field.field_id == alloc.field.field_id and
                       c.crop.crop_id == new_crop.crop_id
                ]
                
                if not similar_candidates:
                    continue
                
                # Find candidate with closest start date
                best_candidate = min(
                    similar_candidates,
                    key=lambda c: abs((c.start_date - alloc.start_date).days)
                )
                
                # Keep same area
                original_area = alloc.area_used
                
                # Create new allocation with changed crop
                new_alloc = self._candidate_to_allocation_with_area(
                    best_candidate,
                    area_used=original_area
                )
                
                # Check if new allocation violates fallow period with other allocations
                # in the same field
                has_overlap = False
                for j, other_alloc in enumerate(solution):
                    if i == j:  # Skip the allocation being replaced
                        continue
                    
                    if other_alloc.field.field_id == new_alloc.field.field_id:
                        if new_alloc.overlaps_with_fallow(other_alloc):
                            has_overlap = True
                            break
                
                if has_overlap:
                    continue  # Skip this candidate - violates fallow period
                
                neighbor = solution.copy()
                neighbor[i] = new_alloc
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

