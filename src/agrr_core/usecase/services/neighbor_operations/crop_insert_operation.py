"""Crop insert operation for local search."""

import uuid
from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)

class CropInsertOperation(NeighborOperation):
    """C3. Crop Insert: Insert new crop allocation from unused candidates.
    
    Strategy:
    - Find unused candidates
    - Check area and time constraints
    - Insert if feasible
    """
    
    @property
    def operation_name(self) -> str:
        return "crop_insert"
    
    @property
    def default_weight(self) -> float:
        return 0.2
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by inserting new allocations."""
        neighbors = []
        candidates = context.get("candidates", [])
        config = context.get("config")
        
        # Get used candidate IDs
        used_ids = {
            (a.field.field_id, a.crop.crop_id, a.start_date.isoformat())
            for a in solution
        }
        
        # Calculate field usage
        field_usage = {}
        for alloc in solution:
            field_id = alloc.field.field_id
            if field_id not in field_usage:
                field_usage[field_id] = {'allocations': [], 'used_area': 0.0}
            field_usage[field_id]['allocations'].append(alloc)
            field_usage[field_id]['used_area'] += alloc.area_used
        
        # Try inserting unused candidates
        for candidate in candidates:
            candidate_id = (
                candidate.field.field_id,
                candidate.crop.crop_id,
                candidate.start_date.isoformat()
            )
            
            if candidate_id in used_ids:
                continue
            
            # Check area constraint
            field_id = candidate.field.field_id
            used_area = field_usage.get(field_id, {'used_area': 0.0})['used_area']
            if candidate.area_used > (candidate.field.area - used_area):
                continue
            
            # Check time overlap
            field_allocs = field_usage.get(field_id, {'allocations': []})['allocations']
            has_overlap = False
            for existing in field_allocs:
                if self._time_overlaps_candidate(candidate, existing):
                    has_overlap = True
                    break
            
            if has_overlap:
                continue
            
            # Create neighbor with inserted allocation
            new_alloc = self._candidate_to_allocation(candidate)
            neighbor = solution + [new_alloc]
            neighbors.append(neighbor)
            
            # Limit number of inserts to avoid explosion
            max_insert_neighbors = config.max_insert_neighbors if config else 100
            if len(neighbors) > max_insert_neighbors:
                break
        
        return neighbors
    
    def _time_overlaps_candidate(self, candidate: Any, allocation: CropAllocation) -> bool:
        """Check if candidate overlaps with allocation in time (including fallow period).
        
        CRITICAL: This method now considers fallow periods to ensure proper soil recovery time.
        
        Args:
            candidate: Allocation candidate to check
            allocation: Existing allocation to check against
            
        Returns:
            True if there is overlap considering fallow period, False otherwise
        """
        from datetime import timedelta
        
        # Calculate end dates including fallow period
        candidate_end_with_fallow = candidate.completion_date + timedelta(
            days=candidate.field.fallow_period_days
        )
        allocation_end_with_fallow = allocation.completion_date + timedelta(
            days=allocation.field.fallow_period_days
        )
        
        # Check overlap with fallow periods included
        return not (candidate_end_with_fallow <= allocation.start_date or 
                    allocation_end_with_fallow <= candidate.start_date)
    
    def _candidate_to_allocation(self, candidate: Any) -> CropAllocation:
        """Convert candidate to allocation."""
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

