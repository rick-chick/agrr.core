"""Allocation adjustment interactor.

This interactor adjusts an existing allocation based on user-specified move instructions.

Algorithm:
1. Load current optimization result
2. Apply move instructions (remove, move allocations)
3. For moved allocations:
   - Calculate completion date from new start date using GDD calculation
   - Recalculate cost, revenue, and profit
4. Return adjusted result

Constraints:
- Fallow period compliance
- Crop rotation rules (interaction rules)
- Field capacity
- Time period boundaries
"""

import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_schedule_entity import FieldSchedule
from agrr_core.entity.entities.multi_field_optimization_result_entity import (
    MultiFieldOptimizationResult,
)
from agrr_core.entity.entities.move_instruction_entity import MoveInstruction, MoveAction
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.value_objects.optimization_objective import OptimizationMetrics
from agrr_core.usecase.dto.allocation_adjust_request_dto import AllocationAdjustRequestDTO
from agrr_core.usecase.dto.allocation_adjust_response_dto import AllocationAdjustResponseDTO
from agrr_core.usecase.dto.growth_period_optimize_request_dto import OptimalGrowthPeriodRequestDTO
from agrr_core.usecase.gateways.allocation_result_gateway import AllocationResultGateway
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.usecase.interactors.growth_period_optimize_interactor import (
    GrowthPeriodOptimizeInteractor,
)


