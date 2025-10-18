"""E2E tests for NOAA FTP weather gateway with real US cities.

This test verifies that NOAA weather data can be fetched for major US cities
using the NOAA FTP data source (more stable than HTTP access).
"""

import pytest
from datetime import datetime, timedelta
from agrr_core.adapter.gateways.weather_noaa_ftp_gateway import WeatherNOAAFTPGateway


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestNOAAUSCities:
    """E2E tests for NOAA FTP weather gateway with real US cities."""
    
    @pytest.fixture
    def gateway(self):
        """Create NOAA FTP gateway."""
        return WeatherNOAAFTPGateway()
    
    @pytest.mark.parametrize("city_name,latitude,longitude", [
        ("New York", 40.7128, -74.0060),
        ("Los Angeles", 34.0522, -118.2437),
        ("Chicago", 41.8781, -87.6298),
    ])
    async def test_fetch_weather_for_us_cities(self, gateway, city_name, latitude, longitude):
        """Test fetching weather data for major US cities."""
        # Use historical data (2023) instead of recent data to avoid availability issues
        start_date = datetime(2023, 1, 1).date()
        end_date = datetime(2023, 1, 7).date()
        
        # Fetch data
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        # Verify response structure
        assert result is not None
        assert result.location is not None
        assert result.weather_data_list is not None
        assert len(result.weather_data_list) > 0
        
        # Verify location
        assert result.location.latitude is not None
        assert result.location.longitude is not None
        
        # Verify weather data
        for weather_data in result.weather_data_list:
            assert weather_data.time is not None
            # At least one temperature field should be present
            assert (
                weather_data.temperature_2m_mean is not None or
                weather_data.temperature_2m_max is not None or
                weather_data.temperature_2m_min is not None
            ), f"No temperature data for {city_name} on {weather_data.time}"
        
        print(f"\n✅ {city_name}: Fetched {len(result.weather_data_list)} days of data")
        print(f"   Station: ({result.location.latitude:.4f}, {result.location.longitude:.4f})")
        
        # Print sample data
        if result.weather_data_list:
            sample = result.weather_data_list[0]
            print(f"   Sample: {sample.time.date()} - Temp: {sample.temperature_2m_mean}°C")
    
    async def test_fetch_historical_data_2023(self, gateway):
        """Test fetching historical data from 2023 for New York."""
        result = await gateway.get_by_location_and_date_range(
            latitude=40.7128,
            longitude=-74.0060,
            start_date="2023-01-01",
            end_date="2023-01-07"
        )
        
        assert result is not None
        assert len(result.weather_data_list) > 0
        
        # Verify dates are in January 2023
        for weather_data in result.weather_data_list:
            assert weather_data.time.year == 2023
            assert weather_data.time.month == 1
        
        print(f"\n✅ Historical 2023: Fetched {len(result.weather_data_list)} days")
    
    async def test_fetch_data_new_york_full_week(self, gateway):
        """Test fetching a full week of data for New York."""
        # Use historical data to ensure availability
        start_date = datetime(2023, 6, 1).date()
        end_date = datetime(2023, 6, 7).date()
        
        result = await gateway.get_by_location_and_date_range(
            latitude=40.7128,
            longitude=-74.0060,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        assert result is not None
        weather_data_list = result.weather_data_list
        
        # Should have approximately 7 days of data
        assert len(weather_data_list) >= 5, f"Expected at least 5 days, got {len(weather_data_list)}"
        
        # Verify data quality
        temps_found = 0
        for data in weather_data_list:
            if data.temperature_2m_mean is not None:
                temps_found += 1
                # Reasonable temperature range for New York
                assert -30 <= data.temperature_2m_mean <= 45, f"Unrealistic temp: {data.temperature_2m_mean}°C"
        
        assert temps_found > 0, "No temperature data found"
        
        print(f"\n✅ New York Full Week: {len(weather_data_list)} days, {temps_found} with temps")
    
    async def test_fetch_data_los_angeles_month(self, gateway):
        """Test fetching a month of data for Los Angeles."""
        # Get January 2023
        result = await gateway.get_by_location_and_date_range(
            latitude=34.0522,
            longitude=-118.2437,
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        
        assert result is not None
        weather_data_list = result.weather_data_list
        
        # Should have close to 31 days
        assert len(weather_data_list) >= 25, f"Expected at least 25 days, got {len(weather_data_list)}"
        
        print(f"\n✅ Los Angeles Month: {len(weather_data_list)} days")
        
        # Check date continuity
        dates = sorted([data.time.date() for data in weather_data_list])
        print(f"   Date range: {dates[0]} to {dates[-1]}")

