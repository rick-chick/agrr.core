"""E2E tests for NOAA ISD India weather data retrieval.

These tests verify that actual data can be fetched from NOAA for Indian agricultural regions.
Note: These tests make real HTTP requests and may be slow or fail if NOAA servers are unavailable.
"""

import pytest
from datetime import datetime, timedelta

from agrr_core.adapter.gateways.weather_noaa_gateway import WeatherNOAAGateway
from agrr_core.framework.services.clients.http_client import HttpClient
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError


@pytest.mark.e2e
@pytest.mark.asyncio
class TestNOAAIndiaE2E:
    """E2E tests for NOAA India data retrieval."""
    
    @pytest.fixture
    def gateway(self):
        """Create gateway with real HTTP client."""
        http_client = HttpClient()
        return WeatherNOAAGateway(http_client)
    
    @pytest.mark.slow
    async def test_delhi_weather_2023(self, gateway):
        """Test fetching Delhi weather data for 2023."""
        # Delhi: (28.5844, 77.2031)
        result = await gateway.get_by_location_and_date_range(
            latitude=28.5844,
            longitude=77.2031,
            start_date="2023-01-01",
            end_date="2023-01-31"  # One month
        )
        
        assert result is not None
        assert result.location is not None
        assert result.location.latitude == pytest.approx(28.5844, abs=0.01)
        assert result.location.longitude == pytest.approx(77.2031, abs=0.01)
        
        # Should have data for January
        assert len(result.weather_data_list) > 0
        # January has 31 days, but some days might be missing
        assert len(result.weather_data_list) >= 20, "Should have at least 20 days of data"
        
        # Check data quality
        for weather_data in result.weather_data_list:
            assert weather_data.time is not None
            # India typical temperature range: -10 to 50°C
            if weather_data.temperature_2m_mean is not None:
                assert -10 <= weather_data.temperature_2m_mean <= 50
    
    @pytest.mark.slow
    async def test_mumbai_weather_recent(self, gateway):
        """Test fetching Mumbai weather data for recent dates."""
        # Mumbai: (19.0896, 72.8681)
        # Fetch last 7 days
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=6)  # 7 days ago
        
        result = await gateway.get_by_location_and_date_range(
            latitude=19.0896,
            longitude=72.8681,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        assert result is not None
        assert result.location is not None
        assert len(result.weather_data_list) > 0
        
        # Mumbai is coastal, should have moderate temperatures (15-35°C typically)
        for weather_data in result.weather_data_list:
            if weather_data.temperature_2m_mean is not None:
                assert 10 <= weather_data.temperature_2m_mean <= 45
    
    @pytest.mark.slow
    async def test_ludhiana_agricultural_region_2022(self, gateway):
        """Test fetching Ludhiana (Punjab agricultural region) data for 2022."""
        # Ludhiana: (30.9000, 75.8500) - Punjab wheat belt
        result = await gateway.get_by_location_and_date_range(
            latitude=30.9000,
            longitude=75.8500,
            start_date="2022-06-01",
            end_date="2022-06-30"  # June (monsoon season)
        )
        
        assert result is not None
        assert result.location is not None
        assert len(result.weather_data_list) > 0
        
        # Check that we got reasonable agricultural data
        temps = [d.temperature_2m_mean for d in result.weather_data_list if d.temperature_2m_mean is not None]
        if temps:
            # June in Punjab: typically 25-40°C
            assert min(temps) >= 15, "Min temperature should be >= 15°C"
            assert max(temps) <= 50, "Max temperature should be <= 50°C"
    
    @pytest.mark.slow
    async def test_bangalore_southern_region_2021(self, gateway):
        """Test fetching Bangalore (Karnataka) data for 2021."""
        # Bangalore: (12.9500, 77.6681) - Southern India
        result = await gateway.get_by_location_and_date_range(
            latitude=12.9500,
            longitude=77.6681,
            start_date="2021-03-01",
            end_date="2021-03-31"  # March (pre-monsoon)
        )
        
        assert result is not None
        assert result.location is not None
        assert len(result.weather_data_list) > 0
        
        # Bangalore has moderate climate year-round
        temps = [d.temperature_2m_mean for d in result.weather_data_list if d.temperature_2m_mean is not None]
        if temps:
            # Bangalore: typically 15-35°C
            assert min(temps) >= 10, "Min temperature should be >= 10°C"
            assert max(temps) <= 40, "Max temperature should be <= 40°C"
    
    @pytest.mark.slow
    async def test_kolkata_eastern_region_2020(self, gateway):
        """Test fetching Kolkata (West Bengal) data for 2020."""
        # Kolkata: (22.6544, 88.4467) - Eastern India
        result = await gateway.get_by_location_and_date_range(
            latitude=22.6544,
            longitude=88.4467,
            start_date="2020-01-01",
            end_date="2020-01-15"  # First half of January
        )
        
        assert result is not None
        assert result.location is not None
        assert len(result.weather_data_list) > 0
        
        # Kolkata winter temperatures: typically 12-25°C in January
        temps = [d.temperature_2m_mean for d in result.weather_data_list if d.temperature_2m_mean is not None]
        if temps:
            assert min(temps) >= 5, "Min temperature should be >= 5°C"
            assert max(temps) <= 35, "Max temperature should be <= 35°C"
    
    @pytest.mark.slow
    async def test_multiple_years_data_availability(self, gateway):
        """Test that data is available for multiple years (2000-2024)."""
        # Test Delhi for different years
        test_years = [2000, 2010, 2020, 2023]
        
        for year in test_years:
            try:
                result = await gateway.get_by_location_and_date_range(
                    latitude=28.5844,  # Delhi
                    longitude=77.2031,
                    start_date=f"{year}-07-01",
                    end_date=f"{year}-07-07"  # One week in July
                )
                
                assert result is not None
                assert len(result.weather_data_list) > 0
                print(f"✓ Data available for {year}: {len(result.weather_data_list)} days")
                
            except WeatherDataNotFoundError:
                # Some years might not have data
                print(f"⚠ No data available for {year}")
                continue
    
    @pytest.mark.slow
    async def test_data_quality_precipitation(self, gateway):
        """Test that precipitation data is present and reasonable."""
        # Test Chennai (coastal) during monsoon season
        # Chennai: (12.9900, 80.1692)
        result = await gateway.get_by_location_and_date_range(
            latitude=12.9900,
            longitude=80.1692,
            start_date="2022-11-01",
            end_date="2022-11-30"  # November (northeast monsoon)
        )
        
        assert result is not None
        assert len(result.weather_data_list) > 0
        
        # Check that some days have precipitation data
        precip_data = [d.precipitation_sum for d in result.weather_data_list if d.precipitation_sum is not None]
        
        # At least some data should be available
        assert len(precip_data) >= len(result.weather_data_list) * 0.3, \
            "At least 30% of days should have precipitation data"
        
        # Precipitation should be non-negative
        for precip in precip_data:
            assert precip >= 0, f"Precipitation should be non-negative, got {precip}"

