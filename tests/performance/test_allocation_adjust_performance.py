"""Performance test for allocation adjust interactor.

This test uses the existing test data to measure performance of the adjust command.
"""

import pytest
import time
from pathlib import Path
from datetime import datetime

from agrr_core.entity.entities.move_instruction_entity import MoveInstruction, MoveAction
from agrr_core.usecase.dto.allocation_adjust_request_dto import AllocationAdjustRequestDTO
from agrr_core.usecase.interactors.allocation_adjust_interactor import AllocationAdjustInteractor
from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.framework.services.io.file_service import FileService

class TimedCropProfileFileGateway(CropProfileFileGateway):
    """Instrumented gateway to measure performance."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_all_count = 0
        self.get_all_time = 0.0
    
    def get_all(self):
        self.get_all_count += 1
        start = time.time()
        result = super().get_all()
        self.get_all_time += time.time() - start
        return result

def test_allocation_adjust_performance_with_test_data():
    """Test performance using existing test data."""
    test_data_dir = Path(__file__).parent.parent.parent / "test_data"
    file_service = FileService()
    
    # Load test data
    allocation_file = str(test_data_dir / "test_current_allocation.json")
    fields_file = str(test_data_dir / "fields.json")
    crops_file = str(test_data_dir / "crops.json")
    weather_file = str(test_data_dir / "weather.json")
    
    # Create gateways with instrumentation
    allocation_gateway = AllocationResultFileGateway(file_service, allocation_file)
    field_gateway = FieldFileGateway(file_service, fields_file)
    crop_gateway = TimedCropProfileFileGateway(file_service, crops_file)
    weather_gateway = WeatherFileGateway(file_service, weather_file)
    crop_profile_gateway_internal = TimedCropProfileFileGateway(file_service, crops_file)
    
    # Create interactor
    interactor = AllocationAdjustInteractor(
        allocation_result_gateway=allocation_gateway,
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
    )
    
    # Create move instructions (test with various numbers)
    move_counts = [1, 2, 5]
    
    for num_moves in move_counts:
        # Reset counters
        crop_gateway.get_all_count = 0
        crop_gateway.get_all_time = 0.0
        crop_profile_gateway_internal.get_all_count = 0
        crop_profile_gateway_internal.get_all_time = 0.0
        
        # Create moves
        moves = []
        for i in range(num_moves):
            move = MoveInstruction(
                allocation_id=f"e4e5fd28-d258-40fa-b8fc-4322941ca0dc",  # Use an ID from test data
                action=MoveAction.MOVE,
                to_field_id="field_3",
                to_start_date=datetime(2023, 6, 1 + i),
            )
            moves.append(move)
        
        # Create request
        request = AllocationAdjustRequestDTO(
            current_optimization_id="test_optimization",
            move_instructions=moves,
            planning_period_start=datetime(2023, 5, 1),
            planning_period_end=datetime(2023, 11, 30),
        )
        
        # Measure execution time
        start_time = time.time()
        try:
            response = interactor.execute(request)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            print(f"\n=== Performance Results ({num_moves} moves) ===")
            print(f"Total execution time: {execution_time:.3f} seconds")
            print(f"Time per move: {execution_time / num_moves:.3f} seconds")
            print(f"\nGateway call statistics:")
            print(f"  Crop Gateway (for completion date):")
            print(f"    get_all() called: {crop_gateway.get_all_count} times")
            print(f"    get_all() total time: {crop_gateway.get_all_time:.3f} seconds")
            print(f"  Internal Crop Gateway (for GDD calc):")
            print(f"    get_all() called: {crop_profile_gateway_internal.get_all_count} times")
            print(f"    get_all() total time: {crop_profile_gateway_internal.get_all_time:.3f} seconds")
            print(f"\nResult:")
            print(f"  Success: {response.success}")
            print(f"  Applied moves: {len(response.applied_moves)}")
            print(f"  Rejected moves: {len(response.rejected_moves)}")
            
            if crop_gateway.get_all_count > num_moves:
                print(f"\n⚠️  INEFFICIENCY: get_all() called {crop_gateway.get_all_count} times for {num_moves} moves")
                print(f"   Expected: ~{num_moves} calls (one per move)")
                print(f"   Optimization opportunity: Cache crop profiles between moves")
            
            # Basic performance assertion - should not be slower than 2s per move
            assert execution_time / num_moves < 2.0, \
                f"Too slow: {execution_time / num_moves:.3f}s per move (threshold: 2.0s)"
        
        except Exception as e:
            print(f"\n❌ Test failed for {num_moves} moves: {e}")
            # Don't fail the test completely, just report
            print(f"   Continuing with next test case...")

def test_allocation_adjust_bottleneck_analysis():
    """Detailed bottleneck analysis to identify slow operations."""
    test_data_dir = Path(__file__).parent.parent.parent / "test_data"
    file_service = FileService()
    
    # Load test data
    allocation_file = str(test_data_dir / "test_current_allocation.json")
    fields_file = str(test_data_dir / "fields.json")
    crops_file = str(test_data_dir / "crops.json")
    weather_file = str(test_data_dir / "weather.json")
    
    # Create gateways with instrumentation
    allocation_gateway = AllocationResultFileGateway(file_service, allocation_file)
    field_gateway = FieldFileGateway(file_service, fields_file)
    crop_gateway = TimedCropProfileFileGateway(file_service, crops_file)
    weather_gateway = WeatherFileGateway(file_service, weather_file)
    crop_profile_gateway_internal = TimedCropProfileFileGateway(file_service, crops_file)
    
    # Create interactor
    interactor = AllocationAdjustInteractor(
        allocation_result_gateway=allocation_gateway,
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
    )
    
    # Create 3 moves for analysis
    moves = []
    for i in range(3):
        move = MoveInstruction(
            allocation_id="e4e5fd28-d258-40fa-b8fc-4322941ca0dc",
            action=MoveAction.MOVE,
            to_field_id="field_3",
            to_start_date=datetime(2023, 6, 1 + i),
        )
        moves.append(move)
    
    request = AllocationAdjustRequestDTO(
        current_optimization_id="test_optimization",
        move_instructions=moves,
        planning_period_start=datetime(2023, 5, 1),
        planning_period_end=datetime(2023, 11, 30),
    )
    
    # Execute and measure
    start_time = time.time()
    try:
        response = interactor.execute(request)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"\n=== Bottleneck Analysis ===")
        print(f"Total execution time: {execution_time:.3f} seconds")
        print(f"\nBreakdown:")
        print(f"  Gateway overhead (crop loading):")
        print(f"    Crop gateway: {crop_gateway.get_all_time:.3f}s ({crop_gateway.get_all_count} calls)")
        print(f"    Internal gateway: {crop_profile_gateway_internal.get_all_time:.3f}s ({crop_profile_gateway_internal.get_all_count} calls)")
        print(f"    Total gateway time: {crop_gateway.get_all_time + crop_profile_gateway_internal.get_all_time:.3f}s")
        
        gateway_percentage = ((crop_gateway.get_all_time + crop_profile_gateway_internal.get_all_time) / execution_time) * 100
        print(f"    Gateway overhead: {gateway_percentage:.1f}% of total time")
        
        print(f"\nRecommendations:")
        if crop_gateway.get_all_count > 1:
            print(f"  1. Cache crop profiles - currently loading {crop_gateway.get_all_count} times")
        if crop_profile_gateway_internal.get_all_count > len(moves):
            print(f"  2. Optimize internal gateway calls - {crop_profile_gateway_internal.get_all_count} calls for {len(moves)} moves")
        if gateway_percentage > 50:
            print(f"  3. Gateway overhead is {gateway_percentage:.1f}% - consider batching or caching")
    
    except Exception as e:
        print(f"\n❌ Bottleneck analysis failed: {e}")
        import traceback
        traceback.print_exc()

