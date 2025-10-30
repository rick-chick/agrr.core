"""Tests for growth period optimize response DTO."""

import pytest
from datetime import datetime

from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    CandidateResultDTO,
    OptimalGrowthPeriodResponseDTO,
)
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop

class TestCandidateResultDTO:
    """Tests for CandidateResultDTO."""
    
    def test_get_metrics_with_crop_calculates_revenue_and_profit(self):
        """Test that get_metrics() calculates revenue and profit when crop is provided."""
        # Arrange
        field = Field(
            field_id="test_field",
            name="Test Field",
            area=100.0,
            daily_fixed_cost=1000.0,
            location="Test Location"
        )
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            variety=None,
            area_per_unit=0.2,
            revenue_per_area=1500.0,
            max_revenue=None,
            groups=["Solanaceae"]
        )
        candidate = CandidateResultDTO(
            start_date=datetime(2023, 6, 5),
            completion_date=datetime(2023, 9, 29),
            growth_days=117,
            field=field,
            crop=crop,
            is_optimal=False,
            yield_factor=1.0
        )
        
        # Act
        metrics = candidate.get_metrics()
        
        # Assert
        assert metrics.growth_days == 117
        assert metrics.daily_fixed_cost == 1000.0
        assert metrics.area_used == 100.0  # field area
        assert metrics.revenue_per_area == 1500.0
        assert metrics.cost == 117000.0  # 117 days * 1000
        assert metrics.revenue == 150000.0  # 100 m² * 1500
        assert metrics.profit == 33000.0  # 150000 - 117000
    
    def test_get_metrics_without_crop_returns_negative_cost_as_profit(self):
        """Test that get_metrics() returns -cost as profit when crop is not provided."""
        # Arrange
        field = Field(
            field_id="test_field",
            name="Test Field",
            area=100.0,
            daily_fixed_cost=1000.0,
            location="Test Location"
        )
        candidate = CandidateResultDTO(
            start_date=datetime(2023, 6, 5),
            completion_date=datetime(2023, 9, 29),
            growth_days=117,
            field=field,
            crop=None,  # No crop
            is_optimal=False,
            yield_factor=1.0
        )
        
        # Act
        metrics = candidate.get_metrics()
        
        # Assert
        assert metrics.cost == 117000.0
        assert metrics.revenue is None
        assert metrics.profit == -117000.0  # -cost when revenue is None
    
    def test_get_metrics_with_yield_factor_reduces_revenue(self):
        """Test that yield_factor reduces revenue proportionally."""
        # Arrange
        field = Field(
            field_id="test_field",
            name="Test Field",
            area=100.0,
            daily_fixed_cost=1000.0,
            location="Test Location"
        )
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            variety=None,
            area_per_unit=0.2,
            revenue_per_area=1500.0,
            max_revenue=None,
            groups=["Solanaceae"]
        )
        candidate = CandidateResultDTO(
            start_date=datetime(2023, 6, 5),
            completion_date=datetime(2023, 9, 29),
            growth_days=117,
            field=field,
            crop=crop,
            is_optimal=False,
            yield_factor=0.8  # 20% yield loss due to temperature stress
        )
        
        # Act
        metrics = candidate.get_metrics()
        
        # Assert
        assert metrics.yield_factor == 0.8
        assert metrics.revenue == 120000.0  # 150000 * 0.8
        assert metrics.profit == 3000.0  # 120000 - 117000
    
    def test_to_dict_includes_revenue_and_profit(self):
        """Test that to_dict() includes revenue and profit."""
        # Arrange
        field = Field(
            field_id="test_field",
            name="Test Field",
            area=100.0,
            daily_fixed_cost=1000.0,
            location="Test Location"
        )
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            variety=None,
            area_per_unit=0.2,
            revenue_per_area=1500.0,
            max_revenue=None,
            groups=["Solanaceae"]
        )
        candidate = CandidateResultDTO(
            start_date=datetime(2023, 6, 5),
            completion_date=datetime(2023, 9, 29),
            growth_days=117,
            field=field,
            crop=crop,
            is_optimal=True,
            yield_factor=1.0
        )
        
        # Act
        result = candidate.to_dict()
        
        # Assert
        assert result["revenue"] == 150000.0
        assert result["profit"] == 33000.0
        assert result["total_cost"] == 117000.0
        assert result["is_optimal"] is True
        assert result["yield_factor"] == 1.0
        assert result["yield_loss_percentage"] == 0.0

class TestOptimalGrowthPeriodResponseDTO:
    """Tests for OptimalGrowthPeriodResponseDTO."""
    
    def test_to_dict_includes_revenue_and_profit(self):
        """Test that to_dict() includes revenue and profit."""
        # Arrange
        field = Field(
            field_id="test_field",
            name="Test Field",
            area=100.0,
            daily_fixed_cost=1000.0,
            location="Test Location"
        )
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            variety=None,
            area_per_unit=0.2,
            revenue_per_area=1500.0,
            max_revenue=None,
            groups=["Solanaceae"]
        )
        candidate = CandidateResultDTO(
            start_date=datetime(2023, 6, 5),
            completion_date=datetime(2023, 9, 29),
            growth_days=117,
            field=field,
            crop=crop,
            is_optimal=True,
            yield_factor=1.0
        )
        
        response = OptimalGrowthPeriodResponseDTO(
            crop_name="Tomato",
            variety=None,
            optimal_start_date=datetime(2023, 6, 5),
            completion_date=datetime(2023, 9, 29),
            growth_days=117,
            total_cost=117000.0,
            revenue=150000.0,
            profit=33000.0,
            daily_fixed_cost=1000.0,
            field=field,
            candidates=[candidate]
        )
        
        # Act
        result = response.to_dict()
        
        # Assert
        assert result["crop_name"] == "Tomato"
        assert result["growth_days"] == 117
        assert result["total_cost"] == 117000.0
        assert result["revenue"] == 150000.0
        assert result["profit"] == 33000.0
        assert result["daily_fixed_cost"] == 1000.0
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["revenue"] == 150000.0
        assert result["candidates"][0]["profit"] == 33000.0

