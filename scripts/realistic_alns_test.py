"""Realistic test comparing DP + LS vs DP + ALNS with larger dataset."""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import time
import logging

# Enable logging to see ALNS debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

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


async def run_comparison():
    """Run realistic comparison with larger problem."""
    
    test_data = Path(__file__).parent.parent / 'test_data'
    
    # Use larger dataset
    fields_file = test_data / 'allocation_fields_large.json'  # 10 fields
    crops_file = test_data / 'allocation_crops_6types.json'   # 6 crops
    weather_file = test_data / 'allocation_weather_1760533282.json'
    rules_file = test_data / 'allocation_rules_1760533282.json'
    
    print("="*80)
    print("REALISTIC DP + LS vs DP + ALNS COMPARISON")
    print("="*80)
    print(f"\nDataset:")
    print(f"  Fields: {fields_file.name} (10 fields)")
    print(f"  Crops: {crops_file.name} (6 crops)")
    print(f"  Weather: {weather_file.name}")
    print(f"  Rules: {rules_file.name}")
    
    # Load data once
    file_service = FileService()
    field_gateway_loader = FieldFileGateway(file_service, str(fields_file))
    crop_gateway_loader = CropProfileFileGateway(file_service, str(crops_file))
    rule_gateway = InteractionRuleFileGateway(file_service, str(rules_file))
    
    fields = await field_gateway_loader.get_all()
    crops = await crop_gateway_loader.get_all()
    interaction_rules = await rule_gateway.get_rules()
    
    print(f"\n✓ Loaded: {len(fields)} fields, {len(crops)} crops, {len(interaction_rules)} rules")
    
    # Create request (use all fields)
    request = MultiFieldCropAllocationRequestDTO(
        field_ids=[f.field_id for f in fields],
        planning_period_start=datetime(2025, 1, 1),
        planning_period_end=datetime(2025, 12, 31),
        optimization_objective="maximize_profit",
    )
    
    # Test 1: DP + Local Search (more iterations)
    print("\n" + "="*80)
    print("Test 1: DP + Local Search (Hill Climbing)")
    print("="*80)
    
    config_ls = OptimizationConfig(
        enable_parallel_candidate_generation=True,
        enable_candidate_filtering=False,
        max_local_search_iterations=100,  # Standard setting
        enable_alns=False,
    )
    
    # Create fresh gateways for Test 1
    field_gateway_ls = FieldFileGateway(FileService(), str(fields_file))
    crop_gateway_ls = CropProfileFileGateway(FileService(), str(crops_file))
    weather_gateway_ls = WeatherFileGateway(FileService(), str(weather_file))
    
    interactor_ls = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway_ls,
        crop_gateway=crop_gateway_ls,
        weather_gateway=weather_gateway_ls,
        crop_profile_gateway_internal=CropProfileInMemoryGateway(),
        config=config_ls,
        interaction_rules=interaction_rules,
    )
    
    start = time.time()
    
    # Get DP initial solution (without local search)
    response_ls_dp_only = await interactor_ls.execute(
        request=request,
        algorithm="dp",
        enable_local_search=False,  # DP only
        config=config_ls,
    )
    dp_only_result = response_ls_dp_only.optimization_result
    print(f"DP-only (before LS):")
    print(f"  Profit: ¥{dp_only_result.total_profit:,.0f}")
    print(f"  Allocations: {sum(len(fs.allocations) for fs in dp_only_result.field_schedules)}")
    
    # Now run with local search
    response_ls = await interactor_ls.execute(
        request=request,
        algorithm="dp",
        enable_local_search=True,
        config=config_ls,
    )
    elapsed_ls = time.time() - start
    
    result_ls = response_ls.optimization_result
    print(f"✓ Success (after LS)!")
    print(f"  Time: {elapsed_ls:.2f}s")
    print(f"  Profit: ¥{result_ls.total_profit:,.0f}")
    print(f"  Revenue: ¥{result_ls.total_revenue:,.0f}")
    print(f"  Cost: ¥{result_ls.total_cost:,.0f}")
    print(f"  Allocations: {sum(len(fs.allocations) for fs in result_ls.field_schedules)}")
    print(f"  Algorithm: {result_ls.algorithm_used}")
    
    # Test 2: DP + ALNS (more iterations)
    print("\n" + "="*80)
    print("Test 2: DP + ALNS (Adaptive Large Neighborhood Search)")
    print("="*80)
    
    config_alns = OptimizationConfig(
        enable_parallel_candidate_generation=True,
        enable_candidate_filtering=False,
        enable_alns=True,
        alns_iterations=200,  # Standard ALNS setting
        alns_removal_rate=0.3,
    )
    
    # Create fresh gateways for Test 2
    field_gateway_alns = FieldFileGateway(FileService(), str(fields_file))
    crop_gateway_alns = CropProfileFileGateway(FileService(), str(crops_file))
    weather_gateway_alns = WeatherFileGateway(FileService(), str(weather_file))
    
    interactor_alns = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway_alns,
        crop_gateway=crop_gateway_alns,
        weather_gateway=weather_gateway_alns,
        crop_profile_gateway_internal=CropProfileInMemoryGateway(),
        config=config_alns,
        interaction_rules=interaction_rules,
    )
    
    start = time.time()
    
    # Get DP initial solution (without ALNS)
    response_alns_dp_only = await interactor_alns.execute(
        request=request,
        algorithm="dp",
        enable_local_search=False,  # DP only
        config=config_alns,
    )
    dp_only_result2 = response_alns_dp_only.optimization_result
    print(f"DP-only (before ALNS):")
    print(f"  Profit: ¥{dp_only_result2.total_profit:,.0f}")
    print(f"  Allocations: {sum(len(fs.allocations) for fs in dp_only_result2.field_schedules)}")
    
    # Now run with ALNS
    response_alns = await interactor_alns.execute(
        request=request,
        algorithm="dp",
        enable_local_search=True,
        config=config_alns,
    )
    elapsed_alns = time.time() - start
    
    result_alns = response_alns.optimization_result
    print(f"✓ Success (after ALNS)!")
    print(f"  Time: {elapsed_alns:.2f}s")
    print(f"  Profit: ¥{result_alns.total_profit:,.0f}")
    print(f"  Revenue: ¥{result_alns.total_revenue:,.0f}")
    print(f"  Cost: ¥{result_alns.total_cost:,.0f}")
    print(f"  Allocations: {sum(len(fs.allocations) for fs in result_alns.field_schedules)}")
    print(f"  Algorithm: {result_alns.algorithm_used}")
    
    # Comparison
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    
    profit_diff = result_alns.total_profit - result_ls.total_profit
    profit_pct = (profit_diff / result_ls.total_profit * 100) if result_ls.total_profit != 0 else 0
    time_diff = elapsed_alns - elapsed_ls
    time_ratio = (elapsed_alns / elapsed_ls) if elapsed_ls > 0 else 0
    
    print(f"\nProfit:")
    print(f"  DP + LS:   ¥{result_ls.total_profit:,.0f}")
    print(f"  DP + ALNS: ¥{result_alns.total_profit:,.0f}")
    print(f"  Difference: ¥{profit_diff:,.0f} ({profit_pct:+.2f}%)")
    
    print(f"\nTime:")
    print(f"  DP + LS:   {elapsed_ls:.2f}s")
    print(f"  DP + ALNS: {elapsed_alns:.2f}s")
    print(f"  Difference: {time_diff:+.2f}s ({time_ratio:.2f}x)")
    
    print(f"\nAllocations:")
    ls_allocs = sum(len(fs.allocations) for fs in result_ls.field_schedules)
    alns_allocs = sum(len(fs.allocations) for fs in result_alns.field_schedules)
    print(f"  DP + LS:   {ls_allocs}")
    print(f"  DP + ALNS: {alns_allocs}")
    
    # Verdict
    print("\n" + "="*80)
    if profit_pct > 1.0:
        print(f"🎉 SUCCESS: ALNS improved profit by {profit_pct:.2f}%!")
        print(f"   Trade-off: +{time_diff:.1f}s for ¥{profit_diff:,.0f} extra profit")
        print(f"   ROI: ¥{profit_diff/time_diff:,.0f} per second")
    elif profit_pct > 0:
        print(f"✓ ALNS slightly improved profit by {profit_pct:.2f}%")
    elif profit_pct == 0:
        print(f"✓ Both algorithms found same solution")
    else:
        print(f"⚠ ALNS found worse solution by {profit_pct:.2f}%")
        print(f"   Possible reasons:")
        print(f"   - Problem too small for ALNS to be effective")
        print(f"   - Randomness in ALNS (try increasing iterations)")
        print(f"   - DP already found near-optimal solution")


if __name__ == '__main__':
    asyncio.run(run_comparison())

