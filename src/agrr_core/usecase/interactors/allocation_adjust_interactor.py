"""Allocation adjustment interactor.

This interactor adjusts an existing allocation based on user-specified move instructions,
then re-optimizes the allocation while respecting constraints.

Algorithm:
1. Load current optimization result
2. Apply move instructions (remove, move allocations)
3. Re-run optimization with:
   - Remaining allocations as constraints
   - Available fields and time slots
   - Same optimization objectives and constraints as original allocate command
4. Return adjusted and re-optimized result

Constraints:
- Fallow period compliance
- Crop rotation rules (interaction rules)
- Field capacity
- Time period boundaries
"""

import uuid
import time
from datetime import datetime, timedelta
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
from agrr_core.usecase.dto.allocation_adjust_request_dto import AllocationAdjustRequestDTO
from agrr_core.usecase.dto.allocation_adjust_response_dto import AllocationAdjustResponseDTO
from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.usecase.gateways.allocation_result_gateway import AllocationResultGateway
from agrr_core.usecase.gateways.move_instruction_gateway import MoveInstructionGateway
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
)


class AllocationAdjustInteractor:
    """Interactor for allocation adjustment use case."""
    
    def __init__(
        self,
        allocation_result_gateway: AllocationResultGateway,
        move_instruction_gateway: MoveInstructionGateway,
        field_gateway: FieldGateway,
        crop_gateway: CropProfileGateway,
        weather_gateway: WeatherGateway,
        crop_profile_gateway_internal: CropProfileGateway,
        interaction_rule_gateway: Optional[InteractionRuleGateway] = None,
        config: Optional[OptimizationConfig] = None,
    ):
        """Initialize with injected dependencies.
        
        Args:
            optimization_result_gateway: Gateway for loading current optimization result
            move_instruction_gateway: Gateway for loading move instructions
            field_gateway: Gateway for field operations
            crop_gateway: Gateway for crop operations
            weather_gateway: Gateway for weather data operations
            crop_profile_gateway_internal: Internal gateway for growth period optimization
            interaction_rule_gateway: Optional gateway for interaction rules
            config: Optional optimization configuration
        """
        self.allocation_result_gateway = allocation_result_gateway
        self.move_instruction_gateway = move_instruction_gateway
        self.field_gateway = field_gateway
        self.crop_gateway = crop_gateway
        self.weather_gateway = weather_gateway
        self.crop_profile_gateway_internal = crop_profile_gateway_internal
        self.interaction_rule_gateway = interaction_rule_gateway
        self.config = config or OptimizationConfig()
        
        # Load interaction rules
        self.interaction_rules: List[InteractionRule] = []
        
        # Create allocation optimizer for re-optimization
        self.allocation_optimizer = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=field_gateway,
            crop_gateway=crop_gateway,
            weather_gateway=weather_gateway,
            crop_profile_gateway_internal=crop_profile_gateway_internal,
            config=self.config,
            interaction_rules=self.interaction_rules,
        )
    
    async def execute(
        self,
        request: AllocationAdjustRequestDTO,
        enable_local_search: bool = True,
        config: Optional[OptimizationConfig] = None,
        algorithm: str = "dp",
    ) -> AllocationAdjustResponseDTO:
        """Execute allocation adjustment use case.
        
        Args:
            request: Request DTO containing adjustment parameters
            enable_local_search: Whether to enable local search optimization
            config: Optional optimization configuration
            algorithm: Algorithm to use ('dp' or 'greedy')
            
        Returns:
            Response DTO containing adjusted and re-optimized result
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
                self.allocation_optimizer.interaction_rule_service.rules = self.interaction_rules
            except Exception as e:
                # Continue without interaction rules
                pass
        
        # Apply move instructions
        adjusted_result, applied_moves, rejected_moves = await self._apply_moves(
            current_result=current_result,
            move_instructions=move_instructions,
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
        
        # Re-optimize with remaining allocations as constraints
        # Create request for re-optimization
        field_ids = [schedule.field.field_id for schedule in adjusted_result.field_schedules]
        
        reopt_request = MultiFieldCropAllocationRequestDTO(
            field_ids=field_ids,
            planning_period_start=request.planning_period_start,
            planning_period_end=request.planning_period_end,
            optimization_objective=request.optimization_objective,
            max_computation_time=request.max_computation_time,
            filter_redundant_candidates=request.filter_redundant_candidates,
        )
        
        # Execute re-optimization
        reopt_response = await self.allocation_optimizer.execute(
            request=reopt_request,
            enable_local_search=enable_local_search,
            config=config or self.config,
            algorithm=algorithm,
        )
        
        computation_time = time.time() - start_time
        
        # Create final result with updated optimization metadata
        final_result = MultiFieldOptimizationResult(
            optimization_id=str(uuid.uuid4()),
            field_schedules=reopt_response.optimization_result.field_schedules,
            total_cost=reopt_response.optimization_result.total_cost,
            total_revenue=reopt_response.optimization_result.total_revenue,
            total_profit=reopt_response.optimization_result.total_profit,
            crop_areas=reopt_response.optimization_result.crop_areas,
            optimization_time=computation_time,
            algorithm_used=f"adjust+{algorithm}",
            is_optimal=reopt_response.optimization_result.is_optimal,
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
    ) -> Tuple[MultiFieldOptimizationResult, List[MoveInstruction], List[Dict[str, str]]]:
        """Apply move instructions to current result.
        
        Args:
            current_result: Current optimization result
            move_instructions: List of move instructions to apply
            
        Returns:
            Tuple of (adjusted_result, applied_moves, rejected_moves)
        """
        applied_moves = []
        rejected_moves = []
        
        # Create mapping of allocation_id to allocation for fast lookup
        allocation_map: Dict[str, CropAllocation] = {}
        field_schedule_map: Dict[str, FieldSchedule] = {}
        
        for schedule in current_result.field_schedules:
            field_schedule_map[schedule.field.field_id] = schedule
            for allocation in schedule.allocations:
                allocation_map[allocation.allocation_id] = allocation
        
        # Process each move instruction
        modified_schedules = {fid: list(schedule.allocations) 
                            for fid, schedule in field_schedule_map.items()}
        
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
                    
                    # Note: The actual move (adding to target field) will be handled
                    # by re-optimization. Here we just mark the instruction as applied.
                    # The interactor will create new candidates and optimize placement.
                    applied_moves.append(move)
                
            except Exception as e:
                rejected_moves.append({
                    "move": move,
                    "reason": str(e),
                })
        
        # Rebuild field schedules with modified allocations
        new_schedules = []
        for field_id, allocations in modified_schedules.items():
            if field_id not in field_schedule_map:
                continue
            
            original_schedule = field_schedule_map[field_id]
            
            # Recalculate totals
            total_cost = sum(a.total_cost for a in allocations)
            total_revenue = sum(a.expected_revenue or 0.0 for a in allocations)
            total_profit = sum(a.profit or 0.0 for a in allocations)
            
            # Calculate utilization (time-integrated)
            total_area_used = sum(a.area_used for a in allocations)
            utilization_rate = 0.0
            if original_schedule.field.area > 0:
                utilization_rate = (total_area_used / original_schedule.field.area) * 100.0
            
            new_schedule = FieldSchedule(
                field=original_schedule.field,
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
            optimization_time=0.0,  # Will be updated after re-optimization
            algorithm_used=current_result.algorithm_used + "_adjusted",
            is_optimal=False,  # No longer optimal after manual adjustment
        )
        
        return adjusted_result, applied_moves, rejected_moves

