"""Tests for WeatherLinearInterpolator."""

import pytest
import numpy as np
from datetime import datetime, date, timedelta

from agrr_core.adapter.services.weather_linear_interpolator import WeatherLinearInterpolator
from agrr_core.entity.entities.weather_entity import WeatherData

class TestWeatherLinearInterpolator:
    """Test cases for WeatherLinearInterpolator."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.interpolator = WeatherLinearInterpolator()
    
    def test_interpolate_missing_middle_value(self):
        """Test interpolation for missing value in the middle."""
        # Arrange: Create weather data with one missing value
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),  # Missing temperature
            date(2025, 1, 3),
        ]
        weather_by_date = {
            dates[0]: WeatherData(time=datetime(2025, 1, 1), temperature_2m_mean=10.0),
            dates[1]: WeatherData(time=datetime(2025, 1, 2), temperature_2m_mean=None),
            dates[2]: WeatherData(time=datetime(2025, 1, 3), temperature_2m_mean=20.0),
        }
        
        # Act
        result = self.interpolator.interpolate_temperature(weather_by_date, dates)
        
        # Assert: Should be linear interpolation (10 + 20) / 2 = 15
        assert result[dates[1]].temperature_2m_mean == 15.0
        assert result[dates[0]].temperature_2m_mean == 10.0
        assert result[dates[2]].temperature_2m_mean == 20.0
    
    def test_interpolate_missing_beginning_value(self):
        """Test forward fill for missing value at beginning."""
        # Arrange
        dates = [
            date(2025, 1, 1),  # Missing
            date(2025, 1, 2),
            date(2025, 1, 3),
        ]
        weather_by_date = {
            dates[0]: WeatherData(time=datetime(2025, 1, 1), temperature_2m_mean=None),
            dates[1]: WeatherData(time=datetime(2025, 1, 2), temperature_2m_mean=15.0),
            dates[2]: WeatherData(time=datetime(2025, 1, 3), temperature_2m_mean=20.0),
        }
        
        # Act
        result = self.interpolator.interpolate_temperature(weather_by_date, dates)
        
        # Assert: Should use first valid value (forward fill)
        assert result[dates[0]].temperature_2m_mean == 15.0
        assert result[dates[1]].temperature_2m_mean == 15.0
        assert result[dates[2]].temperature_2m_mean == 20.0
    
    def test_interpolate_missing_end_value(self):
        """Test backward fill for missing value at end."""
        # Arrange
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),
            date(2025, 1, 3),  # Missing
        ]
        weather_by_date = {
            dates[0]: WeatherData(time=datetime(2025, 1, 1), temperature_2m_mean=10.0),
            dates[1]: WeatherData(time=datetime(2025, 1, 2), temperature_2m_mean=15.0),
            dates[2]: WeatherData(time=datetime(2025, 1, 3), temperature_2m_mean=None),
        }
        
        # Act
        result = self.interpolator.interpolate_temperature(weather_by_date, dates)
        
        # Assert: Should use last valid value (backward fill)
        assert result[dates[0]].temperature_2m_mean == 10.0
        assert result[dates[1]].temperature_2m_mean == 15.0
        assert result[dates[2]].temperature_2m_mean == 15.0
    
    def test_interpolate_multiple_missing_values(self):
        """Test interpolation for multiple consecutive missing values."""
        # Arrange
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),  # Missing
            date(2025, 1, 3),  # Missing
            date(2025, 1, 4),  # Missing
            date(2025, 1, 5),
        ]
        weather_by_date = {
            dates[0]: WeatherData(time=datetime(2025, 1, 1), temperature_2m_mean=10.0),
            dates[1]: WeatherData(time=datetime(2025, 1, 2), temperature_2m_mean=None),
            dates[2]: WeatherData(time=datetime(2025, 1, 3), temperature_2m_mean=None),
            dates[3]: WeatherData(time=datetime(2025, 1, 4), temperature_2m_mean=None),
            dates[4]: WeatherData(time=datetime(2025, 1, 5), temperature_2m_mean=30.0),
        }
        
        # Act
        result = self.interpolator.interpolate_temperature(weather_by_date, dates)
        
        # Assert: Should be linear interpolation
        # Day 1: 10.0
        # Day 2: 10.0 + (30.0 - 10.0) * 1/4 = 15.0
        # Day 3: 10.0 + (30.0 - 10.0) * 2/4 = 20.0
        # Day 4: 10.0 + (30.0 - 10.0) * 3/4 = 25.0
        # Day 5: 30.0
        assert result[dates[0]].temperature_2m_mean == 10.0
        assert result[dates[1]].temperature_2m_mean == 15.0
        assert result[dates[2]].temperature_2m_mean == 20.0
        assert result[dates[3]].temperature_2m_mean == 25.0
        assert result[dates[4]].temperature_2m_mean == 30.0
    
    def test_interpolate_missing_date(self):
        """Test creating data for completely missing date."""
        # Arrange: Date gap in the sequence
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),  # Not in weather_by_date
            date(2025, 1, 3),
        ]
        weather_by_date = {
            dates[0]: WeatherData(time=datetime(2025, 1, 1), temperature_2m_mean=10.0),
            # dates[1] is missing completely
            dates[2]: WeatherData(time=datetime(2025, 1, 3), temperature_2m_mean=20.0),
        }
        
        # Act
        result = self.interpolator.interpolate_temperature(weather_by_date, dates)
        
        # Assert: Should create new data with interpolated temperature
        assert dates[1] in result
        assert result[dates[1]].temperature_2m_mean == 15.0
    
    def test_interpolate_no_missing_values(self):
        """Test that data without missing values is returned unchanged."""
        # Arrange: All values present
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),
            date(2025, 1, 3),
        ]
        weather_by_date = {
            dates[0]: WeatherData(time=datetime(2025, 1, 1), temperature_2m_mean=10.0),
            dates[1]: WeatherData(time=datetime(2025, 1, 2), temperature_2m_mean=15.0),
            dates[2]: WeatherData(time=datetime(2025, 1, 3), temperature_2m_mean=20.0),
        }
        
        # Act
        result = self.interpolator.interpolate_temperature(weather_by_date, dates)
        
        # Assert: Should be unchanged
        assert result[dates[0]].temperature_2m_mean == 10.0
        assert result[dates[1]].temperature_2m_mean == 15.0
        assert result[dates[2]].temperature_2m_mean == 20.0
    
    def test_interpolate_all_missing_raises_error(self):
        """Test that all missing values raises error."""
        # Arrange: All values missing
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),
            date(2025, 1, 3),
        ]
        weather_by_date = {
            dates[0]: WeatherData(time=datetime(2025, 1, 1), temperature_2m_mean=None),
            dates[1]: WeatherData(time=datetime(2025, 1, 2), temperature_2m_mean=None),
            dates[2]: WeatherData(time=datetime(2025, 1, 3), temperature_2m_mean=None),
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="All values are missing"):
            self.interpolator.interpolate_temperature(weather_by_date, dates)
    
    def test_interpolate_preserves_other_fields(self):
        """Test that interpolation preserves other weather fields."""
        # Arrange
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),  # Missing temperature
            date(2025, 1, 3),
        ]
        weather_by_date = {
            dates[0]: WeatherData(
                time=datetime(2025, 1, 1),
                temperature_2m_mean=10.0,
                precipitation_sum=5.0,
                sunshine_duration=3600.0,
            ),
            dates[1]: WeatherData(
                time=datetime(2025, 1, 2),
                temperature_2m_mean=None,
                precipitation_sum=10.0,
                sunshine_duration=7200.0,
            ),
            dates[2]: WeatherData(
                time=datetime(2025, 1, 3),
                temperature_2m_mean=20.0,
                precipitation_sum=2.0,
                sunshine_duration=1800.0,
            ),
        }
        
        # Act
        result = self.interpolator.interpolate_temperature(weather_by_date, dates)
        
        # Assert: Other fields should be preserved
        assert result[dates[1]].temperature_2m_mean == 15.0
        assert result[dates[1]].precipitation_sum == 10.0
        assert result[dates[1]].sunshine_duration == 7200.0
    
    def test_interpolate_does_not_modify_original(self):
        """Test that interpolation does not modify original data."""
        # Arrange
        dates = [
            date(2025, 1, 1),
            date(2025, 1, 2),
            date(2025, 1, 3),
        ]
        weather_by_date = {
            dates[0]: WeatherData(time=datetime(2025, 1, 1), temperature_2m_mean=10.0),
            dates[1]: WeatherData(time=datetime(2025, 1, 2), temperature_2m_mean=None),
            dates[2]: WeatherData(time=datetime(2025, 1, 3), temperature_2m_mean=20.0),
        }
        
        # Act
        result = self.interpolator.interpolate_temperature(weather_by_date, dates)
        
        # Assert: Original should be unchanged
        assert weather_by_date[dates[1]].temperature_2m_mean is None
        assert result[dates[1]].temperature_2m_mean == 15.0

