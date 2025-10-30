"""Tests for DP-based multi-field crop allocation algorithm."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
    AllocationCandidate,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig

@pytest.fixture
def mock_field_gateway():
    """Mock FieldGateway."""
    gateway = Mock()
    return gateway

@pytest.fixture
def mock_crop_gateway():
    """Mock CropProfileGateway."""
    gateway = Mock()
    return gateway

@pytest.fixture
def mock_weather_gateway():
    """Mock WeatherGateway."""
    gateway = Mock()
    return gateway

@pytest.fixture
def mock_crop_profile_gateway_internal():
    """Mock CropProfileGateway for internal use."""
    gateway = Mock()
    gateway.save.return_value = None
    gateway.delete.return_value = None
    return gateway

@pytest.fixture
def interactor(
    mock_field_gateway,
    mock_crop_gateway,
    mock_weather_gateway,
    mock_crop_profile_gateway_internal,
):
    """Create interactor with mocked dependencies."""
    return MultiFieldCropAllocationGreedyInteractor(
        field_gateway=mock_field_gateway,
        crop_gateway=mock_crop_gateway,
        weather_gateway=mock_weather_gateway,
        crop_profile_gateway_internal=mock_crop_profile_gateway_internal,
        config=OptimizationConfig(),
    )

class TestWeightedIntervalSchedulingDP:
    """Test weighted interval scheduling DP algorithm."""

    def test_empty_candidates(self, interactor):
        """Test DP with empty candidate list."""
        result = interactor._weighted_interval_scheduling_dp([])
        assert result == []

    def test_single_candidate(self, interactor):
        """Test DP with single candidate."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        
        candidate = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            area_used=1000.0,
        )
        
        result = interactor._weighted_interval_scheduling_dp([candidate])
        assert len(result) == 1
        assert result[0] == candidate

    def test_non_overlapping_candidates(self, interactor):
        """Test DP with non-overlapping candidates - should select all."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        
        # Two non-overlapping periods
        candidate1 = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=91,
            accumulated_gdd=1000.0,
            area_used=1000.0,
        )
        
        candidate2 = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2024, 7, 1),
            completion_date=datetime(2024, 9, 30),
            growth_days=92,
            accumulated_gdd=1100.0,
            area_used=1000.0,
        )
        
        result = interactor._weighted_interval_scheduling_dp([candidate1, candidate2])
        assert len(result) == 2
        # Both candidates should be selected
        assert candidate1 in result
        assert candidate2 in result

    def test_overlapping_candidates_select_more_profitable(self, interactor):
        """Test DP with overlapping candidates - should select more profitable one."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        
        # Two crops with different profitability
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=30000.0)
        tomato = Crop("tomato", "Tomato", 0.5, revenue_per_area=50000.0)
        
        # Overlapping periods
        rice_candidate = AllocationCandidate(
            field=field,
            crop=rice,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            area_used=1000.0,
        )
        
        tomato_candidate = AllocationCandidate(
            field=field,
            crop=tomato,
            start_date=datetime(2024, 5, 1),
            completion_date=datetime(2024, 9, 30),
            growth_days=153,
            accumulated_gdd=2000.0,
            area_used=1000.0,
        )
        
        result = interactor._weighted_interval_scheduling_dp([rice_candidate, tomato_candidate])
        
        # Should select only one (the more profitable one)
        assert len(result) == 1
        # Tomato is more profitable
        assert result[0].crop.crop_id == "tomato"

    def test_complex_overlapping_scenario(self, interactor):
        """Test DP with complex overlapping scenario."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        
        # Create a scenario where selecting optimal subset is non-trivial
        # Three candidates: A (1-5), B (2-7), C (6-10)
        # Optimal: A + C (non-overlapping, max profit)
        
        candidate_a = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 5, 31),
            growth_days=151,
            accumulated_gdd=1500.0,
            area_used=1000.0,
        )
        
        candidate_b = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2024, 2, 1),
            completion_date=datetime(2024, 7, 31),
            growth_days=181,
            accumulated_gdd=1800.0,
            area_used=1000.0,
        )
        
        candidate_c = AllocationCandidate(
            field=field,
            crop=crop,
            start_date=datetime(2024, 6, 1),
            completion_date=datetime(2024, 10, 31),
            growth_days=153,
            accumulated_gdd=1500.0,
            area_used=1000.0,
        )
        
        result = interactor._weighted_interval_scheduling_dp(
            [candidate_a, candidate_b, candidate_c]
        )
        
        # Should select A and C (non-overlapping, maximum total profit)
        assert len(result) == 2
        assert candidate_a in result
        assert candidate_c in result
        assert candidate_b not in result

class TestFindLatestNonOverlapping:
    """Test binary search for finding latest non-overlapping candidate."""

    def test_no_non_overlapping(self, interactor):
        """Test when no non-overlapping candidate exists."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25)
        
        # All candidates start before the target ends
        candidates = [
            AllocationCandidate(
                field=field,
                crop=crop,
                start_date=datetime(2024, 1, 1),
                completion_date=datetime(2024, 5, 1),
                growth_days=121,
                accumulated_gdd=1000.0,
                area_used=1000.0,
            ),
        ]
        
        # Target starts before first candidate ends
        target_index = 0
        result = interactor._find_latest_non_overlapping(candidates, target_index)
        assert result == 0  # No non-overlapping candidate

    def test_one_non_overlapping(self, interactor):
        """Test when one non-overlapping candidate exists."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25)
        
        # Sorted by completion date
        candidates = [
            AllocationCandidate(
                field=field,
                crop=crop,
                start_date=datetime(2024, 1, 1),
                completion_date=datetime(2024, 3, 31),
                growth_days=90,
                accumulated_gdd=900.0,
                area_used=1000.0,
            ),
            AllocationCandidate(
                field=field,
                crop=crop,
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 6, 30),
                growth_days=91,
                accumulated_gdd=1000.0,
                area_used=1000.0,
            ),
        ]
        
        # Second candidate doesn't overlap with first
        result = interactor._find_latest_non_overlapping(candidates, 1)
        assert result == 1  # Index 0 + 1 for dp array

    def test_multiple_non_overlapping(self, interactor):
        """Test finding the latest among multiple non-overlapping candidates."""
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25)
        
        # Multiple non-overlapping candidates before target
        candidates = [
            AllocationCandidate(
                field=field,
                crop=crop,
                start_date=datetime(2024, 1, 1),
                completion_date=datetime(2024, 2, 28),
                growth_days=59,
                accumulated_gdd=500.0,
                area_used=1000.0,
            ),
            AllocationCandidate(
                field=field,
                crop=crop,
                start_date=datetime(2024, 3, 1),
                completion_date=datetime(2024, 4, 30),
                growth_days=61,
                accumulated_gdd=600.0,
                area_used=1000.0,
            ),
            AllocationCandidate(
                field=field,
                crop=crop,
                start_date=datetime(2024, 5, 1),
                completion_date=datetime(2024, 7, 31),
                growth_days=92,
                accumulated_gdd=1000.0,
                area_used=1000.0,
            ),
        ]
        
        # Third candidate - should find second as latest non-overlapping
        result = interactor._find_latest_non_overlapping(candidates, 2)
        assert result == 2  # Index 1 + 1 for dp array

