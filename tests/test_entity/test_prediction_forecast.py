"""Tests for Forecast entity."""

import pytest
from datetime import datetime

from agrr_core.entity import Forecast

class TestForecast:
    """Test Forecast entity."""
    
    def test_forecast_creation(self):
        """Test creating Forecast entity."""
        date = datetime(2024, 1, 1)
        forecast = Forecast(
            date=date,
            predicted_value=20.5,
            confidence_lower=18.0,
            confidence_upper=23.0
        )
        
        assert forecast.date == date
        assert forecast.predicted_value == 20.5
        assert forecast.confidence_lower == 18.0
        assert forecast.confidence_upper == 23.0
    
    def test_forecast_without_confidence(self):
        """Test creating Forecast without confidence intervals."""
        date = datetime(2024, 1, 1)
        forecast = Forecast(date=date, predicted_value=20.5)
        
        assert forecast.date == date
        assert forecast.predicted_value == 20.5
        assert forecast.confidence_lower is None
        assert forecast.confidence_upper is None
