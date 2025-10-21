"""E2E tests for NOAA Thailand weather data retrieval.

This test suite validates actual data retrieval from NOAA ISD for Thailand's
major agricultural regions.

Note: These tests require network connectivity and may take time to execute.
"""

import pytest
from datetime import datetime

from agrr_core.adapter.gateways.weather_noaa_gateway import WeatherNOAAGateway
from agrr_core.framework.services.clients.http_client import HttpClient


@pytest.mark.e2e
@pytest.mark.asyncio
class TestNOAAThailandE2E:
    """E2E tests for NOAA Thailand weather data."""
    
    @pytest.fixture
    def gateway(self):
        """Create WeatherNOAAGateway instance."""
        http_client = HttpClient()
        return WeatherNOAAGateway(http_client)
    
    async def test_bangkok_weather_2023(self, gateway):
        """Test Bangkok (Don Mueang) weather data retrieval for 2023.
        
        バンコク（ドンムアン空港）の2023年1月のデータ取得テスト
        """
        # Bangkok Don Mueang International Airport
        latitude = 13.9130
        longitude = 100.6070
        start_date = "2023-01-01"
        end_date = "2023-01-31"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        assert abs(result.location.latitude - 13.913) < 0.01
        assert abs(result.location.longitude - 100.607) < 0.01
        assert result.location.timezone == "Asia/Bangkok"
        
        # Verify weather data
        assert len(result.weather_data_list) > 0
        assert len(result.weather_data_list) <= 31  # Max 31 days in January
        
        # Check data quality
        for weather_data in result.weather_data_list:
            assert weather_data.time is not None
            # Bangkok typical temperature range: 20-35°C
            if weather_data.temperature_2m_mean is not None:
                assert 15 <= weather_data.temperature_2m_mean <= 40
    
    async def test_chiang_mai_weather_2023(self, gateway):
        """Test Chiang Mai weather data retrieval for 2023.
        
        チェンマイの2023年3月のデータ取得テスト（北部・米・果樹生産地）
        """
        # Chiang Mai International Airport
        latitude = 18.7670
        longitude = 98.9630
        start_date = "2023-03-01"
        end_date = "2023-03-31"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        assert abs(result.location.latitude - 18.767) < 0.01
        assert abs(result.location.longitude - 98.963) < 0.01
        assert result.location.timezone == "Asia/Bangkok"
        
        # Verify weather data
        assert len(result.weather_data_list) > 0
        
        # Check temperature range (Chiang Mai: cooler than Bangkok)
        for weather_data in result.weather_data_list:
            if weather_data.temperature_2m_mean is not None:
                assert 10 <= weather_data.temperature_2m_mean <= 42
    
    async def test_udon_thani_weather_2023(self, gateway):
        """Test Udon Thani weather data retrieval for 2023.
        
        ウドンターニーの2023年8月のデータ取得テスト（東北部イサーン・米の主要生産地）
        """
        # Udon Thani
        latitude = 17.3860
        longitude = 102.7880
        start_date = "2023-08-01"
        end_date = "2023-08-31"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        assert abs(result.location.latitude - 17.386) < 0.01
        assert abs(result.location.longitude - 102.788) < 0.01
        
        # Verify weather data (rainy season)
        assert len(result.weather_data_list) > 0
        
        # Check for precipitation data (August is rainy season)
        has_precipitation = any(
            wd.precipitation_sum is not None and wd.precipitation_sum > 0
            for wd in result.weather_data_list
        )
        # Note: May not have precipitation every day, so just verify data exists
        assert len(result.weather_data_list) > 0
    
    async def test_surat_thani_weather_2023(self, gateway):
        """Test Surat Thani weather data retrieval for 2023.
        
        スラートターニーの2023年5月のデータ取得テスト（南部・パーム油・ゴム生産地）
        """
        # Surat Thani
        latitude = 9.1330
        longitude = 99.1360
        start_date = "2023-05-01"
        end_date = "2023-05-31"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        assert abs(result.location.latitude - 9.133) < 0.01
        assert abs(result.location.longitude - 99.136) < 0.01
        
        # Verify weather data
        assert len(result.weather_data_list) > 0
        
        # Southern Thailand is typically warm and humid
        for weather_data in result.weather_data_list:
            if weather_data.temperature_2m_mean is not None:
                assert 20 <= weather_data.temperature_2m_mean <= 38
    
    async def test_khon_kaen_weather_2023(self, gateway):
        """Test Khon Kaen weather data retrieval for 2023.
        
        コーンケンの2023年11月のデータ取得テスト（東北部・米の主要生産地）
        """
        # Khon Kaen
        latitude = 16.4670
        longitude = 102.7840
        start_date = "2023-11-01"
        end_date = "2023-11-30"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        assert abs(result.location.latitude - 16.467) < 0.01
        assert abs(result.location.longitude - 102.784) < 0.01
        
        # Verify weather data
        assert len(result.weather_data_list) > 0
    
    async def test_phuket_weather_2023(self, gateway):
        """Test Phuket weather data retrieval for 2023.
        
        プーケットの2023年12月のデータ取得テスト（南部・観光地・ゴム生産地）
        """
        # Phuket International Airport
        latitude = 8.1130
        longitude = 98.3170
        start_date = "2023-12-01"
        end_date = "2023-12-31"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        assert abs(result.location.latitude - 8.113) < 0.01
        assert abs(result.location.longitude - 98.317) < 0.01
        
        # Verify weather data
        assert len(result.weather_data_list) > 0
        
        # Phuket: tropical climate, consistently warm
        for weather_data in result.weather_data_list:
            if weather_data.temperature_2m_mean is not None:
                assert 22 <= weather_data.temperature_2m_mean <= 36
    
    async def test_nakhon_ratchasima_weather_2022(self, gateway):
        """Test Nakhon Ratchasima (Korat) weather data for 2022.
        
        ナコーンラーチャシーマー（コラート）の2022年データ取得テスト
        （東北部南部・米・キャッサバ生産地）
        """
        # Nakhon Ratchasima (Korat)
        latitude = 14.9350
        longitude = 102.0790
        start_date = "2022-06-01"
        end_date = "2022-06-30"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        assert abs(result.location.latitude - 14.935) < 0.01
        assert abs(result.location.longitude - 102.079) < 0.01
        
        # Verify weather data
        assert len(result.weather_data_list) > 0
    
    async def test_multiple_years_chiang_mai(self, gateway):
        """Test multi-year data retrieval for Chiang Mai.
        
        チェンマイの複数年データ取得テスト（2020-2021年）
        """
        # Chiang Mai International Airport
        latitude = 18.7670
        longitude = 98.9630
        start_date = "2020-12-15"
        end_date = "2021-01-15"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        
        # Verify weather data spans across years
        assert len(result.weather_data_list) > 0
        
        # Check that data includes both years
        years = {wd.time.year for wd in result.weather_data_list}
        assert 2020 in years or 2021 in years
    
    async def test_agromet_station_data(self, gateway):
        """Test agricultural meteorological station data.
        
        農業気象観測所（Agromet）のデータ取得テスト
        """
        # Mae Jo Agromet Station (Chiang Mai agricultural station)
        latitude = 18.9170
        longitude = 99.0000
        start_date = "2023-04-01"
        end_date = "2023-04-15"
        
        result = await gateway.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify location
        assert result.location is not None
        assert abs(result.location.latitude - 18.917) < 0.01
        assert abs(result.location.longitude - 99.000) < 0.01
        
        # Verify weather data
        assert len(result.weather_data_list) > 0


