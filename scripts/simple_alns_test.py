"""Simple test to verify ALNS works with actual sample data.

This script tests ALNS with a minimal but realistic scenario to catch
any errors in neighbor operations.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.interaction_rule_file_gateway import InteractionRuleFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.framework.services.io.file_service import FileService


async def test_alns():
    """Test ALNS with sample data."""
    
    test_data = Path(__file__).parent.parent / 'test_data'
    
    # Use sample data files
    fields_file = test_data / 'allocation_fields_1760533282.json'
    crops_file = test_data / 'allocation_crops_6types.json'
    weather_file = test_data / 'allocation_weather_1760533282.json'
    rules_file = test_data / 'allocation_rules_1760533282.json'
    
    print("Loading data...")
    print(f"  Fields: {fields_file.name}")
    print(f"  Crops: {crops_file.name}")
    print(f"  Weather: {weather_file.name}")
    print(f"  Rules: {rules_file.name}")
    
    # Create gateways with FileService
    file_service = FileService()
    
    field_gateway = FieldFileGateway(file_service, str(fields_file))
    crop_gateway = CropProfileFileGateway(file_service, str(crops_file))
    weather_gateway = WeatherFileGateway(file_service, str(weather_file))
    rule_gateway = InteractionRuleFileGateway(file_service, str(rules_file))
    
    # Load interaction rules
    interaction_rules = await rule_gateway.get_rules()
    
    # Get field IDs
    fields = await field_gateway.get_all()
    field_ids = [f.field_id for f in fields]
    
    crops = await crop_gateway.get_all()
    
    print(f"\n✓ Loaded: {len(fields)} fields, {len(crops)} crops, {len(interaction_rules)} rules")
    
    # Create request
    request = MultiFieldCropAllocationRequestDTO(
        field_ids=field_ids[:5],  # Use first 5 fields for quick test
        planning_period_start=datetime(2025, 1, 1),
        planning_period_end=datetime(2025, 12, 31),
        optimization_objective="maximize_profit",
    )
    
    print(f"\nTesting with {len(request.field_ids)} fields...")
    
    # Test 1: DP + Local Search
    print("\n" + "="*80)
    print("Test 1: DP + Local Search (Hill Climbing)")
    print("="*80)
    
    config_ls = OptimizationConfig(
        enable_parallel_candidate_generation=True,
        enable_candidate_filtering=False,  # Don't filter for testing
        max_local_search_iterations=20,  # Small for quick test
        enable_alns=False,
    )
    
    interactor_ls = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=CropProfileInMemoryGateway(),
        config=config_ls,
        interaction_rules=interaction_rules,
    )
    
    try:
        import time
        start = time.time()
        
        response_ls = await interactor_ls.execute(
            request=request,
            algorithm="dp",  # Use DP for allocation
            enable_local_search=True,
            config=config_ls,
        )
        
        elapsed = time.time() - start
        result = response_ls.optimization_result
        
        print(f"✓ Success!")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Profit: ¥{result.total_profit:,.0f}")
        print(f"  Revenue: ¥{result.total_revenue:,.0f}")
        print(f"  Cost: ¥{result.total_cost:,.0f}")
        print(f"  Allocations: {sum(len(fs.allocations) for fs in result.field_schedules)}")
        print(f"  Algorithm: {result.algorithm_used}")
        
        ls_result = {
            'profit': result.total_profit,
            'time': elapsed,
            'allocations': sum(len(fs.allocations) for fs in result.field_schedules),
        }
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        ls_result = None
    
    # Test 2: DP + ALNS
    print("\n" + "="*80)
    print("Test 2: DP + ALNS (Adaptive Large Neighborhood Search)")
    print("="*80)
    
    config_alns = OptimizationConfig(
        enable_parallel_candidate_generation=True,
        enable_candidate_filtering=False,  # Don't filter for testing
        enable_alns=True,
        alns_iterations=20,  # Small for quick test
        alns_removal_rate=0.3,
    )
    
    interactor_alns = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=CropProfileInMemoryGateway(),
        config=config_alns,
        interaction_rules=interaction_rules,
    )
    
    try:
        start = time.time()
        
        response_alns = await interactor_alns.execute(
            request=request,
            algorithm="dp",  # Use DP for allocation
            enable_local_search=True,
            config=config_alns,
        )
        
        elapsed = time.time() - start
        result = response_alns.optimization_result
        
        print(f"✓ Success!")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Profit: ¥{result.total_profit:,.0f}")
        print(f"  Revenue: ¥{result.total_revenue:,.0f}")
        print(f"  Cost: ¥{result.total_cost:,.0f}")
        print(f"  Allocations: {sum(len(fs.allocations) for fs in result.field_schedules)}")
        print(f"  Algorithm: {result.algorithm_used}")
        
        alns_result = {
            'profit': result.total_profit,
            'time': elapsed,
            'allocations': sum(len(fs.allocations) for fs in result.field_schedules),
        }
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        alns_result = None
    
    # Comparison
    if ls_result and alns_result:
        print("\n" + "="*80)
        print("COMPARISON")
        print("="*80)
        
        profit_diff = alns_result['profit'] - ls_result['profit']
        profit_pct = (profit_diff / ls_result['profit'] * 100) if ls_result['profit'] != 0 else 0
        time_diff = alns_result['time'] - ls_result['time']
        
        print(f"Profit Improvement: ¥{profit_diff:,.0f} ({profit_pct:+.2f}%)")
        print(f"Time Difference: {time_diff:+.2f}s")
        print(f"Allocations: {alns_result['allocations']} vs {ls_result['allocations']}")
        
        if profit_pct > 0:
            print(f"\n🎉 ALNS improved profit by {profit_pct:.2f}%!")
        elif profit_pct == 0:
            print(f"\n✓ Both algorithms found same solution")
        else:
            print(f"\n⚠ ALNS found worse solution (unexpected)")


if __name__ == '__main__':
    asyncio.run(test_alns())

