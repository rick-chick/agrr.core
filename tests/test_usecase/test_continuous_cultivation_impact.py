"""Tests for continuous cultivation impact in optimization.

This test suite verifies that InteractionRule for continuous cultivation
is correctly applied in the optimization process.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    AllocationCandidate,
    MultiFieldCropAllocationGreedyInteractor,
)
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.entity.value_objects.rule_type import RuleType
from agrr_core.usecase.services.interaction_rule_service import InteractionRuleService


@pytest.fixture
def mock_crop_profile_gateway_internal():
    """Mock CropProfileGateway for internal use."""
    gateway = AsyncMock()
    gateway.save.return_value = None
    gateway.delete.return_value = None
    return gateway


class TestAllocationCandidateWithInteractionImpact:
    """Test AllocationCandidate with interaction impact."""
    
    def test_candidate_with_no_impact(self):
        """Test that candidate with no impact (1.0) returns original revenue."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0)
        
        candidate = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            area_used=500.0,
        )
        
        # No previous crop, no interaction rules
        # Note: When field_schedules is empty dict and no planning_start_date,
        # soil_recovery_factor defaults to 1.1 (maximum bonus)
        metrics = candidate.get_metrics(
            current_allocations=[],
            field_schedules={},
            interaction_rules=[]
        )
        
        # Revenue should be: 500 * 50000 * 1.1 = 27,500,000
        # (1.1 = soil_recovery_factor when no previous crop and no planning_start_date)
        assert metrics.revenue == pytest.approx(27500000.0, rel=0.001)
        assert metrics.cost == 150 * 5000.0  # 750,000
    
    def test_candidate_with_continuous_cultivation_penalty(self):
        """Test that continuous cultivation penalty reduces revenue."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("eggplant", "Eggplant", 0.5, revenue_per_area=50000.0, groups=["Solanaceae"])
        previous_crop = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        
        # Create previous allocation (tomato)
        previous_allocation = CropAllocation(
            allocation_id="prior",
            field=field,
            crop=previous_crop,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0,
            expected_revenue=None,
            profit=None
        )
        
        # Create interaction rule (Solanaceae continuous cultivation)
        interaction_rule = InteractionRule(
            rule_id="rule_001",
            rule_type=RuleType.CONTINUOUS_CULTIVATION,
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,  # 30% penalty
            is_directional=True
        )
        
        candidate = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2025, 9, 1),
            completion_date=datetime(2026, 1, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            area_used=500.0,
        )
        
        # Get metrics with context
        metrics = candidate.get_metrics(
            current_allocations=[],
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=[interaction_rule]
        )
        
        # Revenue should be: 500 * 50000 * 0.7 = 17,500,000 (30% reduced)
        assert metrics.revenue == 17500000.0
        assert metrics.cost == 150 * 5000.0  # Cost unchanged: 750,000
        
        # Profit = revenue - cost = 17,500,000 - 750,000 = 16,750,000
        expected_profit = 17500000.0 - 750000.0
        assert metrics.profit == pytest.approx(expected_profit, rel=0.001)
    
    def test_candidate_with_max_revenue_limit_and_impact(self):
        """Test that both max_revenue and interaction_impact are applied."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop(
            "tomato", "Tomato", 0.5,
            revenue_per_area=50000.0,
            max_revenue=15000000.0,  # Revenue cap
            groups=["Solanaceae"]
        )
        previous_crop = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        
        # Create previous allocation (tomato - same crop)
        previous_allocation = CropAllocation(
            allocation_id="prior",
            field=field,
            crop=previous_crop,
            area_used=500.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 3, 31),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=None,
            profit=None
        )
        
        # Create interaction rule (20% penalty)
        interaction_rule = InteractionRule(
            rule_id="rule_001",
            rule_type=RuleType.CONTINUOUS_CULTIVATION,
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.8,  # 20% penalty
            is_directional=True
        )
        
        candidate = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            area_used=500.0,
        )
        
        # Get metrics with context
        metrics = candidate.get_metrics(
            current_allocations=[],
            field_schedules={"f1": [previous_allocation]},
            interaction_rules=[interaction_rule]
        )
        
        # Calculation order:
        # 1. Base revenue: 500 * 50000 = 25,000,000
        # 2. × interaction_impact (0.8) = 20,000,000
        # 3. × soil_recovery_factor (1.1) = 22,000,000
        # 4. Apply max_revenue: min(22,000,000, 15,000,000) = 15,000,000
        # Note: max_revenue is applied AFTER all multipliers in the new design
        assert metrics.revenue == pytest.approx(15000000.0, rel=0.001)

