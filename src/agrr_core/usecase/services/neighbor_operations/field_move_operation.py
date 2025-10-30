"""Field move operation for local search."""

from typing import List, Dict, Any

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.services.neighbor_operations.base_neighbor_operation import (
    NeighborOperation,
)

class FieldMoveOperation(NeighborOperation):
    """F1. Field Move: Move allocation to a different field.
    
    Strategy:
    - Select an allocation
    - Try moving it to each other field
    - Find best period candidate for target field
    - Check area and time constraints
    """
    
    @property
    def operation_name(self) -> str:
        return "field_move"
    
    @property
    def default_weight(self) -> float:
        return 0.15
    
    def generate_neighbors(
        self,
        solution: List[CropAllocation],
        context: Dict[str, Any],
    ) -> List[List[CropAllocation]]:
        """Generate neighbors by moving allocations to different fields."""
        neighbors = []
        candidates = context.get("candidates", [])
        fields = context.get("fields", [])
        
        for i, alloc in enumerate(solution):
            for target_field in fields:
                # Skip if same field
                if target_field.field_id == alloc.field.field_id:
                    continue
                
                # Calculate available area in target field
                used_area_in_target = sum(
                    a.area_used 
                    for a in solution 
                    if a.field.field_id == target_field.field_id
                )
                available_area = target_field.area - used_area_in_target
                
                # Check if allocation fits
                if alloc.area_used > available_area:
                    continue
                
                # Check time overlap (including fallow period)
                has_overlap = False
                for existing in solution:
                    if existing.field.field_id == target_field.field_id:
                        if alloc.overlaps_with_fallow(existing):
                            has_overlap = True
                            break
                
                if has_overlap:
                    continue
                
                # Find best period candidate for target field with same crop
                best_candidate = None
                best_profit_rate = -float('inf')
                
                for candidate in candidates:
                    if (candidate.field.field_id == target_field.field_id and
                        candidate.crop.crop_id == alloc.crop.crop_id):
                        if candidate.profit_rate > best_profit_rate:
                            best_candidate = candidate
                            best_profit_rate = candidate.profit_rate
                
                if best_candidate is None:
                    continue
                
                # Create moved allocation with target field's optimal period
                moved_alloc = self._candidate_to_allocation_with_area(
                    best_candidate,
                    area_used=alloc.area_used
                )
                
                neighbor = solution.copy()
                neighbor[i] = moved_alloc
                neighbors.append(neighbor)
        
        return neighbors
    
    def _candidate_to_allocation_with_area(
        self,
        candidate: Any,
        area_used: float,
    ) -> CropAllocation:
        """Convert candidate to allocation with specified area.
        
        Note: revenue/profit are set to None and will be recalculated
        by OptimizationMetrics with full context (soil recovery, interaction, etc.)
        """
        import uuid
        
        cost = candidate.cost
        
        # Revenue/profit set to None - will be recalculated with full context
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
            expected_revenue=None,  # Recalculated later
            profit=None,  # Recalculated later
        )

