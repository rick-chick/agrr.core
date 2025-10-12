"""Tests for continuous cultivation impact in optimization.

This test suite verifies that InteractionRule for continuous cultivation
is correctly applied in the optimization process.
"""

import pytest
from datetime import datetime

from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    AllocationCandidate,
    MultiFieldCropAllocationGreedyInteractor,
)
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.usecase.services.interaction_rule_service import InteractionRuleService


class TestAllocationCandidateWithInteractionImpact:
    """Test AllocationCandidate with interaction impact."""
    
    def test_candidate_with_no_impact(self):
        """Test that candidate with no impact (1.0) returns original revenue."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0)
        
        candidate = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            area_used=500.0,
            previous_crop=None,
            interaction_impact=1.0  # No impact
        )
        
        metrics = candidate.get_metrics()
        
        # Revenue should be: 500 * 50000 = 25,000,000
        assert metrics.revenue == 25000000.0
        assert metrics.cost == 150 * 5000.0  # 750,000
    
    def test_candidate_with_continuous_cultivation_penalty(self):
        """Test that continuous cultivation penalty reduces revenue."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("eggplant", "Eggplant", 0.5, revenue_per_area=50000.0, groups=["Solanaceae"])
        previous_crop = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        
        candidate = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2025, 9, 1),
            completion_date=datetime(2026, 1, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            area_used=500.0,
            previous_crop=previous_crop,
            interaction_impact=0.7  # 30% penalty due to continuous cultivation
        )
        
        metrics = candidate.get_metrics()
        
        # Revenue should be: 500 * 50000 * 0.7 = 17,500,000 (30% reduced)
        assert metrics.revenue == 17500000.0
        assert metrics.cost == 150 * 5000.0  # Cost unchanged: 750,000
        
        # Profit = revenue - cost = 17,500,000 - 750,000 = 16,750,000
        expected_profit = 17500000.0 - 750000.0
        assert metrics.profit == pytest.approx(expected_profit, rel=0.001)
    
    def test_candidate_with_max_revenue_limit_and_impact(self):
        """Test that both max_revenue and interaction_impact are applied."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop(
            "tomato", "Tomato", 0.5,
            revenue_per_area=50000.0,
            max_revenue=15000000.0,  # Revenue cap
            groups=["Solanaceae"]
        )
        
        candidate = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            area_used=500.0,
            interaction_impact=0.8  # 20% penalty
        )
        
        metrics = candidate.get_metrics()
        
        # Base revenue: 500 * 50000 = 25,000,000
        # With impact: 25,000,000 * 0.8 = 20,000,000
        # Max revenue with impact: 15,000,000 * 0.8 = 12,000,000
        # Final revenue: min(20,000,000, 12,000,000) = 12,000,000
        assert metrics.revenue == 12000000.0


class TestInteractionRuleServiceIntegration:
    """Test InteractionRuleService integration with Optimizer."""
    
    def test_get_previous_crop_no_allocations(self):
        """Test getting previous crop when there are no allocations."""
        rules = []
        interaction_rule_service = InteractionRuleService(rules)
        
        interactor = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=None,  # Mock
            crop_requirement_gateway=None,  # Mock
            weather_gateway=None,  # Mock
            interaction_rules=rules
        )
        
        field_schedules = {}
        previous_crop = interactor._get_previous_crop(
            field_id="f1",
            start_date=datetime(2025, 9, 1),
            field_schedules=field_schedules
        )
        
        assert previous_crop is None
    
    def test_get_previous_crop_with_prior_allocation(self):
        """Test getting previous crop from prior allocation."""
        rules = []
        interactor = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=None,
            crop_requirement_gateway=None,
            weather_gateway=None,
            interaction_rules=rules
        )
        
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        
        # Create a prior allocation
        prior_allocation = CropAllocation(
            allocation_id="alloc_001",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0
        )
        
        field_schedules = {"f1": [prior_allocation]}
        
        previous_crop = interactor._get_previous_crop(
            field_id="f1",
            start_date=datetime(2025, 9, 1),  # After completion
            field_schedules=field_schedules
        )
        
        assert previous_crop is not None
        assert previous_crop.crop_id == "tomato"
    
    def test_apply_interaction_rules_no_previous_crop(self):
        """Test applying interaction rules when there's no previous crop."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type="continuous_cultivation",
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True
            )
        ]
        
        interactor = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=None,
            crop_requirement_gateway=None,
            weather_gateway=None,
            interaction_rules=rules
        )
        
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        
        candidate = AllocationCandidate(
            field=field,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            area_used=500.0
        )
        
        field_schedules = {}
        
        updated_candidate = interactor._apply_interaction_rules(candidate, field_schedules)
        
        # No previous crop, so impact should be 1.0
        assert updated_candidate.interaction_impact == 1.0
        assert updated_candidate.previous_crop is None
    
    def test_apply_interaction_rules_continuous_cultivation_detected(self):
        """Test that continuous cultivation is detected and penalty applied."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type="continuous_cultivation",
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True,
                description="Solanaceae continuous cultivation damage"
            )
        ]
        
        interactor = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=None,
            crop_requirement_gateway=None,
            weather_gateway=None,
            interaction_rules=rules
        )
        
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        eggplant = Crop("eggplant", "Eggplant", 0.5, groups=["Solanaceae"])
        
        # Prior allocation: tomato
        prior_allocation = CropAllocation(
            allocation_id="alloc_001",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0
        )
        
        # Current candidate: eggplant (same family as tomato)
        candidate = AllocationCandidate(
            field=field,
            crop=eggplant,
            start_date=datetime(2025, 9, 1),
            completion_date=datetime(2026, 1, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            area_used=500.0
        )
        
        field_schedules = {"f1": [prior_allocation]}
        
        updated_candidate = interactor._apply_interaction_rules(candidate, field_schedules)
        
        # Continuous cultivation detected: impact = 0.7
        assert updated_candidate.interaction_impact == 0.7
        assert updated_candidate.previous_crop is not None
        assert updated_candidate.previous_crop.crop_id == "tomato"
    
    def test_apply_interaction_rules_no_continuous_cultivation(self):
        """Test that different families don't trigger continuous cultivation penalty."""
        rules = [
            InteractionRule(
                rule_id="rule_001",
                rule_type="continuous_cultivation",
                source_group="Solanaceae",
                target_group="Solanaceae",
                impact_ratio=0.7,
                is_directional=True
            )
        ]
        
        interactor = MultiFieldCropAllocationGreedyInteractor(
            field_gateway=None,
            crop_requirement_gateway=None,
            weather_gateway=None,
            interaction_rules=rules
        )
        
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        tomato = Crop("tomato", "Tomato", 0.5, groups=["Solanaceae"])
        soybean = Crop("soybean", "Soybean", 0.15, groups=["Fabaceae"])
        
        # Prior allocation: tomato (Solanaceae)
        prior_allocation = CropAllocation(
            allocation_id="alloc_001",
            field=field,
            crop=tomato,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=2000.0,
            total_cost=750000.0
        )
        
        # Current candidate: soybean (Fabaceae - different family)
        candidate = AllocationCandidate(
            field=field,
            crop=soybean,
            start_date=datetime(2025, 9, 1),
            completion_date=datetime(2026, 1, 31),
            growth_days=120,
            accumulated_gdd=1500.0,
            area_used=200.0
        )
        
        field_schedules = {"f1": [prior_allocation]}
        
        updated_candidate = interactor._apply_interaction_rules(candidate, field_schedules)
        
        # Different families, no penalty: impact = 1.0
        assert updated_candidate.interaction_impact == 1.0
        assert updated_candidate.previous_crop is not None
        assert updated_candidate.previous_crop.crop_id == "tomato"

