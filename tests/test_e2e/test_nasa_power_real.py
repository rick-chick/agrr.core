"""E2E tests for NASA POWER API with real API calls.

These tests verify the actual NASA POWER API integration.
Run with: pytest tests/test_e2e/test_nasa_power_real.py -v -m e2e
"""

import pytest
from datetime import datetime

from agrr_core.framework.services.clients.http_client import HttpClient
from agrr_core.adapter.gateways.weather_nasa_power_gateway import WeatherNASAPowerGateway


class TestNASAPowerRealAPI:
    """E2E tests for NASA POWER API (real API calls)."""
    
    @pytest.fixture
    def http_client(self):
        """Create HTTP client instance."""
        return HttpClient()
    
    @pytest.fixture
    def gateway(self, http_client):
        """Create NASA POWER gateway instance."""
        return WeatherNASAPowerGateway(http_client)
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_fetch_new_delhi_short_period(self, gateway):
        """Test fetching real data for New Delhi (short period)."""
        # New Delhi coordinates
        latitude = 28.6139
        longitude = 77.2090
        
        # Short period for faster testing
        start_date = "2023-01-01"
        end_date = "2023-01-07"
        
        result = await gateway.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
        
        # Verify result
        assert result is not None
        assert len(result.weather_data_list) == 7
        assert result.location.latitude == latitude
        assert result.location.longitude == longitude
        
        # Verify data quality
        for weather_data in result.weather_data_list:
            assert weather_data.time is not None
            # Temperature should be reasonable for New Delhi in January
            if weather_data.temperature_2m_mean is not None:
                assert 0 <= weather_data.temperature_2m_mean <= 40
        
        print(f"\n✅ New Delhi: Successfully fetched {len(result.weather_data_list)} days")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_fetch_mumbai_long_period(self, gateway):
        """Test fetching real data for Mumbai (1 year)."""
        # Mumbai coordinates
        latitude = 19.0760
        longitude = 72.8777
        
        # 1 year period
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        
        result = await gateway.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
        
        # Verify result (should be ~365 days)
        assert result is not None
        assert 360 <= len(result.weather_data_list) <= 366
        
        # Verify temperature ranges for Mumbai (tropical climate)
        temps = [
            wd.temperature_2m_mean 
            for wd in result.weather_data_list 
            if wd.temperature_2m_mean is not None
        ]
        assert len(temps) > 350  # Most days should have temperature data
        assert min(temps) > 15   # Mumbai rarely gets below 15°C
        assert max(temps) < 40   # Mumbai rarely exceeds 40°C
        
        print(f"\n✅ Mumbai: Successfully fetched {len(result.weather_data_list)} days")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_fetch_india_2000_2024(self, gateway):
        """Test fetching 24 years of data (2000-2024) for Delhi.
        
        This test verifies that NASA POWER can handle long-term data requests.
        Marked as 'slow' because it may take 30-60 seconds.
        """
        # New Delhi coordinates
        latitude = 28.6139
        longitude = 77.2090
        
        # 24 years
        start_date = "2000-01-01"
        end_date = "2024-12-31"
        
        result = await gateway.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
        
        # Verify result (should be ~9,131 days for 25 years)
        assert result is not None
        assert 9000 <= len(result.weather_data_list) <= 9200
        
        # Verify data starts from 2000 and ends in 2024
        dates = [wd.time for wd in result.weather_data_list]
        assert min(dates) >= datetime(2000, 1, 1)
        assert max(dates) <= datetime(2024, 12, 31)
        
        print(f"\n✅ Delhi 2000-2024: Successfully fetched {len(result.weather_data_list)} days")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.parametrize("coords,city_name", [
        ((28.6139, 77.2090), "New Delhi"),
        ((19.0760, 72.8777), "Mumbai"),
        ((13.0827, 80.2707), "Chennai"),
        ((22.5726, 88.3639), "Kolkata"),
        ((12.9716, 77.5946), "Bangalore"),
    ])
    async def test_major_cities_data_availability(self, gateway, coords, city_name):
        """Test that major Indian cities have data available.
        
        This test verifies that NASA POWER covers all major Indian cities.
        """
        latitude, longitude = coords
        start_date = "2023-06-01"
        end_date = "2023-06-07"
        
        result = await gateway.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
        
        assert result is not None
        assert len(result.weather_data_list) == 7
        
        # Verify at least one temperature value exists
        has_temp = any(
            wd.temperature_2m_mean is not None 
            for wd in result.weather_data_list
        )
        assert has_temp, f"{city_name} should have temperature data"
        
        print(f"\n✅ {city_name}: Data available")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_remote_location_coverage(self, gateway):
        """Test that NASA POWER covers remote locations (not just cities).
        
        Tests a rural location in Rajasthan to verify grid-based coverage.
        """
        # Rural location in Rajasthan (not a major city)
        latitude = 27.5
        longitude = 73.5
        
        start_date = "2023-01-01"
        end_date = "2023-01-07"
        
        result = await gateway.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
        
        assert result is not None
        assert len(result.weather_data_list) == 7
        
        print(f"\n✅ Remote Rajasthan location: Data available")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_data_quality_checks(self, gateway):
        """Test data quality for a known location."""
        # Bangalore (moderate climate)
        latitude = 12.9716
        longitude = 77.5946
        
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        
        result = await gateway.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
        
        # Count data completeness
        total_days = len(result.weather_data_list)
        
        has_temp_mean = sum(
            1 for wd in result.weather_data_list 
            if wd.temperature_2m_mean is not None
        )
        has_temp_max = sum(
            1 for wd in result.weather_data_list 
            if wd.temperature_2m_max is not None
        )
        has_temp_min = sum(
            1 for wd in result.weather_data_list 
            if wd.temperature_2m_min is not None
        )
        has_precip = sum(
            1 for wd in result.weather_data_list 
            if wd.precipitation_sum is not None
        )
        
        # NASA POWER should have >95% data completeness
        assert has_temp_mean / total_days > 0.95
        assert has_temp_max / total_days > 0.95
        assert has_temp_min / total_days > 0.95
        assert has_precip / total_days > 0.95
        
        print(f"\n✅ Data quality:")
        print(f"   Temperature Mean: {has_temp_mean/total_days*100:.1f}%")
        print(f"   Temperature Max:  {has_temp_max/total_days*100:.1f}%")
        print(f"   Temperature Min:  {has_temp_min/total_days*100:.1f}%")
        print(f"   Precipitation:    {has_precip/total_days*100:.1f}%")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_rate_limiting(self, gateway):
        """Test that rate limiting works correctly.
        
        Makes 5 consecutive requests to verify rate limiting doesn't cause issues.
        """
        cities = [
            (28.6139, 77.2090),  # Delhi
            (19.0760, 72.8777),  # Mumbai
            (13.0827, 80.2707),  # Chennai
            (22.5726, 88.3639),  # Kolkata
            (12.9716, 77.5946),  # Bangalore
        ]
        
        start_date = "2023-01-01"
        end_date = "2023-01-07"
        
        results = []
        for lat, lon in cities:
            result = await gateway.get_by_location_and_date_range(
                lat, lon, start_date, end_date
            )
            results.append(result)
        
        # All requests should succeed
        assert len(results) == 5
        assert all(len(r.weather_data_list) == 7 for r in results)
        
        # Request count should be tracked
        assert gateway._request_count == 5
        
        print(f"\n✅ Rate limiting: {gateway._request_count} requests completed successfully")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_json_output_format(self, gateway):
        """Test that JSON output format is correct for NASA POWER data.
        
        This test verifies that the data can be properly formatted for JSON output,
        including location information (without elevation/timezone which NASA POWER doesn't provide).
        """
        import json
        
        # Delhi, India
        latitude = 28.6139
        longitude = 77.2090
        start_date = "2023-01-01"
        end_date = "2023-01-07"
        
        result = await gateway.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
        
        # Verify result structure
        assert result is not None
        assert result.location is not None
        assert result.weather_data_list is not None
        assert len(result.weather_data_list) == 7
        
        # Verify location data (NASA POWER specific: no elevation/timezone)
        assert result.location.latitude == latitude
        assert result.location.longitude == longitude
        assert result.location.elevation is None
        assert result.location.timezone is None
        
        # Verify data can be converted to JSON format
        from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
        from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
        from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
        
        # Convert to DTOs (as done in presenter)
        dto_list = []
        for weather_data in result.weather_data_list:
            dto = WeatherDataResponseDTO(
                time=weather_data.time.isoformat(),
                temperature_2m_max=weather_data.temperature_2m_max,
                temperature_2m_min=weather_data.temperature_2m_min,
                temperature_2m_mean=weather_data.temperature_2m_mean,
                precipitation_sum=weather_data.precipitation_sum,
                sunshine_duration=weather_data.sunshine_duration,
                sunshine_hours=weather_data.sunshine_hours,
                wind_speed_10m=weather_data.wind_speed_10m,
                weather_code=weather_data.weather_code,
            )
            dto_list.append(dto)
        
        location_dto = LocationResponseDTO(
            latitude=result.location.latitude,
            longitude=result.location.longitude,
            elevation=result.location.elevation,
            timezone=result.location.timezone
        )
        
        weather_list_dto = WeatherDataListResponseDTO(
            data=dto_list,
            total_count=len(dto_list),
            location=location_dto
        )
        
        # Convert to JSON-serializable format
        json_data = {
            "data": [
                {
                    "time": item.time,
                    "temperature_2m_max": item.temperature_2m_max,
                    "temperature_2m_min": item.temperature_2m_min,
                    "temperature_2m_mean": item.temperature_2m_mean,
                    "precipitation_sum": item.precipitation_sum,
                    "sunshine_duration": item.sunshine_duration,
                    "sunshine_hours": item.sunshine_hours,
                    "wind_speed_10m": item.wind_speed_10m,
                    "weather_code": item.weather_code,
                }
                for item in weather_list_dto.data
            ],
            "total_count": weather_list_dto.total_count,
            "location": {
                "latitude": weather_list_dto.location.latitude,
                "longitude": weather_list_dto.location.longitude,
                "elevation": weather_list_dto.location.elevation,
                "timezone": weather_list_dto.location.timezone,
            }
        }
        
        # Verify JSON can be serialized
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        assert json_str is not None
        assert len(json_str) > 0
        
        # Verify JSON structure
        parsed = json.loads(json_str)
        assert "data" in parsed
        assert "total_count" in parsed
        assert "location" in parsed
        assert parsed["total_count"] == 7
        assert parsed["location"]["latitude"] == latitude
        assert parsed["location"]["longitude"] == longitude
        assert parsed["location"]["elevation"] is None
        assert parsed["location"]["timezone"] is None
        
        print(f"\n✅ JSON output format validated")
        print(f"   Total records: {parsed['total_count']}")
        print(f"   Location: {parsed['location']['latitude']}, {parsed['location']['longitude']}")

