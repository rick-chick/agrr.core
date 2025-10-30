"""Performance test using real debug data from ../agrr/tmp/debug."""

import pytest
import time
from pathlib import Path
from datetime import datetime

from agrr_core.usecase.dto.allocation_adjust_request_dto import AllocationAdjustRequestDTO
from agrr_core.usecase.interactors.allocation_adjust_interactor import AllocationAdjustInteractor
from agrr_core.adapter.gateways.allocation_result_file_gateway import AllocationResultFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.move_instruction_file_gateway import MoveInstructionFileGateway
from agrr_core.adapter.gateways.interaction_rule_file_gateway import InteractionRuleFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.framework.services.io.file_service import FileService

class TimedCropProfileFileGateway(CropProfileFileGateway):
    """Instrumented gateway to measure performance."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_all_count = 0
        self.get_all_time = 0.0
    
    async def get_all(self):
        self.get_all_count += 1
        start = time.time()
        result = super().get_all()
        self.get_all_time += time.time() - start
        return result

class TimedWeatherFileGateway(WeatherFileGateway):
    """Instrumented gateway to measure weather loading performance."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_count = 0
        self.get_time = 0.0
    
    async def get(self):
        self.get_count += 1
        start = time.time()
        result = super().get()
        self.get_time += time.time() - start
        return result

def test_real_data_performance():
    """Test with real debug data to identify actual bottlenecks."""
    
    # Use the latest debug data
    debug_dir = Path("/home/akishige/projects/agrr/tmp/debug")
    timestamp = "1761380624"  # Latest
    
    file_service = FileService()
    
    # Files
    current_allocation_file = str(debug_dir / f"adjust_current_allocation_{timestamp}.json")
    fields_file = str(debug_dir / f"adjust_fields_{timestamp}.json")
    crops_file = str(debug_dir / f"adjust_crops_{timestamp}.json")
    weather_file = str(debug_dir / f"adjust_weather_{timestamp}.json")
    moves_file = str(debug_dir / f"adjust_moves_{timestamp}.json")
    rules_file = str(debug_dir / f"adjust_rules_{timestamp}.json")
    
    # Create instrumented gateways
    allocation_gateway = AllocationResultFileGateway(file_service, current_allocation_file)
    field_gateway = FieldFileGateway(file_service, fields_file)
    crop_gateway = TimedCropProfileFileGateway(file_service, crops_file)
    weather_gateway = TimedWeatherFileGateway(file_service, weather_file)
    # Use in-memory gateway for internal use (supports save/delete)
    crop_profile_gateway_internal = CropProfileInMemoryGateway()
    interaction_rule_gateway = InteractionRuleFileGateway(file_service, rules_file)
    
    # Load moves
    move_gateway = MoveInstructionFileGateway(file_service, moves_file)
    moves = move_gateway.get_all()
    
    print(f"\n=== Real Data Performance Test ===")
    print(f"Number of moves: {len(moves)}")
    
    # Create interactor
    interactor = AllocationAdjustInteractor(
        allocation_result_gateway=allocation_gateway,
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        interaction_rule_gateway=interaction_rule_gateway,
    )
    
    # Create request
    request = AllocationAdjustRequestDTO(
        current_optimization_id="test_real_data",
        move_instructions=moves,
        planning_period_start=datetime(2026, 1, 1),
        planning_period_end=datetime(2026, 12, 31),
    )
    
    # Measure execution time with detailed breakdown
    print("\nStarting performance measurement...")
    
    overall_start = time.time()
    response = interactor.execute(request)
    overall_end = time.time()
    
    total_time = overall_end - overall_start
    
    print(f"\n=== Performance Results ===")
    print(f"Total execution time: {total_time:.3f} seconds")
    print(f"Time per move: {total_time / len(moves):.3f} seconds")
    
    print(f"\n=== Gateway Performance Breakdown ===")
    print(f"Crop Gateway (for completion date calc):")
    print(f"  Calls: {crop_gateway.get_all_count}")
    print(f"  Total time: {crop_gateway.get_all_time:.3f}s")
    print(f"  Percentage: {(crop_gateway.get_all_time / total_time * 100):.1f}%")
    
    print(f"\nInternal Crop Gateway (for GDD calc):")
    print(f"  Type: In-memory (no file I/O overhead)")
    
    print(f"\nWeather Gateway:")
    print(f"  Calls: {weather_gateway.get_count}")
    print(f"  Total time: {weather_gateway.get_time:.3f}s")
    print(f"  Percentage: {(weather_gateway.get_time / total_time * 100):.1f}%")
    
    total_gateway_time = crop_gateway.get_all_time + weather_gateway.get_time
    print(f"\nTotal Gateway Time: {total_gateway_time:.3f}s ({(total_gateway_time / total_time * 100):.1f}%)")
    print(f"Core Logic Time: {(total_time - total_gateway_time):.3f}s ({((total_time - total_gateway_time) / total_time * 100):.1f}%)")
    
    print(f"\n=== Execution Results ===")
    print(f"Success: {response.success}")
    print(f"Applied moves: {len(response.applied_moves)}")
    print(f"Rejected moves: {len(response.rejected_moves)}")
    
    if response.rejected_moves:
        print(f"\nRejection reasons:")
        for i, rejection in enumerate(response.rejected_moves[:3], 1):
            print(f"  {i}. {rejection.get('reason', 'Unknown')}")
    
    # Identify bottlenecks
    print(f"\n=== Bottleneck Analysis ===")
    
    if crop_gateway.get_all_count > len(moves):
        print(f"⚠️  Crop profiles loaded {crop_gateway.get_all_count} times for {len(moves)} moves")
        print(f"   Optimization: Cache crop profiles (potential savings: ~{crop_gateway.get_all_time:.3f}s)")
    
    if weather_gateway.get_time / total_time > 0.3:
        print(f"⚠️  Weather loading is {(weather_gateway.get_time / total_time * 100):.1f}% of total time")
        print(f"   Weather file size: 143KB - consider caching or lazy loading")
    
    if (total_time - total_gateway_time) / total_time > 0.5:
        print(f"⚠️  Core logic takes {((total_time - total_gateway_time) / total_time * 100):.1f}% of time")
        print(f"   This suggests the GDD calculation or optimization logic is the bottleneck")
    
    # Performance assertion
    if total_time > 10.0:
        print(f"\n❌ PERFORMANCE ISSUE: {total_time:.3f}s exceeds 10s threshold")
    elif total_time > 5.0:
        print(f"\n⚠️  SLOW: {total_time:.3f}s - optimization recommended")
    else:
        print(f"\n✅ Performance acceptable: {total_time:.3f}s")

