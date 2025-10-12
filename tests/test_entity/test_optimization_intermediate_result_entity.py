"""Tests for OptimizationIntermediateResult entity."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)


class TestOptimizationIntermediateResult:
    """Test cases for OptimizationIntermediateResult entity."""

    def test_create_optimization_intermediate_result(self):
        """Test creating a valid OptimizationIntermediateResult entity."""
        result = OptimizationIntermediateResult(
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 7, 15),
            growth_days=106,
            accumulated_gdd=1500.0,
            field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=5000.0),
            is_optimal=True,
            base_temperature=10.0,
        )

        assert result.start_date == datetime(2024, 4, 1)
        assert result.completion_date == datetime(2024, 7, 15)
        assert result.growth_days == 106
        assert result.accumulated_gdd == 1500.0
        assert result.total_cost == 530000.0  # Calculated from field.daily_fixed_cost * growth_days
        assert result.is_optimal is True
        assert result.base_temperature == 10.0

    def test_create_incomplete_result(self):
        """Test creating a result for incomplete growth."""
        result = OptimizationIntermediateResult(
            start_date=datetime(2024, 6, 1),
            completion_date=None,
            growth_days=None,
            accumulated_gdd=800.0,
            field=None,
            is_optimal=False,
            base_temperature=10.0,
        )

        assert result.start_date == datetime(2024, 6, 1)
        assert result.completion_date is None
        assert result.growth_days is None
        assert result.accumulated_gdd == 800.0
        assert result.total_cost is None
        assert result.is_optimal is False

    def test_invalid_negative_accumulated_gdd(self):
        """Test that negative accumulated_gdd raises ValueError."""
        with pytest.raises(ValueError, match="accumulated_gdd must be non-negative"):
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=-100.0,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=5000.0),
                is_optimal=True,
                base_temperature=10.0,
            )

    def test_invalid_negative_growth_days(self):
        """Test that negative growth_days raises ValueError."""
        with pytest.raises(ValueError, match="growth_days must be non-negative"):
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=-10,
                accumulated_gdd=1500.0,
                field=None,  # Field not needed for this validation test
                is_optimal=True,
                base_temperature=10.0,
            )

    def test_total_cost_calculated_from_field(self):
        """Test that total_cost is calculated from field.daily_fixed_cost * growth_days."""
        result = OptimizationIntermediateResult(
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 7, 15),
            growth_days=106,
            accumulated_gdd=1500.0,
            field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=5000.0),
            is_optimal=True,
            base_temperature=10.0,
        )
        
        # total_cost = growth_days * daily_fixed_cost
        assert result.total_cost == 106 * 5000.0  # 530000.0

    def test_invalid_completion_date_before_start_date(self):
        """Test that completion_date before start_date raises ValueError."""
        with pytest.raises(
            ValueError, 
            match="completion_date .* must be after or equal to start_date"
        ):
            OptimizationIntermediateResult(
                start_date=datetime(2024, 7, 15),
                completion_date=datetime(2024, 4, 1),
                growth_days=106,
                accumulated_gdd=1500.0,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=5000.0),
                is_optimal=True,
                base_temperature=10.0,
            )

    def test_same_start_and_completion_date(self):
        """Test that start_date and completion_date can be the same."""
        result = OptimizationIntermediateResult(
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 4, 1),
            growth_days=1,
            accumulated_gdd=10.0,
            field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=5000.0),
            is_optimal=False,
            base_temperature=10.0,
        )

        assert result.start_date == result.completion_date
        assert result.growth_days == 1

