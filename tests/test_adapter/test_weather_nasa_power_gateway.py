"""Unit tests for WeatherNASAPowerGateway."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from agrr_core.adapter.gateways.weather_nasa_power_gateway import WeatherNASAPowerGateway
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError


class TestWeatherNASAPowerGateway:
    """Test WeatherNASAPowerGateway."""
    
    @pytest.fixture
    def http_client(self):
        """Create mock HTTP client."""
        return Mock()
    
    @pytest.fixture
    def gateway(self, http_client):
        """Create gateway instance."""
        return WeatherNASAPowerGateway(http_client)
    
    def test_init(self, http_client):
        """Test gateway initialization."""
        gateway = WeatherNASAPowerGateway(http_client)
        assert gateway.http_client == http_client
        assert gateway._request_count == 0
    
    @pytest.mark.asyncio
    async def test_get_not_implemented(self, gateway):
        """Test that get() is not implemented."""
        with pytest.raises(NotImplementedError):
            await gateway.get()
    
    @pytest.mark.asyncio
    async def test_create_not_implemented(self, gateway):
        """Test that create() is not implemented."""
        with pytest.raises(NotImplementedError):
            await gateway.create([], "destination")
    
    @pytest.mark.asyncio
    async def test_get_forecast_not_implemented(self, gateway):
        """Test that get_forecast() is not implemented."""
        with pytest.raises(NotImplementedError):
            await gateway.get_forecast(28.6139, 77.2090)
    
    def test_build_url(self, gateway):
        """Test URL building."""
        url = gateway._build_url(28.6139, 77.2090, "2000-01-01", "2000-01-31")
        
        assert "https://power.larc.nasa.gov/api/temporal/daily/point" in url
        assert "latitude=28.6139" in url
        assert "longitude=77.209" in url  # 末尾の0は省略される
        assert "start=20000101" in url
        assert "end=20000131" in url
        assert "format=JSON" in url
        assert "T2M_MAX" in url
        assert "T2M_MIN" in url
        assert "T2M" in url
        assert "PRECTOTCORR" in url
    
    @pytest.mark.asyncio
    async def test_invalid_latitude(self, gateway):
        """Test that invalid latitude raises error."""
        with pytest.raises(WeatherAPIError, match="Invalid latitude"):
            await gateway.get_by_location_and_date_range(
                91.0, 77.2090, "2000-01-01", "2000-01-31"
            )
    
    @pytest.mark.asyncio
    async def test_invalid_longitude(self, gateway):
        """Test that invalid longitude raises error."""
        with pytest.raises(WeatherAPIError, match="Invalid longitude"):
            await gateway.get_by_location_and_date_range(
                28.6139, 181.0, "2000-01-01", "2000-01-31"
            )
    
    @pytest.mark.asyncio
    async def test_invalid_date_format(self, gateway):
        """Test that invalid date format raises error."""
        with pytest.raises(WeatherAPIError, match="Invalid date format"):
            await gateway.get_by_location_and_date_range(
                28.6139, 77.2090, "2000/01/01", "2000/01/31"
            )
    
    @pytest.mark.asyncio
    async def test_invalid_date_order(self, gateway):
        """Test that invalid date order raises error."""
        with pytest.raises(WeatherAPIError, match="must be before or equal"):
            await gateway.get_by_location_and_date_range(
                28.6139, 77.2090, "2000-02-01", "2000-01-01"
            )
    
    def test_safe_value_none(self, gateway):
        """Test safe value conversion with None."""
        assert gateway._safe_value(None) is None
    
    def test_safe_value_valid(self, gateway):
        """Test safe value conversion with valid value."""
        assert gateway._safe_value(25.5) == 25.5
        assert gateway._safe_value("30.2") == 30.2
    
    def test_safe_value_missing_data(self, gateway):
        """Test safe value conversion with missing data indicator."""
        assert gateway._safe_value(-999) is None
        assert gateway._safe_value(-999.0) is None
        assert gateway._safe_value(-950) is None
    
    def test_safe_value_invalid(self, gateway):
        """Test safe value conversion with invalid value."""
        assert gateway._safe_value("invalid") is None
    
    def test_parse_nasa_power_data_empty(self, gateway):
        """Test parsing empty data."""
        data = {"properties": {"parameter": {}}}
        result = gateway._parse_nasa_power_data(data, "2000-01-01", "2000-01-31")
        assert result == []
    
    def test_parse_nasa_power_data_no_t2m(self, gateway):
        """Test parsing data without T2M."""
        data = {
            "properties": {
                "parameter": {
                    "T2M_MAX": {"20000101": 30.0}
                }
            }
        }
        result = gateway._parse_nasa_power_data(data, "2000-01-01", "2000-01-31")
        assert result == []
    
    def test_parse_nasa_power_data_valid(self, gateway):
        """Test parsing valid NASA POWER data."""
        data = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "20000101": 25.0,
                        "20000102": 26.0
                    },
                    "T2M_MAX": {
                        "20000101": 30.0,
                        "20000102": 31.0
                    },
                    "T2M_MIN": {
                        "20000101": 20.0,
                        "20000102": 21.0
                    },
                    "PRECTOTCORR": {
                        "20000101": 5.0,
                        "20000102": 0.0
                    },
                    "WS2M": {
                        "20000101": 2.5,
                        "20000102": 3.0
                    }
                }
            }
        }
        
        result = gateway._parse_nasa_power_data(data, "2000-01-01", "2000-01-02")
        
        assert len(result) == 2
        assert result[0].time == datetime(2000, 1, 1)
        assert result[0].temperature_2m_mean == 25.0
        assert result[0].temperature_2m_max == 30.0
        assert result[0].temperature_2m_min == 20.0
        assert result[0].precipitation_sum == 5.0
        assert result[0].wind_speed_10m == 2.5
        
        assert result[1].time == datetime(2000, 1, 2)
        assert result[1].temperature_2m_mean == 26.0
    
    def test_parse_nasa_power_data_missing_values(self, gateway):
        """Test parsing data with missing values."""
        data = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "20000101": 25.0,
                        "20000102": -999  # Missing data
                    },
                    "T2M_MAX": {
                        "20000101": 30.0,
                        "20000102": -999
                    },
                    "T2M_MIN": {
                        "20000101": 20.0,
                        "20000102": -999
                    }
                }
            }
        }
        
        result = gateway._parse_nasa_power_data(data, "2000-01-01", "2000-01-02")
        
        # Only first date should be included (second date has all temps missing)
        assert len(result) == 1
        assert result[0].time == datetime(2000, 1, 1)
    
    def test_parse_nasa_power_data_date_filtering(self, gateway):
        """Test that data is filtered by date range."""
        data = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "19991231": 24.0,  # Before start_date
                        "20000101": 25.0,  # In range
                        "20000102": 26.0,  # In range
                        "20000201": 27.0   # After end_date
                    },
                    "T2M_MAX": {
                        "19991231": 29.0,
                        "20000101": 30.0,
                        "20000102": 31.0,
                        "20000201": 32.0
                    },
                    "T2M_MIN": {
                        "19991231": 19.0,
                        "20000101": 20.0,
                        "20000102": 21.0,
                        "20000201": 22.0
                    }
                }
            }
        }
        
        result = gateway._parse_nasa_power_data(data, "2000-01-01", "2000-01-31")
        
        # Only dates within range
        assert len(result) == 2
        assert result[0].time == datetime(2000, 1, 1)
        assert result[1].time == datetime(2000, 1, 2)
    
    @pytest.mark.asyncio
    async def test_get_by_location_and_date_range_success(self, gateway):
        """Test successful data retrieval."""
        # Mock response data
        mock_response_data = {
            "properties": {
                "parameter": {
                    "T2M": {"20000101": 25.0},
                    "T2M_MAX": {"20000101": 30.0},
                    "T2M_MIN": {"20000101": 20.0}
                }
            }
        }
        
        # Mock fetch_data method
        with patch.object(gateway, '_fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response_data
            
            result = await gateway.get_by_location_and_date_range(
                28.6139, 77.2090, "2000-01-01", "2000-01-01"
            )
            
            assert result is not None
            assert len(result.weather_data_list) == 1
            assert result.location.latitude == 28.6139
            assert result.location.longitude == 77.2090
    
    @pytest.mark.asyncio
    async def test_get_by_location_and_date_range_no_data(self, gateway):
        """Test error when no data is found."""
        # Mock response with no data
        mock_response_data = {"properties": {"parameter": {"T2M": {}}}}
        
        with patch.object(gateway, '_fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response_data
            
            with pytest.raises(WeatherDataNotFoundError):
                await gateway.get_by_location_and_date_range(
                    28.6139, 77.2090, "2000-01-01", "2000-01-01"
                )

