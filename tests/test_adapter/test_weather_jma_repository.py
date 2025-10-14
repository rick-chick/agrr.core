"""Tests for Weather JMA Repository."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from agrr_core.framework.repositories.weather_jma_repository import WeatherJMARepository, LOCATION_MAPPING
from agrr_core.framework.interfaces.html_table_fetch_interface import HtmlTableFetchInterface
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError


class TestWeatherJMARepository:
    """Test WeatherJMARepository."""
    
    @pytest.fixture
    def mock_html_table_fetcher(self):
        """Create mock HTML table fetcher."""
        fetcher = AsyncMock(spec=HtmlTableFetchInterface)
        return fetcher
    
    @pytest.fixture
    def repository(self, mock_html_table_fetcher):
        """Create repository instance."""
        return WeatherJMARepository(mock_html_table_fetcher)
    
    def test_find_nearest_location_tokyo(self, repository):
        """Test finding nearest location for Tokyo."""
        # Tokyo coordinates
        latitude = 35.6895
        longitude = 139.6917
        
        prec_no, block_no, name = repository._find_nearest_location(latitude, longitude)
        
        assert prec_no == 44
        assert block_no == 47662
        assert name == "東京"
    
    def test_find_nearest_location_sapporo(self, repository):
        """Test finding nearest location for Sapporo."""
        # Sapporo coordinates
        latitude = 43.0642
        longitude = 141.3469
        
        prec_no, block_no, name = repository._find_nearest_location(latitude, longitude)
        
        assert prec_no == 14
        assert block_no == 47412
        assert name == "札幌"
    
    def test_find_nearest_location_osaka(self, repository):
        """Test finding nearest location for Osaka."""
        # Osaka coordinates
        latitude = 34.6937
        longitude = 135.5023
        
        prec_no, block_no, name = repository._find_nearest_location(latitude, longitude)
        
        assert prec_no == 62
        assert block_no == 47772
        assert name == "大阪"
    
    def test_build_url(self, repository):
        """Test URL building."""
        url = repository._build_url(
            prec_no=44,
            block_no=47662,
            year=2024,
            month=1
        )
        
        assert "https://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php" in url
        assert "prec_no=44" in url
        assert "block_no=47662" in url
        assert "year=2024" in url
        assert "month=1" in url
    
    @pytest.mark.asyncio
    async def test_get_by_location_and_date_range_success(
        self,
        repository,
        mock_html_table_fetcher
    ):
        """Test successful data retrieval (skipped - requires HTML table mock data)."""
        # This test would require complex HTML table mock data
        # Integration tests cover actual HTML table fetching
        pytest.skip("Test requires complex HTML table mock data - covered by integration tests")
    
    @pytest.mark.asyncio
    async def test_location_mapping_coverage(self, repository):
        """Test that all 47 prefectures have location mappings."""
        # 47都道府県すべて
        expected_prefectures = [
            "札幌", "青森", "盛岡", "仙台", "秋田", "山形", "福島",
            "水戸", "宇都宮", "前橋", "熊谷", "千葉", "東京", "横浜",
            "新潟", "富山", "金沢", "福井", "甲府", "長野",
            "岐阜", "静岡", "名古屋", "津",
            "大津", "京都", "大阪", "神戸", "奈良", "和歌山",
            "鳥取", "松江", "岡山", "広島", "下関",
            "徳島", "高松", "松山", "高知",
            "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "那覇",
        ]
        
        mapped_cities = [name for (_, _, name) in LOCATION_MAPPING.values()]
        
        # 47都道府県すべてがマッピングされていることを確認
        assert len(LOCATION_MAPPING) == 47, f"Expected 47 prefectures, got {len(LOCATION_MAPPING)}"
        
        for prefecture in expected_prefectures:
            assert prefecture in mapped_cities, f"Prefecture {prefecture} not in mapping"
    
    def test_all_locations_unique_coordinates(self, repository):
        """Test that all locations have unique coordinates."""
        # すべての座標がユニークであることを確認
        coordinates = list(LOCATION_MAPPING.keys())
        assert len(coordinates) == len(set(coordinates)), "Some locations have duplicate coordinates"
    
    def test_find_nearest_location_for_each_region(self, repository):
        """Test finding nearest location for various regions across Japan (verified locations only)."""
        test_cases = [
            # (lat, lon, expected_name)
            (43.0642, 141.3469, "札幌"),   # 北海道
            (38.2682, 140.8694, "仙台"),   # 東北
            (35.6895, 139.6917, "東京"),   # 関東
            (36.6519, 138.1881, "長野"),   # 中部
            (34.6937, 135.5023, "大阪"),   # 近畿
            (34.3853, 132.4553, "広島"),   # 中国
            (33.5904, 130.4017, "福岡"),   # 九州
            (26.2124, 127.6809, "那覇"),   # 沖縄
        ]
        
        for lat, lon, expected_name in test_cases:
            prec_no, block_no, name = repository._find_nearest_location(lat, lon)
            assert name == expected_name, f"Expected {expected_name}, got {name} for ({lat}, {lon})"
    
    def test_interface_compatibility(self, repository):
        """
        Test that WeatherJMARepository implements the same interface as OpenMeteo repository.
        
        This ensures both repositories can be used interchangeably.
        """
        # Both repositories should have the same method signature
        assert hasattr(repository, 'get_by_location_and_date_range')
        
        # Check method signature
        import inspect
        sig = inspect.signature(repository.get_by_location_and_date_range)
        params = list(sig.parameters.keys())
        
        assert 'latitude' in params
        assert 'longitude' in params
        assert 'start_date' in params
        assert 'end_date' in params

