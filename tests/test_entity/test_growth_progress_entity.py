"""Tests for GrowthProgress entity."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.growth_progress_entity import GrowthProgress
from agrr_core.entity.entities.growth_stage_entity import GrowthStage


class TestGrowthProgress:
    """Test cases for GrowthProgress entity."""

    def test_create_growth_progress(self):
        """Test creating a valid GrowthProgress entity."""
        stage = GrowthStage(name="Vegetative", order=1)
        progress = GrowthProgress(
            date=datetime(2024, 5, 1),
            cumulative_gdd=100.0,
            total_required_gdd=1000.0,
            growth_percentage=10.0,
            current_stage=stage,
            is_complete=False,
        )

        assert progress.date == datetime(2024, 5, 1)
        assert progress.cumulative_gdd == 100.0
        assert progress.total_required_gdd == 1000.0
        assert progress.growth_percentage == 10.0
        assert progress.current_stage == stage
        assert progress.is_complete is False

    def test_growth_progress_complete(self):
        """Test growth progress at 100%."""
        stage = GrowthStage(name="Maturity", order=5)
        progress = GrowthProgress(
            date=datetime(2024, 8, 1),
            cumulative_gdd=1000.0,
            total_required_gdd=1000.0,
            growth_percentage=100.0,
            current_stage=stage,
            is_complete=True,
        )

        assert progress.growth_percentage == 100.0
        assert progress.is_complete is True

    def test_invalid_growth_percentage_below_zero(self):
        """Test that growth_percentage below 0 raises ValueError."""
        stage = GrowthStage(name="Vegetative", order=1)
        with pytest.raises(ValueError, match="growth_percentage must be between 0.0 and 100.0"):
            GrowthProgress(
                date=datetime(2024, 5, 1),
                cumulative_gdd=0.0,
                total_required_gdd=1000.0,
                growth_percentage=-1.0,
                current_stage=stage,
                is_complete=False,
            )

    def test_invalid_growth_percentage_above_100(self):
        """Test that growth_percentage above 100 raises ValueError."""
        stage = GrowthStage(name="Vegetative", order=1)
        with pytest.raises(ValueError, match="growth_percentage must be between 0.0 and 100.0"):
            GrowthProgress(
                date=datetime(2024, 5, 1),
                cumulative_gdd=1100.0,
                total_required_gdd=1000.0,
                growth_percentage=110.0,
                current_stage=stage,
                is_complete=False,
            )

    def test_invalid_negative_cumulative_gdd(self):
        """Test that negative cumulative_gdd raises ValueError."""
        stage = GrowthStage(name="Vegetative", order=1)
        with pytest.raises(ValueError, match="cumulative_gdd must be non-negative"):
            GrowthProgress(
                date=datetime(2024, 5, 1),
                cumulative_gdd=-10.0,
                total_required_gdd=1000.0,
                growth_percentage=0.0,
                current_stage=stage,
                is_complete=False,
            )

    def test_invalid_zero_total_required_gdd(self):
        """Test that zero total_required_gdd raises ValueError."""
        stage = GrowthStage(name="Vegetative", order=1)
        with pytest.raises(ValueError, match="total_required_gdd must be positive"):
            GrowthProgress(
                date=datetime(2024, 5, 1),
                cumulative_gdd=0.0,
                total_required_gdd=0.0,
                growth_percentage=0.0,
                current_stage=stage,
                is_complete=False,
            )

    def test_invalid_negative_total_required_gdd(self):
        """Test that negative total_required_gdd raises ValueError."""
        stage = GrowthStage(name="Vegetative", order=1)
        with pytest.raises(ValueError, match="total_required_gdd must be positive"):
            GrowthProgress(
                date=datetime(2024, 5, 1),
                cumulative_gdd=0.0,
                total_required_gdd=-1000.0,
                growth_percentage=0.0,
                current_stage=stage,
                is_complete=False,
            )

