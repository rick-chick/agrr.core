"""Tests for OptimizationResultBuilder."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.optimization_result_builder import (
    OptimizationResultBuilder,
)

@pytest.mark.unit
class TestBuild:
    """Tests for build method."""
    
    def test_build_empty_allocations(self):
        """Test building result with no allocations."""
        builder = OptimizationResultBuilder()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        
        result = builder.build(
            allocations=[],
            fields=[field],
            computation_time=5.0,
            algorithm_used="Greedy"
        )
        
        assert result is not None
        assert result.total_cost == 0.0
        assert result.total_revenue == 0.0
        assert result.total_profit == 0.0
        assert len(result.field_schedules) == 1
        assert result.field_schedules[0].total_area_used == 0.0
        assert result.optimization_time == 5.0
        assert result.algorithm_used == "Greedy"
        assert result.is_optimal is False
    
    def test_build_single_allocation(self):
        """Test building result with single allocation."""
        builder = OptimizationResultBuilder()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=750000.0,
            expected_revenue=5000000.0,
            profit=4250000.0,
            area_used=500.0,
        )
        
        result = builder.build(
            allocations=[alloc],
            fields=[field],
            computation_time=10.5,
            algorithm_used="Greedy + Local Search"
        )
        
        assert result.total_cost == 750000.0
        assert result.total_revenue == 5000000.0
        assert result.total_profit == 4250000.0
        assert result.crop_areas["rice"] == 500.0
        assert result.optimization_time == 10.5
        assert result.algorithm_used == "Greedy + Local Search"
        
        # Check field schedule
        assert len(result.field_schedules) == 1
        schedule = result.field_schedules[0]
        assert schedule.field.field_id == "f1"
        assert schedule.total_area_used == 500.0
        assert schedule.utilization_rate == pytest.approx(50.0)
    
    def test_build_multiple_allocations_single_field(self):
        """Test building result with multiple allocations in single field."""
        builder = OptimizationResultBuilder()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        wheat = Crop("wheat", "Wheat", 0.3, revenue_per_area=8000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=rice,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 7, 31),
            growth_days=120,
            accumulated_gdd=1200.0,
            total_cost=600000.0,
            expected_revenue=2500000.0,
            profit=1900000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=wheat,
            start_date=datetime(2024, 8, 1),
            completion_date=datetime(2024, 11, 30),
            growth_days=120,
            accumulated_gdd=1100.0,
            total_cost=600000.0,
            expected_revenue=4000000.0,
            profit=3400000.0,
            area_used=500.0,
        )
        
        result = builder.build(
            allocations=[alloc1, alloc2],
            fields=[field],
            computation_time=8.0,
            algorithm_used="Greedy"
        )
        
        assert result.total_cost == 1200000.0
        assert result.total_revenue == 6500000.0
        assert result.total_profit == 5300000.0
        assert result.crop_areas["rice"] == 250.0
        assert result.crop_areas["wheat"] == 500.0
        
        # Check field schedule
        schedule = result.field_schedules[0]
        assert len(schedule.allocations) == 2
        assert schedule.total_area_used == 750.0
        assert schedule.utilization_rate == pytest.approx(75.0)
    
    def test_build_multiple_fields(self):
        """Test building result with allocations across multiple fields."""
        builder = OptimizationResultBuilder()
        
        field1 = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        field2 = Field("f2", "Field 2", 800.0, 4500.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=750000.0,
            expected_revenue=5000000.0,
            profit=4250000.0,
            area_used=500.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field2,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=675000.0,
            expected_revenue=4000000.0,
            profit=3325000.0,
            area_used=400.0,
        )
        
        result = builder.build(
            allocations=[alloc1, alloc2],
            fields=[field1, field2],
            computation_time=12.3,
            algorithm_used="Greedy + Local Search"
        )
        
        # Global metrics
        assert result.total_cost == 1425000.0
        assert result.total_revenue == 9000000.0
        assert result.total_profit == 7575000.0
        assert result.crop_areas["rice"] == 900.0
        
        # Field schedules
        assert len(result.field_schedules) == 2
        
        # Field 1
        schedule1 = next(s for s in result.field_schedules if s.field.field_id == "f1")
        assert len(schedule1.allocations) == 1
        assert schedule1.total_area_used == 500.0
        assert schedule1.utilization_rate == pytest.approx(50.0)
        
        # Field 2
        schedule2 = next(s for s in result.field_schedules if s.field.field_id == "f2")
        assert len(schedule2.allocations) == 1
        assert schedule2.total_area_used == 400.0
        assert schedule2.utilization_rate == pytest.approx(50.0)
    
    def test_build_with_none_revenue(self):
        """Test building result when some allocations have no revenue."""
        builder = OptimizationResultBuilder()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=None)  # No revenue data
        
        alloc = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=750000.0,
            expected_revenue=None,
            profit=None,
            area_used=500.0,
        )
        
        result = builder.build(
            allocations=[alloc],
            fields=[field],
            computation_time=5.0,
            algorithm_used="Greedy"
        )
        
        assert result.total_cost == 750000.0
        assert result.total_revenue == 0.0  # No revenue
        assert result.total_profit == 0.0  # No profit

@pytest.mark.unit
class TestGroupByField:
    """Tests for _group_by_field method."""
    
    def test_group_by_field_single_field(self):
        """Test grouping with allocations in single field."""
        builder = OptimizationResultBuilder()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=None,
            profit=None,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,
            start_date=datetime(2024, 7, 1),
            completion_date=datetime(2024, 9, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=None,
            profit=None,
            area_used=250.0,
        )
        
        grouped = builder._group_by_field([alloc1, alloc2], [field])
        
        assert "f1" in grouped
        assert len(grouped["f1"]) == 2
    
    def test_group_by_field_multiple_fields(self):
        """Test grouping with allocations across multiple fields."""
        builder = OptimizationResultBuilder()
        
        field1 = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        field2 = Field("f2", "Field 2", 800.0, 4500.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=None,
            profit=None,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field2,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=None,
            profit=None,
            area_used=200.0,
        )
        
        grouped = builder._group_by_field([alloc1, alloc2], [field1, field2])
        
        assert "f1" in grouped
        assert "f2" in grouped
        assert len(grouped["f1"]) == 1
        assert len(grouped["f2"]) == 1
    
    def test_group_by_field_includes_empty_fields(self):
        """Test that fields without allocations are included."""
        builder = OptimizationResultBuilder()
        
        field1 = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        field2 = Field("f2", "Field 2", 800.0, 4500.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25)
        
        alloc = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=None,
            profit=None,
            area_used=250.0,
        )
        
        grouped = builder._group_by_field([alloc], [field1, field2])
        
        assert "f1" in grouped
        assert "f2" in grouped
        assert len(grouped["f1"]) == 1
        assert len(grouped["f2"]) == 0  # Empty field

@pytest.mark.unit
class TestCalculateFieldMetrics:
    """Tests for _calculate_field_metrics method."""
    
    def test_calculate_field_metrics_basic(self):
        """Test basic field metrics calculation."""
        builder = OptimizationResultBuilder()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=750000.0,
            expected_revenue=5000000.0,
            profit=4250000.0,
            area_used=500.0,
        )
        
        metrics = builder._calculate_field_metrics(field, [alloc])
        
        assert metrics['cost'] == 750000.0
        assert metrics['revenue'] == 5000000.0
        assert metrics['profit'] == 4250000.0
        assert metrics['area_used'] == 500.0
        assert metrics['utilization'] == pytest.approx(50.0)
    
    def test_calculate_field_metrics_multiple_allocations(self):
        """Test metrics calculation with multiple allocations."""
        builder = OptimizationResultBuilder()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,
            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 31),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=450000.0,
            expected_revenue=2500000.0,
            profit=2050000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=450000.0,
            expected_revenue=5000000.0,
            profit=4550000.0,
            area_used=500.0,
        )
        
        metrics = builder._calculate_field_metrics(field, [alloc1, alloc2])
        
        assert metrics['cost'] == 900000.0
        assert metrics['revenue'] == 7500000.0
        assert metrics['profit'] == 6600000.0
        assert metrics['area_used'] == 750.0
        assert metrics['utilization'] == pytest.approx(75.0)

@pytest.mark.unit
class TestAggregateMetrics:
    """Tests for _aggregate_metrics method."""
    
    def test_aggregate_metrics_updates_global(self):
        """Test that aggregation updates global metrics."""
        builder = OptimizationResultBuilder()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        wheat = Crop("wheat", "Wheat", 0.3, revenue_per_area=8000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=rice,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 7, 31),
            growth_days=120,
            accumulated_gdd=1200.0,
            total_cost=600000.0,
            expected_revenue=2500000.0,
            profit=1900000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=wheat,
            start_date=datetime(2024, 8, 1),
            completion_date=datetime(2024, 11, 30),
            growth_days=120,
            accumulated_gdd=1100.0,
            total_cost=540000.0,
            expected_revenue=4000000.0,
            profit=3460000.0,
            area_used=500.0,
        )
        
        global_metrics = {
            'total_cost': 0.0,
            'total_revenue': 0.0,
            'total_profit': 0.0,
            'crop_areas': {},
        }
        
        field_metrics = {
            'cost': 1140000.0,
            'revenue': 6500000.0,
            'profit': 5360000.0,
            'area_used': 750.0,
            'utilization': 75.0,
        }
        
        builder._aggregate_metrics(global_metrics, [alloc1, alloc2], field_metrics)
        
        assert global_metrics['total_cost'] == 1140000.0
        assert global_metrics['total_revenue'] == 6500000.0
        assert global_metrics['total_profit'] == 5360000.0
        assert global_metrics['crop_areas']['rice'] == 250.0
        assert global_metrics['crop_areas']['wheat'] == 500.0

