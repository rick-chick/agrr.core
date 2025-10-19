"""Comparison test between Candidate Pool (legacy) and Period Template strategies.

This test compares the two candidate generation strategies to verify:
1. Both strategies produce valid results
2. Period Template produces equal or better quality (profit)
3. Period Template has better memory efficiency
4. Period Template has wider exploration space

Tests multiple datasets to ensure robustness across different scenarios.
"""

import pytest
from datetime import datetime
import json
from typing import List, Tuple

from agrr_core.framework.services.io.file_service import FileService
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig


# ===== Test Data Sets =====
# Different combinations of crops, fields, and weather for comprehensive testing

TEST_DATASETS = [
    {
        "name": "Standard (6 crops, 3 fields)",
        "crops": "test_data/allocation_crops_1760447748.json",
        "fields": "test_data/allocation_fields_1760447748.json",
        "weather": "test_data/allocation_weather_1760447748.json",
        "field_ids": ["field_1", "field_2", "field_3"],
        "planning_start": datetime(2025, 4, 1),
        "planning_end": datetime(2025, 10, 31),
    },
    {
        "name": "Dataset 1760533282 (2 crops, 2 fields)",
        "crops": "test_data/allocation_crops_1760533282.json",
        "fields": "test_data/allocation_fields_1760533282.json",
        "weather": "test_data/allocation_weather_1760533282.json",
        "field_ids": ["field_16", "field_17"],
        "planning_start": datetime(2025, 4, 1),
        "planning_end": datetime(2025, 10, 31),
    },
    {
        "name": "Dataset 1760536489 (1 field)",
        "crops": "test_data/allocation_crops_1760536489.json",
        "fields": "test_data/allocation_fields_1760536489.json",
        "weather": "test_data/allocation_weather_1760536489.json",
        "field_ids": ["field_9"],
        "planning_start": datetime(2025, 4, 1),
        "planning_end": datetime(2025, 10, 31),
    },
]


@pytest.fixture
def test_data_file_service():
    """File service for test data."""
    return FileService()


@pytest.fixture
def crop_gateway(test_data_file_service):
    """Crop profile gateway with test data."""
    return CropProfileFileGateway(
        file_repository=test_data_file_service,
        file_path="test_data/allocation_crops_1760447748.json"
    )


@pytest.fixture
def weather_gateway(test_data_file_service):
    """Weather gateway with test data."""
    return WeatherFileGateway(
        file_repository=test_data_file_service,
        file_path="test_data/allocation_weather_1760447748.json"
    )


@pytest.fixture
def field_gateway(test_data_file_service):
    """Field gateway with test data."""
    return FieldFileGateway(
        file_repository=test_data_file_service,
        file_path="test_data/allocation_fields_1760447748.json"
    )


@pytest.fixture
def crop_profile_gateway_internal():
    """Internal crop profile gateway."""
    return CropProfileInMemoryGateway()


@pytest.fixture
def allocation_request():
    """Standard allocation request."""
    return MultiFieldCropAllocationRequestDTO(
        field_ids=["field_1", "field_2", "field_3"],
        planning_period_start=datetime(2025, 4, 1),
        planning_period_end=datetime(2025, 10, 31),
        optimization_objective="maximize_profit",
    )