class AllocationAdjustInteractor:
    """Interactor for allocation adjustment use case."""
    
    def __init__(
        self,
        allocation_result_gateway: AllocationResultGateway,
        field_gateway: FieldGateway,
        crop_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        crop_profile_gateway_internal: CropProfileGateway,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None,
    ):
        """Initialize with injected dependencies.
        
        Args:
            allocation_result_gateway: Gateway for loading current allocation result
            field_gateway: Gateway for field operations
            crop_gateway: Gateway for crop operations
            weather_gateway: Gateway for weather data operations
            crop_profile_gateway_internal: Internal gateway for growth period optimization
            interaction_rule_gateway: Optional gateway for interaction rules
        """
        self.allocation_result_gateway = allocation_result_gateway
        self.field_gateway = field_gateway
        self.crop_gateway = crop_gateway
        self.weather_gateway = weather_gateway
        self.crop_profile_gateway_internal = crop_profile_gateway_internal
        self.interaction_rule_gateway = interaction_rule_gateway
        
        # Interaction rules loaded on demand
        self.interaction_rules: List[InteractionRule] = []
        
        # GDD candidate cache for performance optimization
        # Key: "{crop_id}_{variety}_{field_id}_{period_end}"
        # Value: List of candidate periods from GrowthPeriodOptimizeInteractor
        # Note: We don't include start_date in key to allow reuse across different move dates
        self._gdd_candidate_cache: Dict[str, List] = {}
        
        # Create growth period optimizer for GDD calculation
        self.growth_period_optimizer = GrowthPeriodOptimizeInteractor(
            crop_profile_gateway=crop_profile_gateway_internal,
            weather_gateway=weather_gateway,
        )
    
    async def execute(
        self,
        request: AllocationAdjustRequestDTO,
    ) -> AllocationAdjustResponseDTO:
        """Execute allocation adjustment use case.
        
        Args:
            request: Request DTO containing adjustment parameters
            
        Returns:
            Response DTO containing adjusted result
        """
        start_time = time.time()
        
        # Load current allocation result
        current_result = await self.allocation_result_gateway.get()
        if not current_result:
            return AllocationAdjustResponseDTO(
                optimized_result=None,
                applied_moves=[],
                rejected_moves=[],
                success=False,
                message="Failed to load current optimization result",
            )
        
        # Load move instructions
        move_instructions = request.move_instructions
        
        # Load interaction rules if gateway is provided
        if self.interaction_rule_gateway:
            try:
                self.interaction_rules = await self.interaction_rule_gateway.get_rules()
            except Exception as e:
                # Continue without interaction rules
                pass
        
        # Apply move instructions with GDD calculation
        adjusted_result, applied_moves, rejected_moves = await self._apply_moves(
            current_result=current_result,
            move_instructions=move_instructions,
            planning_period_start=request.planning_period_start,
            planning_period_end=request.planning_period_end,
        )
        
        # If no moves were applied successfully, return error
        if not applied_moves:
            return AllocationAdjustResponseDTO(
                optimized_result=current_result,
                applied_moves=[],
                rejected_moves=rejected_moves,
                success=False,
                message="No moves were applied successfully. All moves were rejected.",
            )
        
        computation_time = time.time() - start_time
        
        # Update optimization metadata
        final_result = MultiFieldOptimizationResult(
            optimization_id=str(uuid.uuid4()),
            field_schedules=adjusted_result.field_schedules,
            total_cost=adjusted_result.total_cost,
            total_revenue=adjusted_result.total_revenue,
            total_profit=adjusted_result.total_profit,
            crop_areas=adjusted_result.crop_areas,
            optimization_time=computation_time,
            algorithm_used="adjust",
            is_optimal=False,  # Manual adjustment
        )
        
        return AllocationAdjustResponseDTO(
            optimized_result=final_result,
            applied_moves=applied_moves,
            rejected_moves=rejected_moves,
            success=True,
            message=f"Successfully adjusted allocation with {len(applied_moves)} moves applied, "
                   f"{len(rejected_moves)} moves rejected.",
        )
    
    async def _apply_moves(
        self,
        current_result: MultiFieldOptimizationResult,
        move_instructions: List[MoveInstruction],
        planning_period_start: datetime,
        planning_period_end: datetime,
    ) -> Tuple[MultiFieldOptimizationResult, List[MoveInstruction], List[Dict[str, str]]]:
        """Apply move instructions to current result.
        
        Args:
            current_result: Current optimization result
            move_instructions: List of move instructions to apply
            planning_period_start: Planning period start date
            planning_period_end: Planning period end date
            
        Returns:
            Tuple of (adjusted_result, applied_moves, rejected_moves)
        """
        applied_moves = []
        rejected_moves = []
        
        # Create mapping of allocation_id to allocation for fast lookup
        allocation_map: Dict[str, CropAllocation] = {}
        field_schedule_map: Dict[str, FieldSchedule] = {}
        field_map: Dict[str, Field] = {}
        
        for schedule in current_result.field_schedules:
            field_schedule_map[schedule.field.field_id] = schedule
            field_map[schedule.field.field_id] = schedule.field
            for allocation in schedule.allocations:
                allocation_map[allocation.allocation_id] = allocation
        
        # Process each move instruction
        modified_schedules = {fid: list(schedule.allocations) 
                            for fid, schedule in field_schedule_map.items()}
        new_allocations = []  # Track new allocations for recalculation
        
        for move in move_instructions:
            try:
                # Check if allocation exists
                if move.allocation_id not in allocation_map:
                    rejected_moves.append({
                        "move": move,
                        "reason": f"Allocation {move.allocation_id} not found",
                    })
                    continue
                
                allocation = allocation_map[move.allocation_id]
                
                if move.action == MoveAction.REMOVE:
                    # Remove allocation from its field
                    field_id = allocation.field.field_id
                    modified_schedules[field_id] = [
                        a for a in modified_schedules[field_id]
                        if a.allocation_id != move.allocation_id
                    ]
                    applied_moves.append(move)
                
                elif move.action == MoveAction.MOVE:
                    # Remove from current field
                    current_field_id = allocation.field.field_id
                    modified_schedules[current_field_id] = [
                        a for a in modified_schedules[current_field_id]
                        if a.allocation_id != move.allocation_id
                    ]
                    
                    # Get target field
                    if move.to_field_id not in field_map:
                        # Target field may not exist in current schedules, load it
                        target_field = await self.field_gateway.get(move.to_field_id)
                        if target_field is None:
                            rejected_moves.append({
                                "move": move,
                                "reason": f"Target field {move.to_field_id} not found",
                            })
                            continue
                        field_map[move.to_field_id] = target_field
                        modified_schedules[move.to_field_id] = []
                    
                    target_field = field_map[move.to_field_id]
                    
                    # Calculate completion date using GDD calculation
                    try:
                        completion_date, growth_days = await self._calculate_completion_date(
                            crop=allocation.crop,
                            field=target_field,
                            start_date=move.to_start_date,
                            planning_period_end=planning_period_end,
                        )
                    except ValueError as e:
                        rejected_moves.append({
                            "move": move,
                            "reason": f"Cannot complete growth in planning period: {str(e)}",
                        })
                        continue
                    
                    # Determine area to use
                    area_used = move.to_area if move.to_area is not None else allocation.area_used
                    
                    # Create new allocation with basic values
                    # Cost/revenue/profit will be recalculated after all moves are applied
                    cost = growth_days * target_field.daily_fixed_cost
                    
                    # IMPORTANT: Keep original allocation_id for tracking
                    new_allocation = CropAllocation(
                        allocation_id=allocation.allocation_id,
                        field=target_field,
                        crop=allocation.crop,
                        area_used=area_used,
                        start_date=move.to_start_date,
                        completion_date=completion_date,
                        growth_days=growth_days,
                        accumulated_gdd=0.0,  # TODO: Get from GDD calculation
                        total_cost=cost,
                        expected_revenue=None,  # Will be recalculated with full context
                        profit=None,  # Will be recalculated with full context
                    )
                    
                    # Check for overlap with existing allocations in target field
                    has_overlap = False
                    overlap_with_id = None
                    for existing in modified_schedules.get(move.to_field_id, []):
                        if new_allocation.overlaps_with_fallow(existing):
                            has_overlap = True
                            overlap_with_id = existing.allocation_id
                            break
                    
                    if has_overlap:
                        rejected_moves.append({
                            "move": move,
                            "reason": f"Time overlap with allocation {overlap_with_id} (considering {target_field.fallow_period_days}-day fallow period)",
                        })
                        continue
                    
                    # Add to target field
                    modified_schedules[move.to_field_id].append(new_allocation)
                    new_allocations.append(new_allocation)  # Track for recalculation
                    applied_moves.append(move)
                
            except Exception as e:
                rejected_moves.append({
                    "move": move,
                    "reason": str(e),
                })
        
        # Recalculate only new allocations with full context after all moves are applied
        if new_allocations:
            # Get all allocations for context (including existing + new)
            all_final_allocations = []
            for allocs in modified_schedules.values():
                all_final_allocations.extend(allocs)
            
            # Build field schedules dict for interaction rules
            field_schedules_dict = {fid: allocs for fid, allocs in modified_schedules.items()}
            
            # Recalculate revenue and profit only for new allocations with final context
            recalculated_new = OptimizationMetrics.recalculate_allocations_with_context(
                new_allocations,
                field_schedules_dict,
                self.interaction_rules,
                planning_period_start
            )
            
            # Create mapping of new allocation IDs to recalculated allocations
            recalc_map = {alloc.allocation_id: alloc for alloc in recalculated_new}
            
            # Update modified_schedules with recalculated values
            for field_id, allocs in modified_schedules.items():
                modified_schedules[field_id] = [
                    recalc_map.get(alloc.allocation_id, alloc) for alloc in allocs
                ]
        
        # Use updated modified_schedules
        recalc_by_field = modified_schedules
        
        # Rebuild field schedules with recalculated allocations
        new_schedules = []
        for field_id, allocations in recalc_by_field.items():
            field = field_map.get(field_id) or field_schedule_map[field_id].field
            
            # Recalculate totals
            total_cost = sum(a.total_cost for a in allocations)
            total_revenue = sum(a.expected_revenue or 0.0 for a in allocations)
            total_profit = sum(a.profit or 0.0 for a in allocations)
            
            # Calculate utilization (time-integrated)
            total_area_used = sum(a.area_used for a in allocations)
            utilization_rate = 0.0
            if field.area > 0:
                utilization_rate = (total_area_used / field.area) * 100.0
            
            new_schedule = FieldSchedule(
                field=field,
                allocations=allocations,
                total_area_used=total_area_used,
                total_cost=total_cost,
                total_revenue=total_revenue,
                total_profit=total_profit,
                utilization_rate=utilization_rate,
            )
            new_schedules.append(new_schedule)
        
        # Recalculate aggregate totals
        total_cost = sum(s.total_cost for s in new_schedules)
        total_revenue = sum(s.total_revenue for s in new_schedules)
        total_profit = sum(s.total_profit for s in new_schedules)
        
        # Recalculate crop areas
        crop_areas: Dict[str, float] = {}
        for schedule in new_schedules:
            for allocation in schedule.allocations:
                crop_id = allocation.crop.crop_id
                crop_areas[crop_id] = crop_areas.get(crop_id, 0.0) + allocation.area_used
        
        adjusted_result = MultiFieldOptimizationResult(
            optimization_id=current_result.optimization_id + "_adjusted",
            field_schedules=new_schedules,
            total_cost=total_cost,
            total_revenue=total_revenue,
            total_profit=total_profit,
            crop_areas=crop_areas,
            optimization_time=0.0,
            algorithm_used=current_result.algorithm_used + "_adjusted",
            is_optimal=False,  # No longer optimal after manual adjustment
        )
        
        return adjusted_result, applied_moves, rejected_moves
    
    async def _calculate_completion_date(
        self,
        crop: Crop,
        field: Field,
        start_date: datetime,
        planning_period_end: datetime,
    ) -> Tuple[datetime, int]:
        """Calculate completion date from start date using GDD calculation.
        
        Args:
            crop: Crop to be grown
            field: Field where crop will be grown
            start_date: Start date of cultivation
            planning_period_end: Planning period end date
            
        Returns:
            Tuple of (completion_date, growth_days)
            
        Raises:
            ValueError: If crop cannot complete growth by planning_period_end
        """
        # Get crop profile from gateway (includes stage requirements for GDD calculation)
        all_crops = await self.crop_gateway.get_all()
        crop_profile = None
        for cp in all_crops:
            if cp.crop.crop_id == crop.crop_id:
                crop_profile = cp
                break
        
        if crop_profile is None:
            raise ValueError(f"Crop profile not found for crop {crop.crop_id}")
        
        # Set crop in internal gateway for GrowthPeriodOptimizeInteractor
        await self.crop_profile_gateway_internal.save(crop_profile)
        
        try:
            # Create cache key for GDD candidates
            # Key only on crop, field, and planning period (not start_date)
            # This allows reuse for different start dates within same planning period
            cache_key = (
                f"{crop.crop_id}_{crop.variety or 'default'}_{field.field_id}_"
                f"{planning_period_end.date()}"
            )
            
            # Check cache first (significant performance improvement for multiple moves)
            if cache_key in self._gdd_candidate_cache:
                candidates = self._gdd_candidate_cache[cache_key]
            else:
                # Use GrowthPeriodOptimizeInteractor to find valid cultivation periods
                # We use a narrow evaluation window (start_date to planning_period_end)
                # and check if starting on start_date allows completion
                request = OptimalGrowthPeriodRequestDTO(
                    crop_id=crop.crop_id,
                    variety=crop.variety,
                    evaluation_period_start=start_date,
                    evaluation_period_end=planning_period_end,
                    field=field,
                    filter_redundant_candidates=True,  # Enable filtering for performance
                )
                
                response = await self.growth_period_optimizer.execute(request)
                candidates = response.candidates
                
                # Cache the candidates for future moves
                self._gdd_candidate_cache[cache_key] = candidates
            
            # Find candidate starting on or after the specified date (choose nearest)
            best_candidate = None
            for candidate in candidates:
                if candidate.start_date >= start_date:
                    if candidate.completion_date is None:
                        continue
                    if best_candidate is None or candidate.start_date < best_candidate.start_date:
                        best_candidate = candidate
            
            if best_candidate is None:
                raise ValueError(
                    f"Crop {crop.name} cannot complete growth starting on or after {start_date} "
                    f"by planning period end {planning_period_end}"
                )
            
            return best_candidate.completion_date, best_candidate.growth_days
        
        finally:
            # Clean up
            await self.crop_profile_gateway_internal.delete()

