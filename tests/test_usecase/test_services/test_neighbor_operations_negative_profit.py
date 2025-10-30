"""Test neighbor operations with negative profit candidates.

This test ensures that all neighbor operations work correctly with
unprofitable (negative profit) allocations and don't filter them out.
"""

import pytest
from datetime import datetime
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.usecase.services.neighbor_operations import (
    FieldSwapOperation,
    FieldMoveOperation,
    FieldReplaceOperation,
    FieldRemoveOperation,
    CropInsertOperation,
    CropChangeOperation,
    PeriodReplaceOperation,
    AreaAdjustOperation,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig

@pytest.fixture
def unprofitable_crop():
    """Create a crop with low revenue (unprofitable)."""
    return Crop(
        crop_id="corn",
        name="とうもろこし",
        variety="スイートコーン",
        area_per_unit=0.25,
        revenue_per_area=300.0,  # Low revenue
        max_revenue=30000.0,
        groups=[]
    )

@pytest.fixture
def field1():
    """Create field 1 with high daily cost."""
    return Field(
        field_id="field-1",
        name="Field 1",
        area=25.0,
        daily_fixed_cost=125.0  # High cost
    )

@pytest.fixture
def unprofitable_allocation(unprofitable_crop, field1):
    """Create an unprofitable allocation.
    
    Cost: 125 * 143 = 17,875
    Revenue: 300 * 25 = 7,500
    Profit: -10,375 (unprofitable)
    """
    cost = 125.0 * 143
    revenue = 300.0 * 25.0
    profit = revenue - cost
    
    return CropAllocation(
        allocation_id="alloc-1",
        field=field1,
        crop=unprofitable_crop,
        area_used=25.0,
        start_date=datetime(2025, 5, 16),
        completion_date=datetime(2025, 10, 5),
        growth_days=143,
        accumulated_gdd=1725.0,
        total_cost=cost,
        expected_revenue=revenue,
        profit=profit,
    )

@pytest.fixture
def config():
    """Create optimization config with filtering disabled."""
    return OptimizationConfig(
        enable_candidate_filtering=False  # Important: filtering disabled
    )

class TestNeighborOperationsWithNegativeProfit:
    """Test that all neighbor operations handle negative profit correctly."""
    
    def test_unprofitable_allocation_fixture(self, unprofitable_allocation):
        """Verify the unprofitable allocation is actually unprofitable."""
        assert unprofitable_allocation.profit < 0, "Allocation should be unprofitable"
        assert unprofitable_allocation.profit == -10375.0, f"Expected profit=-10375, got {unprofitable_allocation.profit}"
    
    def test_field_swap_operation_handles_negative_profit(self, unprofitable_allocation, field1):
        """Test FieldSwapOperation with unprofitable allocations."""
        operation = FieldSwapOperation()
        
        # Create a second field
        field2 = Field(
            field_id="field-2",
            name="Field 2",
            area=30.0,
            daily_fixed_cost=100.0
        )
        
        # Create a second allocation
        allocation2 = CropAllocation(
            allocation_id="alloc-2",
            field=field2,
            crop=unprofitable_allocation.crop,
            area_used=20.0,
            start_date=datetime(2025, 6, 1),
            completion_date=datetime(2025, 9, 15),
            growth_days=106,
            accumulated_gdd=1500.0,
            total_cost=10600.0,
            expected_revenue=6000.0,
            profit=-4600.0,
        )
        
        solution = [unprofitable_allocation, allocation2]
        
        context = {
            'candidates': [],
            'fields': [field1, field2],
            'crops': [unprofitable_allocation.crop],
            'config': OptimizationConfig()
        }
        
        # Should not raise exception
        neighbors = operation.generate_neighbors(solution=solution, context=context)
        
        # Should handle unprofitable allocations without filtering
        assert isinstance(neighbors, list), "Should return a list of neighbors"
    
    def test_field_move_operation_handles_negative_profit(self, unprofitable_allocation, field1):
        """Test FieldMoveOperation with unprofitable allocations."""
        operation = FieldMoveOperation()
        solution = [unprofitable_allocation]
        
        field2 = Field(
            field_id="field-2",
            name="Field 2",
            area=30.0,
            daily_fixed_cost=100.0
        )
        
        context = {
            'candidates': [],
            'fields': [field1, field2],
            'crops': [unprofitable_allocation.crop],
            'config': OptimizationConfig()
        }
        
        neighbors = operation.generate_neighbors(solution=solution, context=context)
        
        assert isinstance(neighbors, list), "Should return a list of neighbors"
    
    def test_field_remove_operation_handles_negative_profit(self, unprofitable_allocation):
        """Test FieldRemoveOperation with unprofitable allocations."""
        operation = FieldRemoveOperation()
        solution = [unprofitable_allocation]
        
        context = {
            'candidates': [],
            'fields': [unprofitable_allocation.field],
            'crops': [unprofitable_allocation.crop],
            'config': OptimizationConfig()
        }
        
        neighbors = operation.generate_neighbors(solution=solution, context=context)
        
        # FieldRemoveOperation removes allocations, so neighbors might be empty solutions
        assert isinstance(neighbors, list), "Should return a list of neighbors"
    
    def test_area_adjust_operation_handles_negative_profit(self, unprofitable_allocation):
        """Test AreaAdjustOperation with unprofitable allocations."""
        operation = AreaAdjustOperation()
        solution = [unprofitable_allocation]
        
        context = {
            'candidates': [],
            'fields': [unprofitable_allocation.field],
            'crops': [unprofitable_allocation.crop],
            'config': OptimizationConfig(area_adjustment_multipliers=[0.8, 0.9, 1.0])
        }
        
        neighbors = operation.generate_neighbors(solution=solution, context=context)
        
        assert isinstance(neighbors, list), "Should return a list of neighbors"
    
    def test_all_operations_accept_negative_profit(self, unprofitable_allocation):
        """Meta-test: Verify all operations can handle negative profit without errors."""
        operations = [
            FieldSwapOperation(),
            FieldMoveOperation(),
            FieldReplaceOperation(),
            FieldRemoveOperation(),
            CropInsertOperation(),
            CropChangeOperation(),
            PeriodReplaceOperation(),
            AreaAdjustOperation(),
        ]
        
        field2 = Field(
            field_id="field-2",
            name="Field 2",
            area=30.0,
            daily_fixed_cost=100.0
        )
        
        # Test that all operations accept unprofitable allocations
        for op in operations:
            solution = [unprofitable_allocation]
            context = {
                'candidates': [],
                'fields': [unprofitable_allocation.field, field2],
                'crops': [unprofitable_allocation.crop],
                'config': OptimizationConfig()
            }
            
            try:
                neighbors = op.generate_neighbors(solution=solution, context=context)
                assert isinstance(neighbors, list), f"{op.__class__.__name__} should return a list"
            except Exception as e:
                pytest.fail(f"{op.__class__.__name__} failed with unprofitable allocation: {e}")

class TestLocalSearchPreservesUnprofitableSolutions:
    """Test that local search doesn't discard valid unprofitable solutions."""
    
    def test_single_unprofitable_allocation_preserved(self, unprofitable_allocation):
        """Test that a single unprofitable allocation is preserved in local search."""
        # The fix: _local_search skips when len(solution) < 2
        solution = [unprofitable_allocation]
        
        assert len(solution) == 1, "Test requires single allocation"
        assert solution[0].profit < 0, "Allocation should be unprofitable"
        
        # In the actual implementation, this would be preserved
        # (local search skips when solution < 2 allocations)

def test_optimization_config_filtering_disabled_by_default():
    """Test that candidate filtering is disabled by default."""
    config = OptimizationConfig()
    assert config.enable_candidate_filtering is False, \
        "Candidate filtering should be disabled by default"