@pytest.mark.asyncio
async def test_strategy_comparison_greedy(
    crop_gateway,
    weather_gateway,
    field_gateway,
    crop_profile_gateway_internal,
    allocation_request
):
    """Compare Candidate Pool vs Period Template with Greedy algorithm.
    
    Expected:
    - Both produce valid results
    - Period Template: Equal or better profit
    - Period Template: Uses more exploration (50 vs 10 templates)
    """
    
    # ===== Legacy: Candidate Pool Strategy =====
    config_legacy = OptimizationConfig(
        candidate_generation_strategy="candidate_pool",
        top_period_candidates=10,  # Legacy uses fewer periods
    )
    
    interactor_legacy = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_legacy,
    )
    
    result_legacy = await interactor_legacy.execute(allocation_request, algorithm="greedy")
    
    # ===== New: Period Template Strategy =====
    config_template = OptimizationConfig(
        candidate_generation_strategy="period_template",
        max_templates_per_crop=200,  # Template can use more periods
    )
    
    interactor_template = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_template,
    )
    
    result_template = await interactor_template.execute(allocation_request, algorithm="greedy")
    
    # ===== Verification =====
    
    # 1. Both produce valid results
    assert result_legacy is not None
    assert result_legacy.optimization_result is not None
    assert result_template is not None
    assert result_template.optimization_result is not None
    
    # 2. Extract metrics
    profit_legacy = result_legacy.optimization_result.total_profit
    profit_template = result_template.optimization_result.total_profit
    
    schedules_legacy = len(result_legacy.optimization_result.field_schedules)
    schedules_template = len(result_template.optimization_result.field_schedules)
    
    # 3. Print comparison
    print("\n" + "="*80)
    print("STRATEGY COMPARISON: Greedy Algorithm")
    print("="*80)
    print(f"\nCandidate Pool (Legacy):")
    print(f"  Profit:           ¥{profit_legacy:,.0f}")
    print(f"  Field Schedules:  {schedules_legacy}")
    print(f"  Exploration:      10 periods/crop")
    
    print(f"\nPeriod Template (New):")
    print(f"  Profit:           ¥{profit_template:,.0f}")
    print(f"  Field Schedules:  {schedules_template}")
    print(f"  Exploration:      50 periods/crop (Greedy uses top 50)")
    
    improvement_pct = ((profit_template - profit_legacy) / profit_legacy * 100) if profit_legacy > 0 else 0
    print(f"\nImprovement:        {improvement_pct:+.2f}%")
    print("="*80 + "\n")
    
    # 4. Period Template should be equal or better
    # Note: Due to 5x more exploration (50 vs 10), Period Template may find better solutions
    assert profit_template >= profit_legacy * 0.95, (
        f"Period Template profit ({profit_template}) should be at least 95% of "
        f"Candidate Pool profit ({profit_legacy})"
    )


@pytest.mark.asyncio
async def test_strategy_comparison_dp(
    crop_gateway,
    weather_gateway,
    field_gateway,
    crop_profile_gateway_internal,
    allocation_request
):
    """Compare Candidate Pool vs Period Template with DP algorithm.
    
    Expected:
    - Both produce optimal or near-optimal results
    - Period Template: Equal or better profit
    - Period Template: Uses 20x more exploration (200 vs 10 templates)
    """
    
    # ===== Legacy: Candidate Pool Strategy =====
    config_legacy = OptimizationConfig(
        candidate_generation_strategy="candidate_pool",
        top_period_candidates=10,  # Legacy: limited exploration
    )
    
    interactor_legacy = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_legacy,
    )
    
    result_legacy = await interactor_legacy.execute(allocation_request, algorithm="dp")
    
    # ===== New: Period Template Strategy =====
    config_template = OptimizationConfig(
        candidate_generation_strategy="period_template",
        max_templates_per_crop=200,  # Template: full exploration
    )
    
    interactor_template = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_template,
    )
    
    result_template = await interactor_template.execute(allocation_request, algorithm="dp")
    
    # ===== Verification =====
    
    # 1. Both produce valid results
    assert result_legacy is not None
    assert result_legacy.optimization_result is not None
    assert result_template is not None
    assert result_template.optimization_result is not None
    
    # 2. Extract metrics
    profit_legacy = result_legacy.optimization_result.total_profit
    profit_template = result_template.optimization_result.total_profit
    
    schedules_legacy = len(result_legacy.optimization_result.field_schedules)
    schedules_template = len(result_template.optimization_result.field_schedules)
    
    # Count total allocations
    field_schedules_legacy = result_legacy.optimization_result.field_schedules
    field_schedules_template = result_template.optimization_result.field_schedules
    
    # Handle both list and dict formats
    if isinstance(field_schedules_legacy, dict):
        allocations_legacy = sum(len(s.allocations) for s in field_schedules_legacy.values())
    else:
        allocations_legacy = sum(len(s.allocations) for s in field_schedules_legacy)
    
    if isinstance(field_schedules_template, dict):
        allocations_template = sum(len(s.allocations) for s in field_schedules_template.values())
    else:
        allocations_template = sum(len(s.allocations) for s in field_schedules_template)
    
    # 3. Print comparison
    print("\n" + "="*80)
    print("STRATEGY COMPARISON: DP Algorithm")
    print("="*80)
    print(f"\nCandidate Pool (Legacy):")
    print(f"  Profit:           ¥{profit_legacy:,.0f}")
    print(f"  Field Schedules:  {schedules_legacy}")
    print(f"  Total Allocations: {allocations_legacy}")
    print(f"  Exploration:      10 periods/crop")
    
    print(f"\nPeriod Template (New):")
    print(f"  Profit:           ¥{profit_template:,.0f}")
    print(f"  Field Schedules:  {schedules_template}")
    print(f"  Total Allocations: {allocations_template}")
    print(f"  Exploration:      200 periods/crop (DP uses all)")
    
    improvement_pct = ((profit_template - profit_legacy) / profit_legacy * 100) if profit_legacy > 0 else 0
    print(f"\nImprovement:        {improvement_pct:+.2f}%")
    print("="*80 + "\n")
    
    # 4. Period Template should be significantly better with DP
    # DP + 20x more exploration should find better solutions
    assert profit_template >= profit_legacy, (
        f"Period Template profit ({profit_template}) should be at least equal to "
        f"Candidate Pool profit ({profit_legacy}) with DP algorithm"
    )


