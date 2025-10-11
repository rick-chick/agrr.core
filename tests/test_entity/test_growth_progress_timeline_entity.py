"""Tests for GrowthProgressTimeline entity."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.growth_progress_entity import GrowthProgress
from agrr_core.entity.entities.growth_progress_timeline_entity import GrowthProgressTimeline
from agrr_core.entity.entities.growth_stage_entity import GrowthStage


class TestGrowthProgressTimeline:
    """Test cases for GrowthProgressTimeline entity."""

    def test_create_timeline(self):
        """Test creating a valid GrowthProgressTimeline."""
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        stage = GrowthStage(name="Vegetative", order=1)
        
        progress1 = GrowthProgress(
            date=datetime(2024, 5, 1),
            cumulative_gdd=50.0,
            total_required_gdd=1000.0,
            growth_percentage=5.0,
            current_stage=stage,
            is_complete=False,
        )
        progress2 = GrowthProgress(
            date=datetime(2024, 5, 2),
            cumulative_gdd=100.0,
            total_required_gdd=1000.0,
            growth_percentage=10.0,
            current_stage=stage,
            is_complete=False,
        )

        timeline = GrowthProgressTimeline(
            crop=crop,
            start_date=datetime(2024, 5, 1),
            progress_list=[progress1, progress2],
        )

        assert timeline.crop == crop
        assert timeline.start_date == datetime(2024, 5, 1)
        assert len(timeline.progress_list) == 2
        assert timeline.progress_list[0] == progress1
        assert timeline.progress_list[1] == progress2

    def test_get_final_progress(self):
        """Test getting the final progress record."""
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
        stage = GrowthStage(name="Maturity", order=5)
        
        progress_final = GrowthProgress(
            date=datetime(2024, 8, 1),
            cumulative_gdd=1000.0,
            total_required_gdd=1000.0,
            growth_percentage=100.0,
            current_stage=stage,
            is_complete=True,
        )

        timeline = GrowthProgressTimeline(
            crop=crop,
            start_date=datetime(2024, 5, 1),
            progress_list=[progress_final],
        )

        final = timeline.get_final_progress()
        assert final == progress_final
        assert final.growth_percentage == 100.0

    def test_is_harvest_ready_true(self):
        """Test is_harvest_ready returns True when complete."""
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
        stage = GrowthStage(name="Maturity", order=5)
        
        progress = GrowthProgress(
            date=datetime(2024, 8, 1),
            cumulative_gdd=1000.0,
            total_required_gdd=1000.0,
            growth_percentage=100.0,
            current_stage=stage,
            is_complete=True,
        )

        timeline = GrowthProgressTimeline(
            crop=crop,
            start_date=datetime(2024, 5, 1),
            progress_list=[progress],
        )

        assert timeline.is_harvest_ready() is True

    def test_is_harvest_ready_false(self):
        """Test is_harvest_ready returns False when not complete."""
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
        stage = GrowthStage(name="Vegetative", order=1)
        
        progress = GrowthProgress(
            date=datetime(2024, 5, 1),
            cumulative_gdd=100.0,
            total_required_gdd=1000.0,
            growth_percentage=10.0,
            current_stage=stage,
            is_complete=False,
        )

        timeline = GrowthProgressTimeline(
            crop=crop,
            start_date=datetime(2024, 5, 1),
            progress_list=[progress],
        )

        assert timeline.is_harvest_ready() is False

    def test_get_final_progress_empty_list(self):
        """Test get_final_progress raises ValueError when list is empty."""
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
        timeline = GrowthProgressTimeline(
            crop=crop,
            start_date=datetime(2024, 5, 1),
            progress_list=[],
        )

        with pytest.raises(ValueError, match="progress_list is empty"):
            timeline.get_final_progress()

    def test_is_harvest_ready_empty_list(self):
        """Test is_harvest_ready returns False when list is empty."""
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
        timeline = GrowthProgressTimeline(
            crop=crop,
            start_date=datetime(2024, 5, 1),
            progress_list=[],
        )

        assert timeline.is_harvest_ready() is False

