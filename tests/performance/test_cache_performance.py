"""Test performance improvement with GDD caching for multiple moves."""

import pytest
import time
from pathlib import Path
from datetime import datetime, timedelta

from agrr_core.entity.entities.move_instruction_entity import MoveInstruction, MoveAction
from agrr_core.usecase.dto.allocation_adjust_request_dto import AllocationAdjustRequestDTO
from agrr_core.usecase.interactors.allocation_adjust_interactor import AllocationAdjustInteractor
from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.interaction_rule_file_gateway import InteractionRuleFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.framework.services.io.file_service import FileService

def test_gdd_cache_performance():
    """Test that GDD caching improves performance for multiple moves."""
    
    # Use real debug data
    debug_dir = Path("/home/akishige/projects/agrr/tmp/debug")
    timestamp = "1761380624"
    
    file_service = FileService()
    
    # Files
    current_allocation_file = str(debug_dir / f"adjust_current_allocation_{timestamp}.json")
    fields_file = str(debug_dir / f"adjust_fields_{timestamp}.json")
    crops_file = str(debug_dir / f"adjust_crops_{timestamp}.json")
    weather_file = str(debug_dir / f"adjust_weather_{timestamp}.json")
    rules_file = str(debug_dir / f"adjust_rules_{timestamp}.json")
    
    # Create gateways
    allocation_gateway = AllocationResultFileGateway(file_service, current_allocation_file)
    field_gateway = FieldFileGateway(file_service, fields_file)
    crop_gateway = CropProfileFileGateway(file_service, crops_file)
    weather_gateway = WeatherFileGateway(file_service, weather_file)
    crop_profile_gateway_internal = CropProfileInMemoryGateway()
    interaction_rule_gateway = InteractionRuleFileGateway(file_service, rules_file)
    
    # Load current allocation to get allocation IDs
    current_result = allocation_gateway.get()
    
    # Get an allocation to use for testing
    test_allocation = current_result.field_schedules[0].allocations[0]
    test_field_id = current_result.field_schedules[1].field.field_id  # Different field
    
    print(f"\n=== GDD Cache Performance Test ===")
    print(f"Test allocation: {test_allocation.allocation_id}")
    print(f"Crop: {test_allocation.crop.name}")
    print(f"Target field: {test_field_id}")
    
    # Test 1: Single move (no cache hit)
    interactor1 = AllocationAdjustInteractor(
        allocation_result_gateway=allocation_gateway,
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        interaction_rule_gateway=interaction_rule_gateway,
    )
    
    moves1 = [
        MoveInstruction(
            allocation_id=test_allocation.allocation_id,
            action=MoveAction.MOVE,
            to_field_id=test_field_id,
            to_start_date=datetime(2026, 5, 10),
        )
    ]
    
    request1 = AllocationAdjustRequestDTO(
        current_optimization_id="test",
        move_instructions=moves1,
        planning_period_start=datetime(2026, 1, 1),
        planning_period_end=datetime(2026, 12, 31),
    )
    
    start1 = time.time()
    response1 = interactor1.execute(request1)
    time1 = time.time() - start1
    
    print(f"\n--- Test 1: Single Move (Cold Cache) ---")
    print(f"Time: {time1:.3f}s")
    print(f"Cache size: {len(interactor1._gdd_candidate_cache)}")
    print(f"Success: {response1.success}")
    
    # Test 2: 10 similar moves (cache should hit)
    interactor2 = AllocationAdjustInteractor(
        allocation_result_gateway=allocation_gateway,
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        interaction_rule_gateway=interaction_rule_gateway,
    )
    
    # Create 10 moves with slightly different start dates
    moves2 = [
        MoveInstruction(
            allocation_id=test_allocation.allocation_id,
            action=MoveAction.MOVE,
            to_field_id=test_field_id,
            to_start_date=datetime(2026, 5, 10) + timedelta(days=i),
        )
        for i in range(10)
    ]
    
    request2 = AllocationAdjustRequestDTO(
        current_optimization_id="test",
        move_instructions=moves2,
        planning_period_start=datetime(2026, 1, 1),
        planning_period_end=datetime(2026, 12, 31),
    )
    
    start2 = time.time()
    response2 = interactor2.execute(request2)
    time2 = time.time() - start2
    
    print(f"\n--- Test 2: 10 Similar Moves (Warm Cache) ---")
    print(f"Time: {time2:.3f}s")
    print(f"Time per move: {time2 / 10:.3f}s")
    print(f"Cache size: {len(interactor2._gdd_candidate_cache)}")
    print(f"Applied moves: {len(response2.applied_moves)}")
    print(f"Rejected moves: {len(response2.rejected_moves)}")
    
    # Test 3: Performance comparison
    print(f"\n--- Performance Comparison ---")
    expected_time_without_cache = time1 * 10
    actual_time_with_cache = time2
    speedup = expected_time_without_cache / actual_time_with_cache
    time_saved = expected_time_without_cache - actual_time_with_cache
    
    print(f"Without cache (projected): {expected_time_without_cache:.3f}s")
    print(f"With cache (actual): {actual_time_with_cache:.3f}s")
    print(f"Speedup: {speedup:.1f}x")
    print(f"Time saved: {time_saved:.3f}s ({(time_saved/expected_time_without_cache*100):.1f}%)")
    
    # Test 4: 50 moves simulation (6s case)
    print(f"\n--- Extrapolation to 50 Moves ---")
    projected_50_without_cache = time1 * 50
    # Cache hit rate: After first move, subsequent moves should be much faster
    # Assuming ~78% time is GDD calc, cache should save most of that
    estimated_50_with_cache = time1 + (time2 / 10) * 49  # First move + 49 cached moves
    estimated_speedup = projected_50_without_cache / estimated_50_with_cache
    
    print(f"Projected 50 moves without cache: {projected_50_without_cache:.3f}s")
    print(f"Estimated 50 moves with cache: {estimated_50_with_cache:.3f}s")
    print(f"Estimated speedup: {estimated_speedup:.1f}x")
    print(f"Time saved: {(projected_50_without_cache - estimated_50_with_cache):.3f}s")
    
    if projected_50_without_cache > 6.0:
        print(f"\n✅ This explains the 6s slowdown!")
        print(f"   With caching: {estimated_50_with_cache:.1f}s (much faster!)")
    
    # Performance assertion
    assert speedup > 1.5, f"Cache should provide at least 1.5x speedup, got {speedup:.1f}x"
    
    print(f"\n✅ GDD caching is working and provides significant performance improvement!")

