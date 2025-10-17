"""Tests for NOAA weather gateway."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from agrr_core.adapter.gateways.weather_noaa_gateway import WeatherNOAAGateway, LOCATION_MAPPING
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError


class TestWeatherNOAAGateway:
    """Tests for WeatherNOAAGateway."""
    
    @pytest.fixture
    def mock_http_client(self):
        """Create mock HTTP client."""
        return Mock()
    
    @pytest.fixture
    def gateway(self, mock_http_client):
        """Create gateway instance."""
        return WeatherNOAAGateway(mock_http_client)
    
    def test_init(self, mock_http_client):
        """Test gateway initialization."""
        gateway = WeatherNOAAGateway(mock_http_client)
        assert gateway.http_client == mock_http_client
        assert gateway.logger is not None
    
    @pytest.mark.asyncio
    async def test_get_not_implemented(self, gateway):
        """Test that get() raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await gateway.get()
    
    @pytest.mark.asyncio
    async def test_create_not_implemented(self, gateway):
        """Test that create() raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await gateway.create([], "")
    
    @pytest.mark.asyncio
    async def test_get_forecast_not_implemented(self, gateway):
        """Test that get_forecast() raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await gateway.get_forecast(40.7128, -74.0060)
    
    def test_find_nearest_location_new_york(self, gateway):
        """Test finding nearest location for New York."""
        usaf, wban, name, lat, lon = gateway._find_nearest_location(40.7128, -74.0060)
        
        assert usaf == "725030"
        assert wban == "14732"
        assert "LaGuardia" in name
        assert lat == pytest.approx(40.7769, abs=0.01)
        assert lon == pytest.approx(-73.8739, abs=0.01)
    
    def test_find_nearest_location_los_angeles(self, gateway):
        """Test finding nearest location for Los Angeles."""
        usaf, wban, name, lat, lon = gateway._find_nearest_location(34.0522, -118.2437)
        
        assert usaf == "722950"
        assert wban == "23174"
        assert "Los Angeles" in name
        assert lat == pytest.approx(33.9381, abs=0.01)
        assert lon == pytest.approx(-118.3889, abs=0.01)
    
    def test_find_nearest_location_nearby(self, gateway):
        """Test finding nearest location for nearby coordinates."""
        # Slightly offset from New York
        usaf, wban, name, lat, lon = gateway._find_nearest_location(40.72, -74.01)
        
        # Should still find LaGuardia
        assert usaf == "725030"
        assert "LaGuardia" in name
    
    def test_parse_noaa_value_temperature(self, gateway):
        """Test parsing NOAA temperature value."""
        # NOAA format: "+15.5,1" means 15.5°C (already scaled)
        result = gateway._parse_noaa_value("+155,1", scale=10.0)
        assert result == pytest.approx(15.5, abs=0.1)
    
    def test_parse_noaa_value_missing(self, gateway):
        """Test parsing missing NOAA value."""
        result = gateway._parse_noaa_value("+9999,9")
        assert result is None
    
    def test_parse_noaa_value_empty(self, gateway):
        """Test parsing empty NOAA value."""
        result = gateway._parse_noaa_value("")
        assert result is None
    
    def test_parse_noaa_value_negative(self, gateway):
        """Test parsing negative NOAA value."""
        result = gateway._parse_noaa_value("-50,1", scale=10.0)
        assert result == pytest.approx(-5.0, abs=0.1)
    
    @pytest.mark.asyncio
    async def test_get_by_location_invalid_date_format(self, gateway):
        """Test invalid date format raises error."""
        with pytest.raises(WeatherAPIError, match="Invalid date format"):
            await gateway.get_by_location_and_date_range(
                40.7128, -74.0060,
                "2024/01/01",  # Invalid format
                "2024-01-07"
            )
    
    @pytest.mark.asyncio
    async def test_get_by_location_invalid_date_order(self, gateway):
        """Test invalid date order raises error."""
        with pytest.raises(WeatherAPIError, match="must be before or equal to"):
            await gateway.get_by_location_and_date_range(
                40.7128, -74.0060,
                "2024-01-07",
                "2024-01-01"  # End before start
            )
    
    def test_aggregate_to_daily(self, gateway):
        """Test aggregating hourly data to daily."""
        from agrr_core.entity import WeatherData
        
        # Create hourly data for one day
        hourly_data = [
            WeatherData(
                time=datetime(2024, 1, 15, 0, 0, 0),
                temperature_2m_max=10.0,
                temperature_2m_min=10.0,
                temperature_2m_mean=10.0,
                precipitation_sum=0.5,
                sunshine_duration=None,
                wind_speed_10m=5.0,
                weather_code=None,
            ),
            WeatherData(
                time=datetime(2024, 1, 15, 12, 0, 0),
                temperature_2m_max=20.0,
                temperature_2m_min=20.0,
                temperature_2m_mean=20.0,
                precipitation_sum=1.0,
                sunshine_duration=None,
                wind_speed_10m=10.0,
                weather_code=None,
            ),
        ]
        
        daily_data = gateway._aggregate_to_daily(hourly_data)
        
        assert len(daily_data) == 1
        assert daily_data[0].time.date() == datetime(2024, 1, 15).date()
        assert daily_data[0].temperature_2m_max == 20.0
        assert daily_data[0].temperature_2m_min == 10.0
        assert daily_data[0].temperature_2m_mean == pytest.approx(15.0, abs=0.1)
        assert daily_data[0].precipitation_sum == pytest.approx(1.5, abs=0.1)
        assert daily_data[0].wind_speed_10m == 10.0
    
    def test_aggregate_to_daily_multiple_days(self, gateway):
        """Test aggregating hourly data across multiple days."""
        from agrr_core.entity import WeatherData
        
        hourly_data = [
            WeatherData(
                time=datetime(2024, 1, 15, 12, 0, 0),
                temperature_2m_max=15.0,
                temperature_2m_min=15.0,
                temperature_2m_mean=15.0,
                precipitation_sum=1.0,
                sunshine_duration=None,
                wind_speed_10m=5.0,
                weather_code=None,
            ),
            WeatherData(
                time=datetime(2024, 1, 16, 12, 0, 0),
                temperature_2m_max=20.0,
                temperature_2m_min=20.0,
                temperature_2m_mean=20.0,
                precipitation_sum=2.0,
                sunshine_duration=None,
                wind_speed_10m=10.0,
                weather_code=None,
            ),
        ]
        
        daily_data = gateway._aggregate_to_daily(hourly_data)
        
        assert len(daily_data) == 2
        assert daily_data[0].time.date() == datetime(2024, 1, 15).date()
        assert daily_data[1].time.date() == datetime(2024, 1, 16).date()
    
    def test_location_mapping_coverage(self):
        """Test that location mapping includes major US cities."""
        # Check major cities are present
        cities = {
            (40.7128, -74.0060): "New York",
            (34.0522, -118.2437): "Los Angeles",
            (41.8781, -87.6298): "Chicago",
            (29.7604, -95.3698): "Houston",
            (33.4484, -112.0740): "Phoenix",
        }
        
        for coords, city_name in cities.items():
            assert coords in LOCATION_MAPPING, f"{city_name} not in mapping"


class TestNOAALocationMapping:
    """Tests for NOAA location mapping."""
    
    def test_location_mapping_structure(self):
        """Test location mapping has correct structure."""
        for coords, station_info in LOCATION_MAPPING.items():
            assert len(coords) == 2, "Coordinates should be (lat, lon)"
            assert len(station_info) == 5, "Station info should be (usaf, wban, name, lat, lon)"
            
            lat, lon = coords
            usaf, wban, name, st_lat, st_lon = station_info
            
            # Validate coordinate ranges
            assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
            assert -180 <= lon <= 180, f"Invalid longitude: {lon}"
            assert -90 <= st_lat <= 90, f"Invalid station latitude: {st_lat}"
            assert -180 <= st_lon <= 180, f"Invalid station longitude: {st_lon}"
            
            # Validate station IDs
            assert isinstance(usaf, str), "USAF should be string"
            assert isinstance(wban, str), "WBAN should be string"
            assert len(usaf) > 0, "USAF should not be empty"
            assert len(wban) > 0, "WBAN should not be empty"
            
            # Validate name
            assert isinstance(name, str), "Name should be string"
            assert len(name) > 0, "Name should not be empty"

