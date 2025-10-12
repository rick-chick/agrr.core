"""Tests for NeighborGeneratorService."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.usecase.services.neighbor_generator_service import (
    NeighborGeneratorService,
)


@pytest.mark.unit
def test_neighbor_generator_service_creates_default_operations():
    """Test that service creates default operations."""
    config = OptimizationConfig()
    service = NeighborGeneratorService(config)
    
    # Verify default operations are created
    assert len(service.operations) == 8
    operation_names = [op.operation_name for op in service.operations]
    assert "field_swap" in operation_names
    assert "field_move" in operation_names
    assert "crop_insert" in operation_names


@pytest.mark.unit
def test_neighbor_generator_service_generates_neighbors():
    """Test that service generates neighbors."""
    config = OptimizationConfig(enable_neighbor_sampling=False)
    service = NeighborGeneratorService(config)
    
    # Create test data
    field1 = Field(field_id="field1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
    crop1 = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, revenue_per_area=1000.0)
    
    alloc1 = CropAllocation(
        allocation_id="alloc1",
        field=field1,
        crop=crop1,
        quantity=1000.0,
        start_date=datetime(2024, 4, 1),
        completion_date=datetime(2024, 8, 31),
        growth_days=150,
        accumulated_gdd=1500.0,
        total_cost=15000.0,
        expected_revenue=250000.0,
        profit=235000.0,
        area_used=250.0,
    )
    
    solution = [alloc1]
    candidates = []
    fields = [field1]
    crops = [crop1]
    
    # Generate neighbors
    neighbors = service.generate_neighbors(solution, candidates, fields, crops)
    
    # Verify some neighbors are generated
    # At minimum, field_remove should generate 1 neighbor (empty solution)
    assert len(neighbors) >= 1


@pytest.mark.unit
def test_neighbor_generator_service_with_sampling():
    """Test that service generates neighbors with sampling."""
    config = OptimizationConfig(
        enable_neighbor_sampling=True,
        max_neighbors_per_iteration=50,
    )
    service = NeighborGeneratorService(config)
    
    # Create test data with multiple allocations
    field1 = Field(field_id="field1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
    field2 = Field(field_id="field2", name="Field 2", area=800.0, daily_fixed_cost=90.0)
    
    crop1 = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, revenue_per_area=1000.0)
    crop2 = Crop(crop_id="wheat", name="Wheat", area_per_unit=0.3, revenue_per_area=900.0)
    
    allocations = []
    for i in range(5):
        alloc = CropAllocation(
            allocation_id=f"alloc{i}",
            field=field1 if i % 2 == 0 else field2,
            crop=crop1 if i % 2 == 0 else crop2,
            quantity=1000.0,
            start_date=datetime(2024, 4 + i, 1),
            completion_date=datetime(2024, 8 + i, 30),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=15000.0,
            expected_revenue=250000.0,
            profit=235000.0,
            area_used=250.0,
        )
        allocations.append(alloc)
    
    candidates = []
    fields = [field1, field2]
    crops = [crop1, crop2]
    
    # Generate neighbors
    neighbors = service.generate_neighbors(allocations, candidates, fields, crops)
    
    # Verify neighbors are limited by sampling
    assert len(neighbors) <= config.max_neighbors_per_iteration


@pytest.mark.unit
def test_neighbor_generator_service_respects_operation_weights():
    """Test that service respects operation weights in sampling."""
    # Configure with specific operation weights
    config = OptimizationConfig(
        enable_neighbor_sampling=True,
        max_neighbors_per_iteration=100,
        operation_weights={
            "field_swap": 0.5,  # 50% of neighbors
            "field_remove": 0.5,  # 50% of neighbors
            "field_move": 0.0,  # No neighbors
            "crop_insert": 0.0,
            "crop_change": 0.0,
            "period_replace": 0.0,
            "quantity_adjust": 0.0,
        }
    )
    service = NeighborGeneratorService(config)
    
    # Create test data
    field1 = Field(field_id="field1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
    field2 = Field(field_id="field2", name="Field 2", area=800.0, daily_fixed_cost=90.0)
    
    crop1 = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, revenue_per_area=1000.0)
    
    alloc1 = CropAllocation(
        allocation_id="alloc1",
        field=field1,
        crop=crop1,
        quantity=1000.0,
        start_date=datetime(2024, 4, 1),
        completion_date=datetime(2024, 8, 31),
        growth_days=150,
        accumulated_gdd=1500.0,
        total_cost=15000.0,
        expected_revenue=250000.0,
        profit=235000.0,
        area_used=250.0,
    )
    
    alloc2 = CropAllocation(
        allocation_id="alloc2",
        field=field2,
        crop=crop1,
        quantity=1000.0,
        start_date=datetime(2024, 5, 1),
        completion_date=datetime(2024, 9, 30),
        growth_days=150,
        accumulated_gdd=1500.0,
        total_cost=15000.0,
        expected_revenue=250000.0,
        profit=235000.0,
        area_used=250.0,
    )
    
    solution = [alloc1, alloc2]
    candidates = []
    fields = [field1, field2]
    crops = [crop1]
    
    # Generate neighbors
    neighbors = service.generate_neighbors(solution, candidates, fields, crops)
    
    # Verify neighbors are generated (field_swap and field_remove only)
    assert len(neighbors) > 0
    # Total should be roughly 100 (or less if operations don't generate enough)
    assert len(neighbors) <= 100

