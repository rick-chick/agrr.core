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
    - Swap their fields while keeping areas
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
        """Generate neighbors by swapping allocations between fields.
        
        Uses candidate pool periods for both sides after swap. Generates a neighbor
        only when both sides have valid candidate periods in their target fields.
        Also checks fallow period overlaps.
        """
        neighbors = []
        candidates = context.get("candidates", [])
        config = context.get("config")
        # Tolerance for start date proximity (None means unlimited if not configured)
        tolerance_days = getattr(config, "candidate_date_tolerance_days", None) if config else None
        
        # If no candidate pool is provided, perform simple swap keeping original periods
        if not candidates:
            for i in range(len(solution)):
                for j in range(i + 1, len(solution)):
                    alloc_a = solution[i]
                    alloc_b = solution[j]
                    if alloc_a.field.field_id == alloc_b.field.field_id:
                        continue
                    swapped = self._swap_allocations_with_area_adjustment(alloc_a, alloc_b, solution)
                    if swapped is None:
                        continue
                    new_alloc_a, new_alloc_b = swapped
                    # Check fallow overlap constraints in their new fields
                    has_overlap = False
                    for alloc in solution:
                        if alloc.allocation_id != alloc_b.allocation_id and alloc.field.field_id == new_alloc_a.field.field_id:
                            if new_alloc_a.overlaps_with_fallow(alloc):
                                has_overlap = True
                                break
                    if has_overlap:
                        continue
                    for alloc in solution:
                        if alloc.allocation_id != alloc_a.allocation_id and alloc.field.field_id == new_alloc_b.field.field_id:
                            if new_alloc_b.overlaps_with_fallow(alloc):
                                has_overlap = True
                                break
                    if has_overlap:
                        continue
                    neighbor = solution.copy()
                    neighbor[i] = new_alloc_a
                    neighbor[j] = new_alloc_b
                    neighbors.append(neighbor)
            return neighbors
        
        for i in range(len(solution)):
            for j in range(i + 1, len(solution)):
                alloc_a = solution[i]
                alloc_b = solution[j]
                # Only consider different fields
                if alloc_a.field.field_id == alloc_b.field.field_id:
                    continue
                
                # Capacity checks excluding the swapping pair
                area_a = alloc_a.area_used
                area_b = alloc_b.area_used
                used_area_in_field_a = sum(
                    alloc.area_used
                    for alloc in solution
                    if alloc.field.field_id == alloc_a.field.field_id and alloc.allocation_id != alloc_a.allocation_id
                )
                used_area_in_field_b = sum(
                    alloc.area_used
                    for alloc in solution
                    if alloc.field.field_id == alloc_b.field.field_id and alloc.allocation_id != alloc_b.allocation_id
                )
                available_in_field_a = alloc_a.field.area - used_area_in_field_a
                available_in_field_b = alloc_b.field.area - used_area_in_field_b
                if area_b > available_in_field_a or area_a > available_in_field_b:
                    continue
                
                # Lookup candidate periods from pool for both sides
                # Try a limited combination search of closest candidates to avoid overlaps
                cand_list_a = self._find_candidates_sorted(
                    candidates=candidates,
                    target_field_id=alloc_b.field.field_id,
                    crop_id=alloc_a.crop.crop_id,
                    target_start=alloc_a.start_date,
                )
                cand_list_b = self._find_candidates_sorted(
                    candidates=candidates,
                    target_field_id=alloc_a.field.field_id,
                    crop_id=alloc_b.crop.crop_id,
                    target_start=alloc_b.start_date,
                )
                if tolerance_days is not None:
                    cand_list_a = [c for c in cand_list_a if abs((c.start_date - alloc_a.start_date).days) <= tolerance_days]
                    cand_list_b = [c for c in cand_list_b if abs((c.start_date - alloc_b.start_date).days) <= tolerance_days]
                if not cand_list_a or not cand_list_b:
                    continue

                found = False
                for limit in (5, 10, 20, 50):
                    for ca in cand_list_a[:limit]:
                        if found:
                            break
                        for cb in cand_list_b[:limit]:
                            cost_a_in_field_b = ca.growth_days * alloc_b.field.daily_fixed_cost
                            cost_b_in_field_a = cb.growth_days * alloc_a.field.daily_fixed_cost
                            new_alloc_a = CropAllocation(
                                allocation_id=str(uuid.uuid4()),
                                field=alloc_b.field,
                                crop=alloc_a.crop,
                                area_used=area_a,
                                start_date=ca.start_date,
                                completion_date=ca.completion_date,
                                growth_days=ca.growth_days,
                                accumulated_gdd=ca.accumulated_gdd,
                                total_cost=cost_a_in_field_b,
                                expected_revenue=None,
                                profit=None,
                            )
                            new_alloc_b = CropAllocation(
                                allocation_id=str(uuid.uuid4()),
                                field=alloc_a.field,
                                crop=alloc_b.crop,
                                area_used=area_b,
                                start_date=cb.start_date,
                                completion_date=cb.completion_date,
                                growth_days=cb.growth_days,
                                accumulated_gdd=cb.accumulated_gdd,
                                total_cost=cost_b_in_field_a,
                                expected_revenue=None,
                                profit=None,
                            )

                            has_overlap_a = False
                            for alloc in solution:
                                if alloc.allocation_id != alloc_b.allocation_id and alloc.field.field_id == new_alloc_a.field.field_id:
                                    if new_alloc_a.overlaps_with_fallow(alloc):
                                        has_overlap_a = True
                                        break
                            if has_overlap_a:
                                continue
                            has_overlap_b = False
                            for alloc in solution:
                                if alloc.allocation_id != alloc_a.allocation_id and alloc.field.field_id == new_alloc_b.field.field_id:
                                    if new_alloc_b.overlaps_with_fallow(alloc):
                                        has_overlap_b = True
                                        break
                            if has_overlap_b:
                                continue

                            neighbor = solution.copy()
                            neighbor[i] = new_alloc_a
                            neighbor[j] = new_alloc_b
                            neighbors.append(neighbor)
                            found = True
                            break
                    if found:
                        break
        
        return neighbors
    
    def _swap_allocations_with_area_adjustment(
        self,
        alloc_a: CropAllocation,
        alloc_b: CropAllocation,
        solution: List[CropAllocation],
    ) -> Optional[Tuple[CropAllocation, CropAllocation]]:
        """Swap two allocations between fields keeping their areas.
        
        When swapping crops between fields, keep their area usage.
        
        Args:
            alloc_a: First allocation
            alloc_b: Second allocation
            solution: Complete solution (to check capacity with other allocations)
            
        Returns:
            Tuple of (new_alloc_a, new_alloc_b) if swap is valid, None otherwise
        """
        # Deprecated by candidate-pool-based swap in generate_neighbors()
        # Get areas from allocations
        area_a = alloc_a.area_used
        area_b = alloc_b.area_used
        
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
        
        if area_b > available_in_field_a:
            return None
        
        if area_a > available_in_field_b:
            return None
        
        # Note: cost/revenue/profit will be recalculated by OptimizationMetrics later
        # These values are just placeholders and will be overwritten
        cost_a_in_field_b = alloc_a.growth_days * alloc_b.field.daily_fixed_cost
        cost_b_in_field_a = alloc_b.growth_days * alloc_a.field.daily_fixed_cost
        
        # Create swapped allocations
        # Revenue/profit set to None - will be recalculated with full context
        new_alloc_a = CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=alloc_b.field,
            crop=alloc_a.crop,
            area_used=area_a,
            start_date=alloc_a.start_date,
            completion_date=alloc_a.completion_date,
            growth_days=alloc_a.growth_days,
            accumulated_gdd=alloc_a.accumulated_gdd,
            total_cost=cost_a_in_field_b,
            expected_revenue=None,  # Recalculated later
            profit=None,  # Recalculated later
        )
        
        new_alloc_b = CropAllocation(
            allocation_id=str(uuid.uuid4()),
            field=alloc_a.field,
            crop=alloc_b.crop,
            area_used=area_b,
            start_date=alloc_b.start_date,
            completion_date=alloc_b.completion_date,
            growth_days=alloc_b.growth_days,
            accumulated_gdd=alloc_b.accumulated_gdd,
            total_cost=cost_b_in_field_a,
            expected_revenue=None,  # Recalculated later
            profit=None,  # Recalculated later
        )
        
        return (new_alloc_a, new_alloc_b)

    def _find_candidates_sorted(
        self,
        candidates: List[Any],
        target_field_id: str,
        crop_id: str,
        target_start,
    ) -> List[Any]:
        """Return candidates sorted by proximity of start_date to target_start."""
        filtered = [
            c for c in candidates
            if c.field.field_id == target_field_id and c.crop.crop_id == crop_id and c.completion_date is not None
        ]
        return sorted(filtered, key=lambda c: abs((c.start_date - target_start).days))

