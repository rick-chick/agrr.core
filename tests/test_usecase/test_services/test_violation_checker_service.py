"""Tests for ViolationCheckerService."""

import pytest
from datetime import date, datetime, timedelta

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.value_objects.violation_type import ViolationType
from agrr_core.entity.value_objects.rule_type import RuleType
from agrr_core.entity.entities.interaction_rule_entity import InteractionRule
from agrr_core.usecase.services.violation_checker_service import ViolationCheckerService
from agrr_core.usecase.services.interaction_rule_service import InteractionRuleService

class TestViolationCheckerService:
    """Test ViolationCheckerService."""
    
    @pytest.fixture
    def field1(self):
        """Create a sample field."""
        return Field(
            field_id="field1",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=100.0,
            fallow_period_days=28,
            location="test"
        )
    
    @pytest.fixture
    def field2(self):
        """Create another sample field."""
        return Field(
            field_id="field2",
            name="Field 2",
            area=500.0,
            daily_fixed_cost=50.0,
            fallow_period_days=14,
            location="test"
        )
    
    @pytest.fixture
    def crop_tomato(self):
        """Create a tomato crop."""
        return Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=1.0,
            groups=["Solanaceae"]
        )
    
    @pytest.fixture
    def crop_pepper(self):
        """Create a pepper crop."""
        return Crop(
            crop_id="pepper",
            name="Pepper",
            area_per_unit=1.0,
            groups=["Solanaceae"]
        )
    
    @pytest.fixture
    def crop_bean(self):
        """Create a bean crop."""
        return Crop(
            crop_id="bean",
            name="Bean",
            area_per_unit=1.0,
            groups=["Fabaceae"]
        )
    
    @pytest.fixture
    def allocation1(self, field1, crop_tomato):
        """Create a sample allocation."""
        return CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop_tomato,
            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 1),
            area_used=500.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
    
    def test_check_no_violations(self, allocation1):
        """Test checking allocation with no violations."""
        checker = ViolationCheckerService()
        violations = checker.check_violations(allocation1)
        
        assert len(violations) == 0
    
    def test_check_fallow_period_violation(self, field1, crop_tomato, crop_pepper):
        """Test checking fallow period violation."""
        # First allocation
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop_tomato,
            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 1),
            area_used=500.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        # Second allocation that violates fallow period (starts too early)
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field1,
            crop=crop_pepper,
            start_date=datetime(2024, 3, 5),  # Only 4 days after completion (need 28)
            completion_date=datetime(2024, 5, 1),
            area_used=500.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        checker = ViolationCheckerService()
        violations = checker.check_violations(
            allocation=alloc2,
            previous_allocation=alloc1
        )
        
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.FALLOW_PERIOD
        assert violations[0].severity == "error"
        assert "Fallow period violation" in violations[0].message
    
    def test_check_no_fallow_period_violation(self, field1, crop_tomato, crop_pepper):
        """Test checking no fallow period violation when period is respected."""
        # First allocation
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop_tomato,
            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 1),
            area_used=500.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        # Second allocation that respects fallow period
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field1,
            crop=crop_pepper,
            start_date=datetime(2024, 3, 30),  # 29 days after completion (need 28)
            completion_date=datetime(2024, 5, 1),
            area_used=500.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        checker = ViolationCheckerService()
        violations = checker.check_violations(
            allocation=alloc2,
            previous_allocation=alloc1
        )
        
        assert len(violations) == 0
    
    def test_check_continuous_cultivation_violation(self, field1, crop_tomato, crop_pepper):
        """Test checking continuous cultivation violation."""
        # Rule: Continuous cultivation reduces yield by 30%
        rule = InteractionRule(
            rule_id="test_rule",
            rule_type=RuleType.CONTINUOUS_CULTIVATION,
            source_group="Solanaceae",
            target_group="Solanaceae",
            impact_ratio=0.7,
            is_directional=True
        )
        
        interaction_service = InteractionRuleService(rules=[rule])
        checker = ViolationCheckerService(interaction_rule_service=interaction_service)
        
        # First allocation
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop_tomato,  # Solanaceae
            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 1),
            area_used=500.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        # Second allocation with continuous cultivation
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field1,
            crop=crop_pepper,  # Solanaceae - same family
            start_date=datetime(2024, 3, 30),
            completion_date=datetime(2024, 5, 1),
            area_used=500.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        violations = checker.check_violations(
            allocation=alloc2,
            previous_allocation=alloc1
        )
        
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.CONTINUOUS_CULTIVATION
        assert violations[0].severity == "warning"
        assert violations[0].impact_ratio == 0.7
        assert "30.0%" in violations[0].message  # (1.0 - 0.7) * 100
    
    def test_check_field_crop_incompatibility_skipped(self, field1, crop_tomato):
        """Test checking field-crop incompatibility is skipped (not yet implemented)."""
        # Field groups are not yet implemented, so this check is skipped
        # This test verifies that the check doesn't crash
        checker = ViolationCheckerService()
        
        allocation = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop_tomato,
            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 1),
            area_used=500.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        violations = checker.check_violations(allocation)
        
        # Should return no violations since field-crop check is not implemented yet
        assert len(violations) == 0
    
    def test_check_area_constraint_violation(self, field1, crop_tomato):
        """Test checking area constraint violation."""
        checker = ViolationCheckerService()
        
        allocation1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,  # area = 1000.0
            crop=crop_tomato,
            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 1),
            area_used=600.0,
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        allocation2 = CropAllocation(
            allocation_id="alloc2",
            field=field1,
            crop=crop_tomato,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 1),
            area_used=500.0,  # Total would be 1100, exceeds 1000
            growth_days=60,
            total_cost=1000.0,
            expected_revenue=2000.0,
            profit=1000.0,
            accumulated_gdd=1000.0
        )
        
        all_allocations = [allocation1, allocation2]
        violations = checker.check_violations(
            allocation=allocation2,
            all_allocations=all_allocations
        )
        
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.AREA_CONSTRAINT
        assert violations[0].severity == "error"
    
    def test_is_feasible_no_violations(self):
        """Test is_feasible with no violations."""
        checker = ViolationCheckerService()
        violations = []
        
        assert checker.is_feasible(violations) is True
    
    def test_is_feasible_warning_only(self):
        """Test is_feasible with warning-only violations."""
        from agrr_core.entity.value_objects.violation import Violation
        
        checker = ViolationCheckerService()
        violations = [
            Violation(
                violation_type=ViolationType.CONTINUOUS_CULTIVATION,
                code="TEST_001",
                message="Test warning",
                severity="warning",
                impact_ratio=0.8
            )
        ]
        
        assert checker.is_feasible(violations) is True
    
    def test_is_feasible_with_error(self):
        """Test is_feasible with error violations."""
        from agrr_core.entity.value_objects.violation import Violation
        
        checker = ViolationCheckerService()
        violations = [
            Violation(
                violation_type=ViolationType.FALLOW_PERIOD,
                code="TEST_001",
                message="Test error",
                severity="error",
                impact_ratio=1.0
            )
        ]
        
        assert checker.is_feasible(violations) is False
