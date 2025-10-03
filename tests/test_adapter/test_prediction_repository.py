"""Tests for prediction repository."""

import pytest
from datetime import datetime

from agrr_core.adapter.repositories.prediction_repository import InMemoryPredictionRepository
from agrr_core.entity import Forecast


class TestInMemoryPredictionRepository:
    """Test InMemoryPredictionRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.repository = InMemoryPredictionRepository()
    
    @pytest.mark.asyncio
    async def test_save_and_get_forecast(self):
        """Test saving and retrieving forecast data."""
        # Create test forecast data
        forecasts = [
            Forecast(
                date=datetime(2024, 1, 1),
                predicted_value=20.5,
                confidence_lower=18.0,
                confidence_upper=23.0
            ),
            Forecast(
                date=datetime(2024, 1, 2),
                predicted_value=21.0,
                confidence_lower=19.0,
                confidence_upper=24.0
            ),
            Forecast(
                date=datetime(2024, 1, 15),  # Outside date range
                predicted_value=22.0,
                confidence_lower=20.0,
                confidence_upper=25.0
            ),
        ]
        
        # Save forecast data
        await self.repository.save_forecast(forecasts)
        
        # Retrieve forecast data within date range
        result = await self.repository.get_forecast_by_date_range(
            "2024-01-01", "2024-01-10"
        )
        
        # Should return only forecasts within date range
        assert len(result) == 2
        assert result[0].date == datetime(2024, 1, 1)
        assert result[0].predicted_value == 20.5
        assert result[0].confidence_lower == 18.0
        assert result[0].confidence_upper == 23.0
        
        assert result[1].date == datetime(2024, 1, 2)
        assert result[1].predicted_value == 21.0
    
    @pytest.mark.asyncio
    async def test_empty_repository(self):
        """Test retrieving from empty repository."""
        result = await self.repository.get_forecast_by_date_range(
            "2024-01-01", "2024-01-01"
        )
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_clear_repository(self):
        """Test clearing repository."""
        # Add some forecast data
        forecasts = [
            Forecast(
                date=datetime(2024, 1, 1),
                predicted_value=20.5,
                confidence_lower=18.0,
                confidence_upper=23.0
            )
        ]
        await self.repository.save_forecast(forecasts)
        
        # Clear repository
        self.repository.clear()
        
        # Verify it's empty
        result = await self.repository.get_forecast_by_date_range(
            "2024-01-01", "2024-01-01"
        )
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_date_range_filtering(self):
        """Test date range filtering."""
        # Create forecast data spanning multiple months
        forecasts = []
        for day in range(1, 32):  # January has 31 days
            forecasts.append(
                Forecast(
                    date=datetime(2024, 1, day),
                    predicted_value=20.0 + day * 0.1,
                    confidence_lower=18.0 + day * 0.1,
                    confidence_upper=23.0 + day * 0.1
                )
            )
        
        await self.repository.save_forecast(forecasts)
        
        # Test specific date range
        result = await self.repository.get_forecast_by_date_range(
            "2024-01-10", "2024-01-20"
        )
        
        # Should return 11 days (10th to 20th inclusive)
        assert len(result) == 11
        assert result[0].date == datetime(2024, 1, 10)
        assert result[-1].date == datetime(2024, 1, 20)
    
    @pytest.mark.asyncio
    async def test_forecast_without_confidence(self):
        """Test saving forecasts without confidence intervals."""
        forecasts = [
            Forecast(
                date=datetime(2024, 1, 1),
                predicted_value=20.5
            ),
            Forecast(
                date=datetime(2024, 1, 2),
                predicted_value=21.0
            ),
        ]
        
        await self.repository.save_forecast(forecasts)
        
        result = await self.repository.get_forecast_by_date_range(
            "2024-01-01", "2024-01-02"
        )
        
        assert len(result) == 2
        assert result[0].predicted_value == 20.5
        assert result[0].confidence_lower is None
        assert result[0].confidence_upper is None
        
        assert result[1].predicted_value == 21.0
        assert result[1].confidence_lower is None
        assert result[1].confidence_upper is None
    
    @pytest.mark.asyncio
    async def test_multiple_save_operations(self):
        """Test multiple save operations."""
        # First batch
        forecasts1 = [
            Forecast(
                date=datetime(2024, 1, 1),
                predicted_value=20.5
            )
        ]
        
        # Second batch
        forecasts2 = [
            Forecast(
                date=datetime(2024, 1, 2),
                predicted_value=21.0
            ),
            Forecast(
                date=datetime(2024, 1, 3),
                predicted_value=21.5
            ),
        ]
        
        # Save both batches
        await self.repository.save_forecast(forecasts1)
        await self.repository.save_forecast(forecasts2)
        
        # Retrieve all forecasts
        result = await self.repository.get_forecast_by_date_range(
            "2024-01-01", "2024-01-03"
        )
        
        assert len(result) == 3
        assert result[0].predicted_value == 20.5
        assert result[1].predicted_value == 21.0
        assert result[2].predicted_value == 21.5
