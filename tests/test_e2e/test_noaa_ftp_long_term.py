"""E2E tests for NOAA FTP gateway with long-term historical data (2000+).

This test verifies that NOAA ISD FTP data can be fetched for historical periods.
"""

import pytest
from datetime import datetime
from agrr_core.adapter.gateways.weather_noaa_ftp_gateway import WeatherNOAAFTPGateway


@pytest.mark.asyncio
@pytest.mark.slow
class TestNOAAFTPLongTerm:
    """E2E tests for NOAA FTP gateway with long-term data."""
    
    @pytest.fixture
    def gateway(self):
        """Create gateway."""
        return WeatherNOAAFTPGateway()
    
    async def test_fetch_2023_new_york_one_week(self, gateway):
        """Test fetching 1 week of data from 2023 for New York."""
        result = await gateway.get_by_location_and_date_range(
            latitude=40.7128,
            longitude=-74.0060,
            start_date="2023-01-01",
            end_date="2023-01-07"
        )
        
        assert result is not None
        assert result.location is not None
        assert result.weather_data_list is not None
        assert len(result.weather_data_list) >= 5, f"Expected at least 5 days, got {len(result.weather_data_list)}"
        
        # Verify data quality
        for weather_data in result.weather_data_list:
            assert weather_data.time is not None
            assert weather_data.time.year == 2023
            assert weather_data.time.month == 1
            # At least one temperature field should be present
            assert (
                weather_data.temperature_2m_mean is not None or
                weather_data.temperature_2m_max is not None or
                weather_data.temperature_2m_min is not None
            ), f"No temperature data for {weather_data.time}"
        
        print(f"\n✅ 2023 New York: Fetched {len(result.weather_data_list)} days")
        print(f"   Station: ({result.location.latitude:.4f}, {result.location.longitude:.4f})")
        
        # Print sample
        if result.weather_data_list:
            sample = result.weather_data_list[0]
            print(f"   Sample: {sample.time.date()} - Temp: {sample.temperature_2m_mean}°C")
    
    async def test_fetch_2010_los_angeles_one_month(self, gateway):
        """Test fetching 1 month of data from 2010 for Los Angeles."""
        result = await gateway.get_by_location_and_date_range(
            latitude=34.0522,
            longitude=-118.2437,
            start_date="2010-07-01",
            end_date="2010-07-31"
        )
        
        assert result is not None
        assert len(result.weather_data_list) >= 28, f"Expected at least 28 days, got {len(result.weather_data_list)}"
        
        # Verify dates are in July 2010
        for weather_data in result.weather_data_list:
            assert weather_data.time.year == 2010
            assert weather_data.time.month == 7
        
        print(f"\n✅ 2010 Los Angeles: Fetched {len(result.weather_data_list)} days")
    
    async def test_fetch_2005_chicago(self, gateway):
        """Test fetching data from 2005 for Chicago."""
        result = await gateway.get_by_location_and_date_range(
            latitude=41.8781,
            longitude=-87.6298,
            start_date="2005-12-01",
            end_date="2005-12-07"
        )
        
        assert result is not None
        assert len(result.weather_data_list) >= 5
        
        print(f"\n✅ 2005 Chicago: Fetched {len(result.weather_data_list)} days")
    
    async def test_fetch_2000_miami(self, gateway):
        """Test fetching data from 2000 for Miami."""
        result = await gateway.get_by_location_and_date_range(
            latitude=25.7617,
            longitude=-80.1918,
            start_date="2000-06-01",
            end_date="2000-06-07"
        )
        
        assert result is not None
        assert len(result.weather_data_list) >= 5
        
        # Verify temperature ranges are reasonable for Miami summer
        for weather_data in result.weather_data_list:
            if weather_data.temperature_2m_mean is not None:
                # Miami summer: typically 24-32°C
                assert 20 <= weather_data.temperature_2m_mean <= 40, \
                    f"Unrealistic temp for Miami summer: {weather_data.temperature_2m_mean}°C"
        
        print(f"\n✅ 2000 Miami: Fetched {len(result.weather_data_list)} days")
    
    async def test_fetch_multi_year_data(self, gateway):
        """Test fetching data across multiple years (2020-2021)."""
        result = await gateway.get_by_location_and_date_range(
            latitude=40.7128,
            longitude=-74.0060,
            start_date="2020-12-25",
            end_date="2021-01-05"
        )
        
        assert result is not None
        assert len(result.weather_data_list) >= 10
        
        # Verify we have data from both years
        years = set(w.time.year for w in result.weather_data_list)
        assert 2020 in years, "Should have data from 2020"
        assert 2021 in years, "Should have data from 2021"
        
        print(f"\n✅ Multi-year (2020-2021): Fetched {len(result.weather_data_list)} days")
        print(f"   Years covered: {sorted(years)}")


@pytest.mark.asyncio
@pytest.mark.slow
class TestNOAAFTPDataQuality:
    """Tests for data quality and edge cases."""
    
    @pytest.fixture
    def gateway(self):
        """Create gateway."""
        return WeatherNOAAFTPGateway()
    
    async def test_temperature_aggregation(self, gateway):
        """Test that daily temperature aggregation works correctly."""
        result = await gateway.get_by_location_and_date_range(
            latitude=40.7128,
            longitude=-74.0060,
            start_date="2023-01-15",
            end_date="2023-01-15"  # Single day
        )
        
        assert result is not None
        assert len(result.weather_data_list) >= 1
        
        # Check that max >= mean >= min
        for weather_data in result.weather_data_list:
            if (weather_data.temperature_2m_max is not None and 
                weather_data.temperature_2m_min is not None and
                weather_data.temperature_2m_mean is not None):
                assert weather_data.temperature_2m_max >= weather_data.temperature_2m_mean, \
                    f"Max temp should be >= mean temp"
                assert weather_data.temperature_2m_mean >= weather_data.temperature_2m_min, \
                    f"Mean temp should be >= min temp"
        
        print(f"\n✅ Temperature aggregation check passed")
    
    async def test_location_mapping(self, gateway):
        """Test that location mapping works for all major cities."""
        test_cities = [
            (40.7128, -74.0060, "New York"),
            (34.0522, -118.2437, "Los Angeles"),
            (41.8781, -87.6298, "Chicago"),
        ]
        
        for lat, lon, city_name in test_cities:
            usaf, wban, name, st_lat, st_lon = gateway._find_nearest_location(lat, lon)
            
            assert usaf is not None
            assert wban is not None
            assert name is not None
            assert st_lat is not None
            assert st_lon is not None
            
            print(f"\n✅ {city_name}: {name} (USAF: {usaf}, WBAN: {wban})")

