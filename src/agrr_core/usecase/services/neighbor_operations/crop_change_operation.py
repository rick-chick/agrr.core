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
    - Adjust quantity to maintain area equivalence
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
        """Generate neighbors by changing crops."""
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
                
                # Calculate area-equivalent quantity
                original_area = alloc.area_used
                new_quantity = original_area / new_crop.area_per_unit if new_crop.area_per_unit > 0 else 0
                
                if new_quantity <= 0:
                    continue
                
                # Create new allocation with changed crop
                new_alloc = self._candidate_to_allocation_with_quantity(
                    best_candidate,
                    quantity=new_quantity
                )
                
                neighbor = solution.copy()
                neighbor[i] = new_alloc
                neighbors.append(neighbor)
        
        return neighbors
    
    def _candidate_to_allocation_with_quantity(
        self,
        candidate: Any,
        quantity: float,
    ) -> CropAllocation:
        """Convert candidate to allocation with specified quantity."""
        area_used = quantity * candidate.crop.area_per_unit
        cost = candidate.cost
        
        revenue = None
        if candidate.crop.revenue_per_area is not None:
            revenue = quantity * candidate.crop.revenue_per_area * candidate.crop.area_per_unit
        
        profit = (revenue - cost) if revenue is not None else None
        
        return CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=candidate.field,
            crop=candidate.crop,
            quantity=quantity,
            start_date=candidate.start_date,
            completion_date=candidate.completion_date,
            growth_days=candidate.growth_days,
            accumulated_gdd=candidate.accumulated_gdd,
            total_cost=cost,
            expected_revenue=revenue,
            profit=profit,
            area_used=area_used,
        )

