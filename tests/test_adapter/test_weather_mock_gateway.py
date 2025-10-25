"""Tests for weather mock gateway."""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock

from agrr_core.adapter.gateways.weather_mock_gateway import WeatherMockGateway
from agrr_core.entity.entities.weather_entity import WeatherData


class TestWeatherMockGateway:
    """Test cases for WeatherMockGateway."""
    
    def test_init(self):
        """Test gateway initialization."""
        gateway = WeatherMockGateway()
        assert gateway.mock_data_file is None
        assert gateway._mock_data_cache is None
    
    def test_init_with_mock_data_file(self):
        """Test gateway initialization with mock data file."""
        mock_file = "test_mock_data.json"
        gateway = WeatherMockGateway(mock_data_file=mock_file)
        assert gateway.mock_data_file == mock_file
    
    @pytest.mark.asyncio
    async def test_get_by_location_and_date_range(self):
        """Test getting weather data by location and date range."""
        gateway = WeatherMockGateway()
        
        # Test parameters
        latitude = 35.6762
        longitude = 139.6503
        start_date = "2024-01-01"
        end_date = "2024-01-07"
        
        # Call method
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Assertions
        assert result is not None
        assert result.location is not None
        assert result.location.latitude == latitude
        assert result.location.longitude == longitude
        assert len(result.weather_data_list) == 7  # 7 days
        
        # Check that data is sorted by date
        dates = [data.time.date() for data in result.weather_data_list]
        assert dates == sorted(dates)
        
        # Check that all data has required fields
        for data in result.weather_data_list:
            assert isinstance(data, WeatherData)
            assert data.temperature_2m_max is not None
            assert data.temperature_2m_min is not None
            assert data.temperature_2m_mean is not None
            assert data.precipitation_sum is not None
            assert data.sunshine_duration is not None
            assert data.wind_speed_10m is not None
            assert data.weather_code is not None
    
    @pytest.mark.asyncio
    async def test_get_forecast(self):
        """Test getting weather forecast."""
        gateway = WeatherMockGateway()
        
        # Test parameters
        latitude = 35.6762
        longitude = 139.6503
        
        # Call method
        result = await gateway.get_forecast(
            latitude=latitude,
            longitude=longitude
        )
        
        # Assertions
        assert result is not None
        assert result.location is not None
        assert result.location.latitude == latitude
        assert result.location.longitude == longitude
        assert len(result.weather_data_list) == 16  # 16-day forecast
        
        # Check that forecast starts from tomorrow
        tomorrow = datetime.now().date() + timedelta(days=1)
        first_date = result.weather_data_list[0].time.date()
        assert first_date == tomorrow
    
    @pytest.mark.asyncio
    async def test_create_weather_data(self, tmp_path):
        """Test creating weather data file."""
        gateway = WeatherMockGateway()
        
        # Create test weather data
        test_data = [
            WeatherData(
                time=datetime(2024, 1, 1),
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
                temperature_2m_mean=20.0,
                precipitation_sum=0.0,
                sunshine_duration=36000,  # 10 hours
                wind_speed_10m=5.0,
                weather_code=0
            ),
            WeatherData(
                time=datetime(2024, 1, 2),
                temperature_2m_max=27.0,
                temperature_2m_min=17.0,
                temperature_2m_mean=22.0,
                precipitation_sum=5.0,
                sunshine_duration=28800,  # 8 hours
                wind_speed_10m=3.0,
                weather_code=2
            )
        ]
        
        # Create output file
        output_file = tmp_path / "test_weather.json"
        await gateway.create(test_data, str(output_file))
        
        # Check that file was created
        assert output_file.exists()
        
        # Check file content
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'latitude' in data
        assert 'longitude' in data
        assert 'data' in data
        assert len(data['data']) == 2
        
        # Check first record
        first_record = data['data'][0]
        assert first_record['time'] == '2024-01-01T00:00:00'
        assert first_record['temperature_2m_max'] == 25.0
        assert first_record['temperature_2m_min'] == 15.0
        assert first_record['temperature_2m_mean'] == 20.0
    
    def test_generate_daily_mock_data(self):
        """Test generating daily mock data."""
        gateway = WeatherMockGateway()
        
        # Test parameters
        latitude = 35.6762
        longitude = 139.6503
        current_date = datetime(2024, 6, 15)  # Summer
        last_year_date = datetime(2023, 6, 15)
        
        # Call method
        result = gateway._generate_daily_mock_data(
            latitude, longitude, current_date, last_year_date
        )
        
        # Assertions
        assert isinstance(result, WeatherData)
        assert result.time == current_date
        assert result.temperature_2m_max is not None
        assert result.temperature_2m_min is not None
        assert result.temperature_2m_mean is not None
        assert result.precipitation_sum is not None
        assert result.sunshine_duration is not None
        assert result.wind_speed_10m is not None
        assert result.weather_code is not None
        
        # Check temperature relationships
        assert result.temperature_2m_max >= result.temperature_2m_mean
        assert result.temperature_2m_min <= result.temperature_2m_mean
    
    def test_get_seasonal_base_temperature(self):
        """Test getting seasonal base temperature."""
        gateway = WeatherMockGateway()
        
        # Test summer temperature (should be higher)
        summer_date = datetime(2024, 7, 15)
        summer_temp = gateway._get_seasonal_base_temperature(35.6762, 139.6503, summer_date)
        
        # Test winter temperature (should be lower)
        winter_date = datetime(2024, 1, 15)
        winter_temp = gateway._get_seasonal_base_temperature(35.6762, 139.6503, winter_date)
        
        # Summer should be warmer than winter
        assert summer_temp > winter_temp
        
        # Test latitude effect (higher latitude should be colder)
        tokyo_temp = gateway._get_seasonal_base_temperature(35.6762, 139.6503, summer_date)
        hokkaido_temp = gateway._get_seasonal_base_temperature(43.0642, 141.3469, summer_date)
        
        assert tokyo_temp > hokkaido_temp
    
    def test_generate_weather_code(self):
        """Test generating weather code."""
        gateway = WeatherMockGateway()
        
        # Test different conditions
        code_clear = gateway._generate_weather_code(0.0, 10.0)
        code_cloudy = gateway._generate_weather_code(0.0, 3.0)
        code_light_rain = gateway._generate_weather_code(2.0, 8.0)
        code_heavy_rain = gateway._generate_weather_code(10.0, 5.0)
        
        # Assertions
        assert code_clear == 0  # Clear
        assert code_cloudy == 1  # Cloudy
        assert code_light_rain == 2  # Light rain
        assert code_heavy_rain == 3  # Heavy rain
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid inputs."""
        gateway = WeatherMockGateway()
        
        # Test invalid date format
        with pytest.raises(Exception):
            await gateway.get_by_location_and_date_range(
                latitude=35.6762,
                longitude=139.6503,
                start_date="invalid-date",
                end_date="2024-01-07"
            )
        
        # Test invalid coordinates
        with pytest.raises(Exception):
            await gateway.get_by_location_and_date_range(
                latitude=999.0,  # Invalid latitude
                longitude=139.6503,
                start_date="2024-01-01",
                end_date="2024-01-07"
            )