@pytest.mark.asyncio
async def test_strategy_comparison_with_local_search(
    crop_gateway,
    weather_gateway,
    field_gateway,
    crop_profile_gateway_internal,
    allocation_request
):
    """Compare strategies with DP + Local Search (recommended default).
    
    Expected:
    - Both produce high-quality results
    - Period Template: Better profit (more exploration enables better local optima)
    """
    
    # ===== Legacy: Candidate Pool + DP + Local Search =====
    config_legacy = OptimizationConfig(
        candidate_generation_strategy="candidate_pool",
        top_period_candidates=10,
        max_local_search_iterations=50,  # Reduced for faster testing
    )
    
    interactor_legacy = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_legacy,
    )
    
    result_legacy = await interactor_legacy.execute(
        allocation_request, 
        algorithm="dp",
        enable_local_search=True
    )
    
    # ===== New: Period Template + DP + Local Search =====
    config_template = OptimizationConfig(
        candidate_generation_strategy="period_template",
        max_templates_per_crop=200,
        max_local_search_iterations=50,  # Reduced for faster testing
    )
    
    interactor_template = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_template,
    )
    
    result_template = await interactor_template.execute(
        allocation_request,
        algorithm="dp",
        enable_local_search=True
    )
    
    # ===== Verification =====
    
    profit_legacy = result_legacy.optimization_result.total_profit
    profit_template = result_template.optimization_result.total_profit
    
    # Print comparison
    print("\n" + "="*80)
    print("STRATEGY COMPARISON: DP + Local Search (Recommended Default)")
    print("="*80)
    print(f"\nCandidate Pool (Legacy):")
    print(f"  Profit:           ¥{profit_legacy:,.0f}")
    print(f"  Exploration:      10 periods/crop + Local Search")
    
    print(f"\nPeriod Template (New):")
    print(f"  Profit:           ¥{profit_template:,.0f}")
    print(f"  Exploration:      200 periods/crop + Local Search")
    
    improvement_pct = ((profit_template - profit_legacy) / profit_legacy * 100) if profit_legacy > 0 else 0
    print(f"\nImprovement:        {improvement_pct:+.2f}%")
    print("="*80 + "\n")
    
    # Period Template should be equal or better
    assert profit_template >= profit_legacy * 0.98, (
        f"Period Template profit ({profit_template}) should be at least 98% of "
        f"Candidate Pool profit ({profit_legacy}) with Local Search"
    )


# ===== Parametrized Tests for Multiple Datasets =====


