"""Detailed time overlap check for ALNS solution."""

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


def check_time_overlaps(field_schedule):
    """Check for time overlaps in a single field."""
    
    field = field_schedule.field
    allocations = sorted(field_schedule.allocations, key=lambda a: a.start_date)
    
    print(f"\n{'='*80}")
    print(f"Field: {field.name} ({field.area} m²)")
    print(f"{'='*80}")
    print(f"Allocations: {len(allocations)}")
    
    overlaps_found = []
    
    for i, alloc in enumerate(allocations, 1):
        print(f"\n{i}. {alloc.crop.name} ({alloc.crop.variety or 'N/A'})")
        print(f"   Start:  {alloc.start_date.date()}")
        print(f"   End:    {alloc.completion_date.date()}")
        print(f"   Days:   {alloc.growth_days}")
        print(f"   Area:   {alloc.area_used:.2f} m²")
        print(f"   Profit: ¥{alloc.profit:,.0f}")
        
        # Check overlap with all other allocations
        for j, other in enumerate(allocations, 1):
            if i >= j:
                continue
            
            # Check if periods overlap
            overlap = not (
                alloc.completion_date < other.start_date or
                other.completion_date < alloc.start_date
            )
            
            if overlap:
                overlaps_found.append((i, j, alloc, other))
                print(f"\n   ❌ OVERLAPS WITH #{j}:")
                print(f"      This:  {alloc.start_date.date()} - {alloc.completion_date.date()}")
                print(f"      Other: {other.start_date.date()} - {other.completion_date.date()}")
                
                # Calculate overlap period
                overlap_start = max(alloc.start_date, other.start_date)
                overlap_end = min(alloc.completion_date, other.completion_date)
                overlap_days = (overlap_end - overlap_start).days + 1
                print(f"      Overlap: {overlap_start.date()} - {overlap_end.date()} ({overlap_days} days)")
    
    return overlaps_found


async def test_overlap():
    """Test for time overlaps in ALNS solution."""
    
    test_data = Path(__file__).parent.parent / 'test_data'
    
    fields_file = test_data / 'allocation_fields_large.json'
    crops_file = test_data / 'allocation_crops_6types.json'
    weather_file = test_data / 'allocation_weather_1760533282.json'
    rules_file = test_data / 'allocation_rules_1760533282.json'
    
    file_service = FileService()
    
    # Create gateways
    field_gateway = FieldFileGateway(file_service, str(fields_file))
    crop_gateway = CropProfileFileGateway(file_service, str(crops_file))
    weather_gateway = WeatherFileGateway(file_service, str(weather_file))
    rule_gateway = InteractionRuleFileGateway(file_service, str(rules_file))
    
    fields = await field_gateway.get_all()
    interaction_rules = await rule_gateway.get_rules()
    
    request = MultiFieldCropAllocationRequestDTO(
        field_ids=[f.field_id for f in fields],
        planning_period_start=datetime(2025, 1, 1),
        planning_period_end=datetime(2025, 12, 31),
        optimization_objective="maximize_profit",
    )
    
    # Run DP + ALNS
    print("Running DP + ALNS...")
    
    config = OptimizationConfig(
        enable_parallel_candidate_generation=True,
        enable_candidate_filtering=False,
        enable_alns=True,
        alns_iterations=200,
        alns_removal_rate=0.3,
    )
    
    interactor = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=CropProfileInMemoryGateway(),
        config=config,
        interaction_rules=interaction_rules,
    )
    
    response = await interactor.execute(
        request=request,
        algorithm="dp",
        enable_local_search=True,
        config=config,
    )
    
    result = response.optimization_result
    
    print(f"\n✓ Optimization completed")
    print(f"  Total Allocations: {sum(len(fs.allocations) for fs in result.field_schedules)}")
    print(f"  Total Profit: ¥{result.total_profit:,.0f}")
    
    # Check each field for overlaps
    total_overlaps = []
    
    for field_schedule in result.field_schedules:
        overlaps = check_time_overlaps(field_schedule)
        total_overlaps.extend(overlaps)
    
    # Summary
    print("\n" + "="*80)
    print("OVERLAP CHECK SUMMARY")
    print("="*80)
    
    if total_overlaps:
        print(f"\n❌ Found {len(total_overlaps)} time overlaps!")
        print("\nThis is a CRITICAL BUG in the optimization algorithm.")
        print("Same field cannot have overlapping cultivations.")
        return False
    else:
        print(f"\n✅ No time overlaps found!")
        print(f"   All allocations are properly scheduled.")
        print(f"\n   Total allocations: {sum(len(fs.allocations) for fs in result.field_schedules)}")
        print(f"   This means multiple crop rotations per field (which is valid).")
        return True


if __name__ == '__main__':
    asyncio.run(test_overlap())

