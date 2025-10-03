"""Tests for weather data entities."""

import pytest
from datetime import datetime

from agrr_core.entity import WeatherData, Location, DateRange, Forecast
from agrr_core.entity.exceptions.weather_exceptions import (
    InvalidLocationError,
    InvalidDateRangeError,
)


class TestWeatherData:
    """Test WeatherData entity."""
    
    def test_weather_data_creation(self):
        """Test creating WeatherData entity."""
        time = datetime(2023, 1, 1)
        weather_data = WeatherData(
            time=time,
            temperature_2m_max=25.0,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=5.0,
            sunshine_duration=28800.0  # 8 hours in seconds
        )
        
        assert weather_data.time == time
        assert weather_data.temperature_2m_max == 25.0
        assert weather_data.temperature_2m_min == 15.0
        assert weather_data.temperature_2m_mean == 20.0
        assert weather_data.precipitation_sum == 5.0
        assert weather_data.sunshine_duration == 28800.0
    
    def test_sunshine_hours_property(self):
        """Test sunshine_hours computed property."""
        weather_data = WeatherData(
            time=datetime(2023, 1, 1),
            sunshine_duration=28800.0  # 8 hours in seconds
        )
        
        assert weather_data.sunshine_hours == 8.0
    
    def test_sunshine_hours_none(self):
        """Test sunshine_hours when sunshine_duration is None."""
        weather_data = WeatherData(
            time=datetime(2023, 1, 1),
            sunshine_duration=None
        )
        
        assert weather_data.sunshine_hours is None
    
    def test_optional_fields(self):
        """Test creating WeatherData with only required fields."""
        time = datetime(2023, 1, 1)
        weather_data = WeatherData(time=time)
        
        assert weather_data.time == time
        assert weather_data.temperature_2m_max is None
        assert weather_data.temperature_2m_min is None
        assert weather_data.temperature_2m_mean is None
        assert weather_data.precipitation_sum is None
        assert weather_data.sunshine_duration is None


class TestLocation:
    """Test Location entity."""
    
    def test_valid_location(self):
        """Test creating valid Location."""
        location = Location(latitude=35.7, longitude=139.7)
        
        assert location.latitude == 35.7
        assert location.longitude == 139.7
    
    def test_invalid_latitude_too_high(self):
        """Test invalid latitude (too high)."""
        with pytest.raises(InvalidLocationError):
            Location(latitude=91.0, longitude=139.7)
    
    def test_invalid_latitude_too_low(self):
        """Test invalid latitude (too low)."""
        with pytest.raises(InvalidLocationError):
            Location(latitude=-91.0, longitude=139.7)
    
    def test_invalid_longitude_too_high(self):
        """Test invalid longitude (too high)."""
        with pytest.raises(InvalidLocationError):
            Location(latitude=35.7, longitude=181.0)
    
    def test_invalid_longitude_too_low(self):
        """Test invalid longitude (too low)."""
        with pytest.raises(InvalidLocationError):
            Location(latitude=35.7, longitude=-181.0)
    
    def test_boundary_values(self):
        """Test boundary values."""
        # Valid boundary values
        Location(latitude=90.0, longitude=180.0)
        Location(latitude=-90.0, longitude=-180.0)


class TestDateRange:
    """Test DateRange entity."""
    
    def test_valid_date_range(self):
        """Test creating valid DateRange."""
        date_range = DateRange(start_date="2023-01-01", end_date="2023-12-31")
        
        assert date_range.start_date == "2023-01-01"
        assert date_range.end_date == "2023-12-31"
    
    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(InvalidDateRangeError):
            DateRange(start_date="2023/01/01", end_date="2023-12-31")
    
    def test_invalid_date_format_end(self):
        """Test invalid end date format."""
        with pytest.raises(InvalidDateRangeError):
            DateRange(start_date="2023-01-01", end_date="2023/12/31")
    
    def test_invalid_date_string(self):
        """Test invalid date string."""
        with pytest.raises(InvalidDateRangeError):
            DateRange(start_date="invalid-date", end_date="2023-12-31")


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
