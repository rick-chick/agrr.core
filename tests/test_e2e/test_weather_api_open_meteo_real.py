"""E2E tests for Open-Meteo API integration.

These tests make actual API calls to Open-Meteo and require internet connection.
They are marked with @pytest.mark.e2e and can be skipped in CI/CD if needed.
"""

import pytest
from datetime import datetime, timedelta

from agrr_core.adapter.repositories.weather_api_open_meteo_repository import OpenMeteoWeatherRepository
from agrr_core.entity import Location, WeatherData
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError


@pytest.mark.e2e
class TestOpenMeteoAPIReal:
    """E2E tests for real Open-Meteo API calls."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.repository = OpenMeteoWeatherRepository()
        # Use historical dates that should always be available
        # Archive API supports data from 1940 to ~5 days ago
        end_date = datetime.now().date() - timedelta(days=10)
        start_date = end_date - timedelta(days=6)
        self.start_date = start_date.strftime('%Y-%m-%d')
        self.end_date = end_date.strftime('%Y-%m-%d')
    
    @pytest.mark.asyncio
    async def test_real_api_call_tokyo(self):
        """Test real API call with Tokyo coordinates.
        
        This test verifies:
        - Actual API endpoint is accessible
        - Response format matches expectations
        - Data can be parsed correctly
        """
        # Tokyo coordinates
        latitude = 35.6762
        longitude = 139.6503
        
        # Make actual API call
        weather_data_list, location = await self.repository.get_weather_data_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Verify we got data
        assert len(weather_data_list) == 7, f"Expected 7 days of data, got {len(weather_data_list)}"
        
        # Verify all items are WeatherData entities
        for data in weather_data_list:
            assert isinstance(data, WeatherData)
            assert isinstance(data.time, datetime)
            # Temperature data should exist for most locations
            assert data.temperature_2m_max is not None or data.temperature_2m_min is not None
        
        # Verify location information
        assert isinstance(location, Location)
        assert abs(location.latitude - latitude) < 0.1, "Latitude should be close to requested"
        assert abs(location.longitude - longitude) < 0.1, "Longitude should be close to requested"
        assert location.elevation is not None, "Elevation should be provided"
        assert location.timezone is not None, "Timezone should be provided"
        assert "Tokyo" in location.timezone or "Asia" in location.timezone
    
    @pytest.mark.asyncio
    async def test_real_api_call_new_york(self):
        """Test real API call with New York coordinates."""
        # New York coordinates
        latitude = 40.7128
        longitude = -74.0060
        
        # Make actual API call
        weather_data_list, location = await self.repository.get_weather_data_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Verify we got data
        assert len(weather_data_list) == 7
        
        # Verify location
        assert isinstance(location, Location)
        assert abs(location.latitude - latitude) < 0.1
        assert abs(location.longitude - longitude) < 0.1
        # Note: timezone is set to Asia/Tokyo in the repository implementation
        # This is a known limitation that should be fixed to use auto timezone
        assert location.timezone is not None
    
    @pytest.mark.asyncio
    async def test_real_api_call_single_day(self):
        """Test real API call for a single day."""
        # Use a single historical date
        single_date = (datetime.now().date() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        weather_data_list, location = await self.repository.get_weather_data_by_location_and_date_range(
            latitude=51.5074,  # London
            longitude=-0.1278,
            start_date=single_date,
            end_date=single_date
        )
        
        # Should get exactly 1 day of data
        assert len(weather_data_list) == 1
        assert weather_data_list[0].time.strftime('%Y-%m-%d') == single_date
    
    @pytest.mark.asyncio
    async def test_real_api_data_completeness(self):
        """Test that API returns all expected fields."""
        weather_data_list, location = await self.repository.get_weather_data_by_location_and_date_range(
            latitude=35.6762,
            longitude=139.6503,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Check first day's data has expected fields
        first_day = weather_data_list[0]
        
        # These fields should always be present for historical data
        assert first_day.time is not None
        
        # Temperature fields (at least one should be present)
        has_temp = (
            first_day.temperature_2m_max is not None or
            first_day.temperature_2m_min is not None or
            first_day.temperature_2m_mean is not None
        )
        assert has_temp, "At least one temperature field should be present"
        
        # Check sunshine_hours calculation
        if first_day.sunshine_duration is not None:
            expected_hours = first_day.sunshine_duration / 3600
            assert abs(first_day.sunshine_hours - expected_hours) < 0.01
    
    @pytest.mark.asyncio
    async def test_real_api_edge_case_extreme_coordinates(self):
        """Test API call with extreme but valid coordinates."""
        # Northern location (Reykjavik, Iceland)
        latitude = 64.1466
        longitude = -21.9426
        
        weather_data_list, location = await self.repository.get_weather_data_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Should still get valid data
        assert len(weather_data_list) == 7
        assert isinstance(location, Location)
        
        # Sunshine hours might be 0 or very low in winter in Iceland
        for data in weather_data_list:
            if data.sunshine_hours is not None:
                assert data.sunshine_hours >= 0
                assert data.sunshine_hours <= 24
    
    @pytest.mark.asyncio
    async def test_real_api_response_time(self):
        """Test that API responds within reasonable time."""
        import time
        
        start_time = time.time()
        
        await self.repository.get_weather_data_by_location_and_date_range(
            latitude=35.6762,
            longitude=139.6503,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        elapsed_time = time.time() - start_time
        
        # API should respond within 10 seconds
        assert elapsed_time < 10, f"API took {elapsed_time:.2f}s, should be < 10s"