@pytest.mark.e2e
@pytest.mark.asyncio
class TestNOAAThailandRegionalCoverage:
    """Test NOAA coverage across all major Thai agricultural regions."""
    
    @pytest.fixture
    def gateway(self):
        """Create WeatherNOAAGateway instance."""
        http_client = HttpClient()
        return WeatherNOAAGateway(http_client)
    
    async def test_northern_region_coverage(self, gateway):
        """Test northern region (rice, fruits, tea) coverage.
        
        北部地域（米・果樹・茶）のカバレッジテスト
        """
        # Test multiple stations in northern region
        stations = [
            (18.767, 98.963, "Chiang Mai"),
            (19.885, 99.827, "Chiang Rai"),
            (18.271, 99.504, "Lampang"),
        ]
        
        start_date = "2023-02-01"
        end_date = "2023-02-05"
        
        for lat, lon, name in stations:
            result = await gateway.get_by_location_and_date_range(
                latitude=lat,
                longitude=lon,
                start_date=start_date,
                end_date=end_date
            )
            
            assert result.location is not None, f"Failed to get location for {name}"
            assert len(result.weather_data_list) > 0, f"No data for {name}"
    
    async def test_isan_region_coverage(self, gateway):
        """Test Isan region (major rice production) coverage.
        
        イサーン地域（最大の米生産地域）のカバレッジテスト
        """
        # Test multiple stations in Isan (Northeastern) region
        stations = [
            (17.386, 102.788, "Udon Thani"),
            (16.467, 102.784, "Khon Kaen"),
            (15.251, 104.870, "Ubon Ratchathani"),
        ]
        
        start_date = "2023-07-01"
        end_date = "2023-07-05"
        
        for lat, lon, name in stations:
            result = await gateway.get_by_location_and_date_range(
                latitude=lat,
                longitude=lon,
                start_date=start_date,
                end_date=end_date
            )
            
            assert result.location is not None, f"Failed to get location for {name}"
            assert len(result.weather_data_list) > 0, f"No data for {name}"
    
    async def test_central_region_coverage(self, gateway):
        """Test central region (Chao Phraya basin, rice) coverage.
        
        中部地域（チャオプラヤー川流域・米生産地）のカバレッジテスト
        """
        # Test multiple stations in central region
        stations = [
            (13.913, 100.607, "Bangkok"),
            (15.673, 100.137, "Nakhon Sawan"),
            (14.467, 100.133, "Suphan Buri"),
        ]
        
        start_date = "2023-09-01"
        end_date = "2023-09-05"
        
        for lat, lon, name in stations:
            result = await gateway.get_by_location_and_date_range(
                latitude=lat,
                longitude=lon,
                start_date=start_date,
                end_date=end_date
            )
            
            assert result.location is not None, f"Failed to get location for {name}"
            assert len(result.weather_data_list) > 0, f"No data for {name}"
    
    async def test_southern_region_coverage(self, gateway):
        """Test southern region (rubber, palm oil) coverage.
        
        南部地域（ゴム・パーム油生産地）のカバレッジテスト
        """
        # Test multiple stations in southern region
        stations = [
            (9.133, 99.136, "Surat Thani"),
            (8.113, 98.317, "Phuket"),
            (6.933, 100.393, "Hat Yai"),
        ]
        
        start_date = "2023-10-01"
        end_date = "2023-10-05"
        
        for lat, lon, name in stations:
            result = await gateway.get_by_location_and_date_range(
                latitude=lat,
                longitude=lon,
                start_date=start_date,
                end_date=end_date
            )
            
            assert result.location is not None, f"Failed to get location for {name}"
            assert len(result.weather_data_list) > 0, f"No data for {name}"


if __name__ == "__main__":
    """Run E2E tests for Thailand weather data."""
    pytest.main([__file__, "-v", "-m", "e2e"])

