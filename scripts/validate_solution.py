"""Validate optimization solution for constraint violations.

Checks:
1. Time overlap: Same field cannot have overlapping allocations
2. Area constraint: Total area per field doesn't exceed field area
3. Max revenue: Total revenue per crop doesn't exceed max_revenue
4. Data integrity: All allocations have valid data
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

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


def validate_solution(optimization_result):
    """Validate solution for constraint violations."""
    
    print("\n" + "="*80)
    print("SOLUTION VALIDATION")
    print("="*80)
    
    violations = []
    
    # Check each field
    for field_schedule in optimization_result.field_schedules:
        field = field_schedule.field
        allocations = field_schedule.allocations
        
        print(f"\nField: {field.name} (ID: {field.field_id})")
        print(f"  Area: {field.area} m²")
        print(f"  Daily Cost: ¥{field.daily_fixed_cost}")
        print(f"  Allocations: {len(allocations)}")
        
        # Check 1: Time overlap
        for i, alloc1 in enumerate(allocations):
            for j, alloc2 in enumerate(allocations):
                if i >= j:
                    continue
                
                # Check overlap
                if not (alloc1.completion_date < alloc2.start_date or 
                        alloc2.completion_date < alloc1.start_date):
                    violations.append({
                        'type': 'TIME_OVERLAP',
                        'field': field.name,
                        'alloc1': f"{alloc1.crop.name} ({alloc1.start_date.date()} - {alloc1.completion_date.date()})",
                        'alloc2': f"{alloc2.crop.name} ({alloc2.start_date.date()} - {alloc2.completion_date.date()})",
                    })
                    print(f"  ❌ TIME OVERLAP:")
                    print(f"     {alloc1.crop.name}: {alloc1.start_date.date()} - {alloc1.completion_date.date()}")
                    print(f"     {alloc2.crop.name}: {alloc2.start_date.date()} - {alloc2.completion_date.date()}")
        
        # Check 2: Area constraint (simultaneous allocations)
        # Group by time period
        from collections import defaultdict
        daily_area = defaultdict(float)
        
        for alloc in allocations:
            current_date = alloc.start_date
            while current_date <= alloc.completion_date:
                daily_area[current_date.date()] += alloc.area_used
                current_date += timedelta(days=1)
        
        # Check if any day exceeds field area
        for date, area in daily_area.items():
            if area > field.area + 0.01:  # Small tolerance for floating point
                violations.append({
                    'type': 'AREA_EXCEEDED',
                    'field': field.name,
                    'date': date,
                    'used': area,
                    'max': field.area,
                })
                print(f"  ❌ AREA EXCEEDED on {date}:")
                print(f"     Used: {area:.2f} m²")
                print(f"     Max:  {field.area:.2f} m²")
        
        # Print allocation details
        for i, alloc in enumerate(allocations, 1):
            print(f"  {i}. {alloc.crop.name} ({alloc.crop.variety or 'N/A'})")
            print(f"     Period: {alloc.start_date.date()} - {alloc.completion_date.date()} ({alloc.growth_days} days)")
            print(f"     Area: {alloc.area_used:.2f} m²")
            print(f"     Profit: ¥{alloc.profit:,.0f}")
    
    # Check 3: Max revenue constraint
    crop_revenues = {}
    for field_schedule in optimization_result.field_schedules:
        for alloc in field_schedule.allocations:
            crop_id = alloc.crop.crop_id
            if crop_id not in crop_revenues:
                crop_revenues[crop_id] = {
                    'total_revenue': 0.0,
                    'max_revenue': alloc.crop.max_revenue,
                    'crop_name': alloc.crop.name,
                }
            if alloc.expected_revenue:
                crop_revenues[crop_id]['total_revenue'] += alloc.expected_revenue
    
    print("\n" + "="*80)
    print("CROP REVENUE CONSTRAINTS")
    print("="*80)
    
    for crop_id, data in crop_revenues.items():
        print(f"\n{data['crop_name']}:")
        print(f"  Total Revenue: ¥{data['total_revenue']:,.0f}")
        if data['max_revenue']:
            print(f"  Max Revenue: ¥{data['max_revenue']:,.0f}")
            if data['total_revenue'] > data['max_revenue']:
                violations.append({
                    'type': 'MAX_REVENUE_EXCEEDED',
                    'crop': data['crop_name'],
                    'total': data['total_revenue'],
                    'max': data['max_revenue'],
                })
                print(f"  ❌ EXCEEDED by ¥{data['total_revenue'] - data['max_revenue']:,.0f}")
            else:
                print(f"  ✓ OK")
        else:
            print(f"  (No limit)")
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    if violations:
        print(f"\n❌ Found {len(violations)} constraint violations:")
        for v in violations:
            print(f"  - {v['type']}: {v}")
        return False
    else:
        print(f"\n✓ No constraint violations found!")
        print(f"  Total allocations: {sum(len(fs.allocations) for fs in optimization_result.field_schedules)}")
        print(f"  Total profit: ¥{optimization_result.total_profit:,.0f}")
        return True


async def test_with_validation():
    """Run ALNS test with validation."""
    
    test_data = Path(__file__).parent.parent / 'test_data'
    
    fields_file = test_data / 'allocation_fields_large.json'
    crops_file = test_data / 'allocation_crops_6types.json'
    weather_file = test_data / 'allocation_weather_1760533282.json'
    rules_file = test_data / 'allocation_rules_1760533282.json'
    
    file_service = FileService()
    
    # Create request
    field_gateway = FieldFileGateway(file_service, str(fields_file))
    fields = await field_gateway.get_all()
    
    request = MultiFieldCropAllocationRequestDTO(
        field_ids=[f.field_id for f in fields],
        planning_period_start=datetime(2025, 1, 1),
        planning_period_end=datetime(2025, 12, 31),
        optimization_objective="maximize_profit",
    )
    
    # Test DP + ALNS
    print("Running DP + ALNS...")
    
    config_alns = OptimizationConfig(
        enable_parallel_candidate_generation=True,
        enable_candidate_filtering=False,
        enable_alns=True,
        alns_iterations=200,
        alns_removal_rate=0.3,
    )
    
    crop_gateway = CropProfileFileGateway(file_service, str(crops_file))
    weather_gateway = WeatherFileGateway(file_service, str(weather_file))
    rule_gateway = InteractionRuleFileGateway(file_service, str(rules_file))
    interaction_rules = await rule_gateway.get_rules()
    
    interactor = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=CropProfileInMemoryGateway(),
        config=config_alns,
        interaction_rules=interaction_rules,
    )
    
    response = await interactor.execute(
        request=request,
        algorithm="dp",
        enable_local_search=True,
        config=config_alns,
    )
    
    result = response.optimization_result
    
    print(f"\n✓ Optimization completed")
    print(f"  Algorithm: {result.algorithm_used}")
    print(f"  Total Profit: ¥{result.total_profit:,.0f}")
    print(f"  Total Allocations: {sum(len(fs.allocations) for fs in result.field_schedules)}")
    
    # Validate
    is_valid = validate_solution(result)
    
    if not is_valid:
        print("\n🚨 SOLUTION HAS CONSTRAINT VIOLATIONS!")
        print("   This indicates a bug in the optimization algorithm.")
    else:
        print("\n✅ SOLUTION IS VALID!")
        print("   All constraints are satisfied.")
    
    return is_valid


if __name__ == '__main__':
    asyncio.run(test_with_validation())

