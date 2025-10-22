#!/usr/bin/env python3
"""Real performance measurement for allocation adjust in client environment."""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, '/home/akishige/projects/agrr.core/src')

# Set profiling environment variable
os.environ["AGRR_PROFILE"] = "1"

from agrr_core.usecase.interactors.allocation_adjust_interactor import AllocationAdjustInteractor
from agrr_core.usecase.dto.allocation_adjust_request_dto import AllocationAdjustRequestDTO
from agrr_core.entity.entities.move_instruction_entity import MoveInstruction, MoveAction

# Import real gateways (not mocks)
from agrr_core.usecase.gateways.allocation_result_gateway import AllocationResultGateway
from agrr_core.usecase.gateways.field_gateway import FieldGateway
from agrr_core.usecase.gateways.crop_profile_gateway import CropProfileGateway
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.interaction_rule_gateway import InteractionRuleGateway

async def measure_real_performance():
    """Measure real performance with actual gateways."""
    print("=== Real Performance Measurement ===")
    print("Using actual gateways (not mocks)")
    print("=" * 50)
    
    # Create real gateways (these will use actual file paths and data)
    allocation_gateway = AllocationResultGateway()
    field_gateway = FieldGateway()
    crop_gateway = CropProfileGateway()
    weather_gateway = WeatherGateway()
    interaction_gateway = InteractionRuleGateway()
    
    # Create interactor with real gateways
    interactor = AllocationAdjustInteractor(
        allocation_result_gateway=allocation_gateway,
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_gateway,
        interaction_rule_gateway=interaction_gateway
    )
    
    # Create realistic move instructions
    move_instructions = [
        MoveInstruction(
            allocation_id="alloc_1",
            action=MoveAction.MOVE,
            to_field_id="field_2",
            to_start_date=datetime.now() + timedelta(days=1),
            to_area=50.0
        ),
        MoveInstruction(
            allocation_id="",
            action=MoveAction.ADD,
            crop_id="tomato",
            variety="default",
            to_field_id="field_3",
            to_start_date=datetime.now() + timedelta(days=5),
            to_area=30.0
        )
    ]
    
    # Create request
    request = AllocationAdjustRequestDTO(
        current_optimization_id="real_opt",
        move_instructions=move_instructions,
        planning_period_start=datetime.now(),
        planning_period_end=datetime.now() + timedelta(days=90)
    )
    
    print("Executing allocation adjust with real data...")
    print("-" * 30)
    
    # Measure total time
    start_time = time.time()
    result = await interactor.execute(request)
    end_time = time.time()
    
    print("-" * 30)
    print(f"Total execution time: {end_time - start_time:.3f}s")
    print(f"Success: {result.success}")
    print(f"Applied moves: {len(result.applied_moves)}")
    print(f"Rejected moves: {len(result.rejected_moves)}")
    
    if result.rejected_moves:
        print("Rejected moves:")
        for move in result.rejected_moves:
            print(f"  - {move}")

if __name__ == "__main__":
    asyncio.run(measure_real_performance())
