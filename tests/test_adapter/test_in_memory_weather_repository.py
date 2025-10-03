"""Tests for InMemoryWeatherRepository."""

import pytest
from datetime import datetime

from agrr_core.adapter.repositories.in_memory_weather_repository import InMemoryWeatherRepository
from agrr_core.entity import WeatherData


class TestInMemoryWeatherRepository:
    """Test InMemoryWeatherRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.repository = InMemoryWeatherRepository()
    
    @pytest.mark.asyncio
    async def test_save_and_get_weather_data(self):
        """Test saving and retrieving weather data."""
        # Create test data
        weather_data = [
            WeatherData(
                time=datetime(2023, 1, 1),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            ),
            WeatherData(
                time=datetime(2023, 1, 2),
                temperature_2m_mean=21.0,
                temperature_2m_max=26.0,
                temperature_2m_min=16.0,
            ),
            WeatherData(
                time=datetime(2023, 1, 15),  # Outside date range
                temperature_2m_mean=22.0,
                temperature_2m_max=27.0,
                temperature_2m_min=17.0,
            ),
        ]
        
        # Save data
        await self.repository.save_weather_data(weather_data)
        
        # Retrieve data within date range
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-10"
        )
        
        # Should return only data within date range
        assert len(result) == 2
        assert result[0].time == datetime(2023, 1, 1)
        assert result[1].time == datetime(2023, 1, 2)
    
    @pytest.mark.asyncio
    async def test_empty_repository(self):
        """Test retrieving from empty repository."""
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-01"
        )
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_clear_repository(self):
        """Test clearing repository."""
        # Add some data
        weather_data = [
            WeatherData(time=datetime(2023, 1, 1), temperature_2m_mean=20.0)
        ]
        await self.repository.save_weather_data(weather_data)
        
        # Clear repository
        self.repository.clear()
        
        # Verify it's empty
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-01"
        )
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_date_range_filtering(self):
        """Test date range filtering."""
        # Create data spanning multiple months
        weather_data = []
        for day in range(1, 32):  # January has 31 days
            weather_data.append(
                WeatherData(
                    time=datetime(2023, 1, day),
                    temperature_2m_mean=20.0 + day * 0.1
                )
            )
        
        await self.repository.save_weather_data(weather_data)
        
        # Test specific date range
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-10", "2023-01-20"
        )
        
        # Should return 11 days (10th to 20th inclusive)
        assert len(result) == 11
        assert result[0].time == datetime(2023, 1, 10)
        assert result[-1].time == datetime(2023, 1, 20)