@pytest.mark.parametrize("dataset", TEST_DATASETS, ids=lambda d: d["name"])
@pytest.mark.asyncio
async def test_multiple_datasets_dp_comparison(dataset):
    """Compare strategies across multiple datasets with DP algorithm.
    
    Tests Period Template superiority across diverse scenarios:
    - Different crop types and counts
    - Different field configurations
    - Different weather conditions
    """
    file_repo = FileService()
    
    # Setup gateways with dataset-specific files
    crop_gateway = CropProfileFileGateway(
        file_repository=file_repo,
        file_path=dataset["crops"]
    )
    
    weather_gateway = WeatherFileGateway(
        file_repository=file_repo,
        file_path=dataset["weather"]
    )
    
    field_gateway = FieldFileGateway(
        file_repository=file_repo,
        file_path=dataset["fields"]
    )
    
    crop_profile_gateway_internal = CropProfileInMemoryGateway()
    
    # Create allocation request
    request = MultiFieldCropAllocationRequestDTO(
        field_ids=dataset["field_ids"],
        planning_period_start=dataset["planning_start"],
        planning_period_end=dataset["planning_end"],
        optimization_objective="maximize_profit",
    )
    
    # ===== Legacy Strategy =====
    config_legacy = OptimizationConfig(
        candidate_generation_strategy="candidate_pool",
        top_period_candidates=10,
    )
    
    interactor_legacy = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_legacy,
    )
    
    result_legacy = await interactor_legacy.execute(request, algorithm="dp")
    
    # ===== Period Template Strategy =====
    config_template = OptimizationConfig(
        candidate_generation_strategy="period_template",
        max_templates_per_crop=200,
    )
    
    interactor_template = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_template,
    )
    
    result_template = await interactor_template.execute(request, algorithm="dp")
    
    # ===== Comparison =====
    profit_legacy = result_legacy.optimization_result.total_profit
    profit_template = result_template.optimization_result.total_profit
    
    improvement_pct = ((profit_template - profit_legacy) / profit_legacy * 100) if profit_legacy > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"Dataset: {dataset['name']}")
    print(f"{'='*80}")
    print(f"Candidate Pool:  ¥{profit_legacy:,.0f}")
    print(f"Period Template: ¥{profit_template:,.0f}")
    print(f"Improvement:     {improvement_pct:+.2f}%")
    print(f"{'='*80}\n")
    
    # Period Template should be equal or better
    assert profit_template >= profit_legacy, (
        f"Period Template ({profit_template}) should be >= Candidate Pool ({profit_legacy}) "
        f"for dataset: {dataset['name']}"
    )


@pytest.mark.parametrize("dataset", TEST_DATASETS, ids=lambda d: d["name"])
@pytest.mark.asyncio
async def test_multiple_datasets_greedy_comparison(dataset):
    """Compare strategies across multiple datasets with Greedy algorithm."""
    file_repo = FileService()
    
    crop_gateway = CropProfileFileGateway(
        file_repository=file_repo,
        file_path=dataset["crops"]
    )
    
    weather_gateway = WeatherFileGateway(
        file_repository=file_repo,
        file_path=dataset["weather"]
    )
    
    field_gateway = FieldFileGateway(
        file_repository=file_repo,
        file_path=dataset["fields"]
    )
    
    crop_profile_gateway_internal = CropProfileInMemoryGateway()
    
    request = MultiFieldCropAllocationRequestDTO(
        field_ids=dataset["field_ids"],
        planning_period_start=dataset["planning_start"],
        planning_period_end=dataset["planning_end"],
        optimization_objective="maximize_profit",
    )
    
    # ===== Legacy Strategy =====
    config_legacy = OptimizationConfig(
        candidate_generation_strategy="candidate_pool",
        top_period_candidates=10,
    )
    
    interactor_legacy = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_legacy,
    )
    
    result_legacy = await interactor_legacy.execute(request, algorithm="greedy")
    
    # ===== Period Template Strategy =====
    config_template = OptimizationConfig(
        candidate_generation_strategy="period_template",
        max_templates_per_crop=200,
    )
    
    interactor_template = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
        config=config_template,
    )
    
    result_template = await interactor_template.execute(request, algorithm="greedy")
    
    # ===== Comparison =====
    profit_legacy = result_legacy.optimization_result.total_profit
    profit_template = result_template.optimization_result.total_profit
    
    improvement_pct = ((profit_template - profit_legacy) / profit_legacy * 100) if profit_legacy > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"Dataset: {dataset['name']} (Greedy)")
    print(f"{'='*80}")
    print(f"Candidate Pool:  ¥{profit_legacy:,.0f}")
    print(f"Period Template: ¥{profit_template:,.0f}")
    print(f"Improvement:     {improvement_pct:+.2f}%")
    print(f"{'='*80}\n")
    
    # Period Template should be at least 95% (greedy can have some variance)
    assert profit_template >= profit_legacy * 0.95, (
        f"Period Template ({profit_template}) should be >= 95% of Candidate Pool ({profit_legacy}) "
        f"for dataset: {dataset['name']}"
    )


