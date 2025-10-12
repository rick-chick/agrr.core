"""Test for optimization schedule entity.

Tests the OptimizationSchedule entity validation and invariants.
"""

import pytest
from datetime import datetime

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)
from agrr_core.entity.entities.field_entity import Field


class TestOptimizationSchedule:
    """Test suite for OptimizationSchedule entity."""

    def test_valid_schedule(self):
        """Test creating a valid schedule."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=80.0)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field1,
                is_optimal=False,
                base_temperature=10.0,
            ),
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 11),
                completion_date=datetime(2025, 1, 20),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        schedule = OptimizationSchedule(
            schedule_id="test_001",
            selected_results=results,
            total_cost=1800.0
        )
        
        assert schedule.schedule_id == "test_001"
        assert len(schedule.selected_results) == 2
        assert schedule.total_cost == 1800.0
        assert schedule.period_count == 2

    def test_empty_schedule_id_raises_error(self):
        """Test that empty schedule_id raises ValueError."""
        field = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        with pytest.raises(ValueError, match="schedule_id must not be empty"):
            OptimizationSchedule(
                schedule_id="",
                selected_results=results,
                total_cost=1000.0
            )

    def test_negative_cost_raises_error(self):
        """Test that negative total_cost raises ValueError."""
        field = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        with pytest.raises(ValueError, match="total_cost must be non-negative"):
            OptimizationSchedule(
                schedule_id="test_001",
                selected_results=results,
                total_cost=-100.0
            )

    def test_overlapping_results_raises_error(self):
        """Test that overlapping results raise ValueError."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=66.67)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=72.73)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 15),
                growth_days=15,
                accumulated_gdd=100.0,
                field=field1,
                is_optimal=False,
                base_temperature=10.0,
            ),
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 10),  # Overlaps with first result
                completion_date=datetime(2025, 1, 20),
                growth_days=11,
                accumulated_gdd=100.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        with pytest.raises(ValueError, match="Results overlap"):
            OptimizationSchedule(
                schedule_id="test_001",
                selected_results=results,
                total_cost=1800.0
            )

    def test_boundary_non_overlapping_is_valid(self):
        """Test that results touching at boundary are valid (non-overlapping)."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=72.73)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field1,
                is_optimal=False,
                base_temperature=10.0,
            ),
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 10),  # Same day as completion
                completion_date=datetime(2025, 1, 20),
                growth_days=11,
                accumulated_gdd=100.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        schedule = OptimizationSchedule(
            schedule_id="test_001",
            selected_results=results,
            total_cost=1800.0
        )
        
        assert schedule.period_count == 2

    def test_incomplete_result_raises_error(self):
        """Test that results with None completion_date raise ValueError."""
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=None,  # Incomplete
                growth_days=None,
                accumulated_gdd=50.0,
                field=None,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        with pytest.raises(ValueError, match="has no completion_date"):
            OptimizationSchedule(
                schedule_id="test_001",
                selected_results=results,
                total_cost=0.0
            )

    def test_single_result_schedule(self):
        """Test schedule with single result."""
        field = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        schedule = OptimizationSchedule(
            schedule_id="test_001",
            selected_results=results,
            total_cost=1000.0
        )
        
        assert schedule.period_count == 1

    def test_empty_results_list(self):
        """Test schedule with empty results list."""
        schedule = OptimizationSchedule(
            schedule_id="test_001",
            selected_results=[],
            total_cost=0.0
        )
        
        assert schedule.period_count == 0

    def test_immutability(self):
        """Test that OptimizationSchedule is immutable (frozen)."""
        field = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        schedule = OptimizationSchedule(
            schedule_id="test_001",
            selected_results=results,
            total_cost=1000.0
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            schedule.total_cost = 2000.0