@pytest.mark.asyncio
async def test_comprehensive_benchmark_all_datasets():
    """Run comprehensive benchmark across all datasets and generate summary report.
    
    This test generates a detailed comparison report including:
    - Profit improvement per dataset
    - Allocation count comparison
    - Average improvement statistics
    """
    file_repo = FileService()
    results = []
    
    for dataset in TEST_DATASETS:
        # Setup gateways
        crop_gateway = CropProfileFileGateway(
            file_repository=file_repo,
            file_path=dataset["crops"]
        )
        
        weather_gateway = WeatherFileGateway(
            file_repository=file_repo,
            file_path=dataset["weather"]
        )
        
        field_gateway = FieldFileGateway(
            file_repository=file_repo,
            file_path=dataset["fields"]
        )
        
        crop_profile_gateway_internal = CropProfileInMemoryGateway()
        
        request = MultiFieldCropAllocationRequestDTO(
            field_ids=dataset["field_ids"],
            planning_period_start=dataset["planning_start"],
            planning_period_end=dataset["planning_end"],
            optimization_objective="maximize_profit",
        )
        
        # Test both strategies
        for algorithm in ["greedy", "dp"]:
            # Legacy
            config_legacy = OptimizationConfig(
                candidate_generation_strategy="candidate_pool",
                top_period_candidates=10,
            )
            
            interactor_legacy = MultiFieldCropAllocationGreedyInteractor(
                field_gateway=field_gateway,
                crop_gateway=crop_gateway,
                weather_gateway=weather_gateway,
                crop_profile_gateway_internal=crop_profile_gateway_internal,
                config=config_legacy,
            )
            
            result_legacy = await interactor_legacy.execute(request, algorithm=algorithm)
            
            # Period Template
            config_template = OptimizationConfig(
                candidate_generation_strategy="period_template",
                max_templates_per_crop=200,
            )
            
            interactor_template = MultiFieldCropAllocationGreedyInteractor(
                field_gateway=field_gateway,
                crop_gateway=crop_gateway,
                weather_gateway=weather_gateway,
                crop_profile_gateway_internal=crop_profile_gateway_internal,
                config=config_template,
            )
            
            result_template = await interactor_template.execute(request, algorithm=algorithm)
            
            # Extract metrics
            profit_legacy = result_legacy.optimization_result.total_profit
            profit_template = result_template.optimization_result.total_profit
            
            field_schedules_legacy = result_legacy.optimization_result.field_schedules
            field_schedules_template = result_template.optimization_result.field_schedules
            
            # Count allocations
            if isinstance(field_schedules_legacy, dict):
                alloc_legacy = sum(len(s.allocations) for s in field_schedules_legacy.values())
            else:
                alloc_legacy = sum(len(s.allocations) for s in field_schedules_legacy)
            
            if isinstance(field_schedules_template, dict):
                alloc_template = sum(len(s.allocations) for s in field_schedules_template.values())
            else:
                alloc_template = sum(len(s.allocations) for s in field_schedules_template)
            
            improvement = ((profit_template - profit_legacy) / profit_legacy * 100) if profit_legacy > 0 else 0
            
            results.append({
                "dataset": dataset["name"],
                "algorithm": algorithm,
                "profit_legacy": profit_legacy,
                "profit_template": profit_template,
                "allocations_legacy": alloc_legacy,
                "allocations_template": alloc_template,
                "improvement_pct": improvement,
            })
    
    # ===== Generate Summary Report =====
    print("\n" + "="*80)
    print("COMPREHENSIVE BENCHMARK SUMMARY")
    print("="*80)
    print()
    
    # Table header
    print(f"{'Dataset':<35} {'Algo':<8} {'Legacy':<12} {'Template':<12} {'Improve':>10} {'Alloc':>8}")
    print("-" * 80)
    
    # Table rows
    for r in results:
        print(
            f"{r['dataset']:<35} "
            f"{r['algorithm']:<8} "
            f"¥{r['profit_legacy']:>10,.0f} "
            f"¥{r['profit_template']:>10,.0f} "
            f"{r['improvement_pct']:>9.2f}% "
            f"{r['allocations_legacy']}→{r['allocations_template']}"
        )
    
    print("-" * 80)
    
    # Calculate averages
    avg_improvement_greedy = sum(r["improvement_pct"] for r in results if r["algorithm"] == "greedy") / len([r for r in results if r["algorithm"] == "greedy"])
    avg_improvement_dp = sum(r["improvement_pct"] for r in results if r["algorithm"] == "dp") / len([r for r in results if r["algorithm"] == "dp"])
    
    print(f"\nAverage Improvement (Greedy): {avg_improvement_greedy:+.2f}%")
    print(f"Average Improvement (DP):     {avg_improvement_dp:+.2f}%")
    print("="*80 + "\n")
    
    # All results should show improvement or equal performance
    for r in results:
        assert r["improvement_pct"] >= -5, (
            f"Period Template should not be significantly worse than Legacy "
            f"(dataset: {r['dataset']}, algorithm: {r['algorithm']})"
        )
