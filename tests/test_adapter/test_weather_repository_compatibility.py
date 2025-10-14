"""Test compatibility between OpenMeteo and JMA repositories.

This test verifies that both repositories implement the same interface
and can be used interchangeably in the system.
"""

import pytest
import inspect
from unittest.mock import AsyncMock
import pandas as pd

from agrr_core.framework.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository
from agrr_core.framework.repositories.weather_jma_repository import WeatherJMARepository
from agrr_core.framework.interfaces.http_service_interface import HttpServiceInterface
from agrr_core.framework.interfaces.html_table_fetch_interface import HtmlTableFetchInterface
from agrr_core.framework.interfaces.html_table_structures import HtmlTable, TableRow
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO


class TestWeatherRepositoryCompatibility:
    """Test that OpenMeteo and JMA repositories are compatible."""
    
    @pytest.fixture
    def openmeteo_repository(self):
        """Create OpenMeteo repository."""
        mock_http = AsyncMock(spec=HttpServiceInterface)
        return WeatherAPIOpenMeteoRepository(mock_http)
    
    @pytest.fixture
    def jma_repository(self):
        """Create JMA repository."""
        mock_html_fetcher = AsyncMock(spec=HtmlTableFetchInterface)
        return WeatherJMARepository(mock_html_fetcher)
    
    def test_both_have_same_method(self, openmeteo_repository, jma_repository):
        """Test that both repositories have the same main method."""
        method_name = 'get_by_location_and_date_range'
        
        assert hasattr(openmeteo_repository, method_name)
        assert hasattr(jma_repository, method_name)
    
    def test_same_method_signature(self, openmeteo_repository, jma_repository):
        """Test that both repositories have the same method signature."""
        openmeteo_sig = inspect.signature(openmeteo_repository.get_by_location_and_date_range)
        jma_sig = inspect.signature(jma_repository.get_by_location_and_date_range)
        
        openmeteo_params = list(openmeteo_sig.parameters.keys())
        jma_params = list(jma_sig.parameters.keys())
        
        assert openmeteo_params == jma_params, (
            f"Method signatures don't match: "
            f"OpenMeteo={openmeteo_params}, JMA={jma_params}"
        )
        
        # Check parameter names
        assert 'latitude' in openmeteo_params
        assert 'longitude' in openmeteo_params
        assert 'start_date' in openmeteo_params
        assert 'end_date' in openmeteo_params
    
    def test_same_return_type(self, openmeteo_repository, jma_repository):
        """Test that both repositories return the same type."""
        openmeteo_sig = inspect.signature(openmeteo_repository.get_by_location_and_date_range)
        jma_sig = inspect.signature(jma_repository.get_by_location_and_date_range)
        
        # Both should return WeatherDataWithLocationDTO
        assert openmeteo_sig.return_annotation == WeatherDataWithLocationDTO
        assert jma_sig.return_annotation == WeatherDataWithLocationDTO
    
    @pytest.mark.asyncio
    async def test_both_return_compatible_data_structure(self):
        """Test that both repositories return the same data structure."""
        # Setup OpenMeteo mock
        mock_http_openmeteo = AsyncMock(spec=HttpServiceInterface)
        mock_http_openmeteo.get.return_value = {
            'latitude': 35.6895,
            'longitude': 139.6917,
            'elevation': 40.0,
            'timezone': 'Asia/Tokyo',
            'daily': {
                'time': ['2024-01-01', '2024-01-02'],
                'temperature_2m_max': [10.5, 11.2],
                'temperature_2m_min': [2.3, 3.1],
                'temperature_2m_mean': [6.4, 7.2],
                'precipitation_sum': [0.0, 2.5],
                'sunshine_duration': [18720, 11160],  # seconds
                'wind_speed_10m_max': [3.5, 4.2],
                'weather_code': [1, 61],
            }
        }
        openmeteo_repo = WeatherAPIOpenMeteoRepository(mock_http_openmeteo)
        
        # Setup JMA mock with HtmlTable
        mock_html_fetcher_jma = AsyncMock(spec=HtmlTableFetchInterface)
        
        # Helper function to create HtmlTable
        def create_table_row(day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_max):
            cells = [
                str(day), '1013.0', '1023.0',  # day, pressure_local, pressure_sea
                str(precip), '0.0', '0.0',  # precip_sum, precip_1h, precip_10m
                str(temp_mean), str(temp_max), str(temp_min),  # temp_mean, temp_max, temp_min
                '60', '50',  # humidity_avg, humidity_min
                '3.0', str(wind_max),  # wind_avg, wind_max
                '北', '10.0', '0',  # wind_dir, wind_speed, wind_gust
                str(sunshine_h), '0.0', '0.0', '--', '--'  # sunshine, snow, snow_depth, weather, cloud
            ]
            return TableRow(cells=cells)
        
        rows = [
            create_table_row(1, 0.0, 6.4, 10.5, 2.3, 5.2, 3.5),
            create_table_row(2, 2.5, 7.2, 11.2, 3.1, 3.1, 4.2),
        ]
        
        table = HtmlTable(headers=[], rows=rows, table_id='tablefix1')
        mock_html_fetcher_jma.get.return_value = [table]
        jma_repo = WeatherJMARepository(mock_html_fetcher_jma)
        
        # Get data from both
        openmeteo_result = await openmeteo_repo.get_by_location_and_date_range(
            latitude=35.6895,
            longitude=139.6917,
            start_date='2024-01-01',
            end_date='2024-01-02'
        )
        
        jma_result = await jma_repo.get_by_location_and_date_range(
            latitude=35.6895,
            longitude=139.6917,
            start_date='2024-01-01',
            end_date='2024-01-02'
        )
        
        # Both should return WeatherDataWithLocationDTO
        assert isinstance(openmeteo_result, WeatherDataWithLocationDTO)
        assert isinstance(jma_result, WeatherDataWithLocationDTO)
        
        # Both should have location
        assert openmeteo_result.location is not None
        assert jma_result.location is not None
        
        # Both should have weather data list
        assert openmeteo_result.weather_data_list is not None
        assert jma_result.weather_data_list is not None
        assert len(openmeteo_result.weather_data_list) > 0
        assert len(jma_result.weather_data_list) > 0
        
        # Both should have the same fields in WeatherData
        openmeteo_first = openmeteo_result.weather_data_list[0]
        jma_first = jma_result.weather_data_list[0]
        
        assert hasattr(openmeteo_first, 'time')
        assert hasattr(jma_first, 'time')
        assert hasattr(openmeteo_first, 'temperature_2m_max')
        assert hasattr(jma_first, 'temperature_2m_max')
        assert hasattr(openmeteo_first, 'temperature_2m_min')
        assert hasattr(jma_first, 'temperature_2m_min')
        assert hasattr(openmeteo_first, 'temperature_2m_mean')
        assert hasattr(jma_first, 'temperature_2m_mean')
        assert hasattr(openmeteo_first, 'precipitation_sum')
        assert hasattr(jma_first, 'precipitation_sum')
        assert hasattr(openmeteo_first, 'sunshine_duration')
        assert hasattr(jma_first, 'sunshine_duration')
        assert hasattr(openmeteo_first, 'wind_speed_10m')
        assert hasattr(jma_first, 'wind_speed_10m')
        assert hasattr(openmeteo_first, 'weather_code')
        assert hasattr(jma_first, 'weather_code')
        
        # Check values match
        assert jma_first.temperature_2m_max == 10.5
        assert jma_first.temperature_2m_min == 2.3
        assert jma_first.temperature_2m_mean == 6.4
        assert jma_first.precipitation_sum == 0.0
        # JMA converts hours to seconds: 5.2 * 3600 = 18720
        assert jma_first.sunshine_duration == 18720.0
        assert jma_first.wind_speed_10m == 3.5
        # JMA doesn't have weather code
        assert jma_first.weather_code is None
    
    def test_can_be_used_interchangeably(self, openmeteo_repository, jma_repository):
        """
        Test that both repositories can be used interchangeably.
        
        This is the key test for compatibility - if UseCase layer
        uses WeatherGateway interface, it shouldn't matter which
        repository implementation is used.
        """
        repositories = [openmeteo_repository, jma_repository]
        
        for repo in repositories:
            # Both should have the same interface
            assert hasattr(repo, 'get_by_location_and_date_range')
            assert callable(repo.get_by_location_and_date_range)
            
            # Method should be async
            assert inspect.iscoroutinefunction(repo.get_by_location_and_date_range)
    
    def test_data_source_identification(self):
        """
        Test that we can identify which data source was used.
        
        This is useful for logging, debugging, and metrics.
        """
        mock_http = AsyncMock(spec=HttpServiceInterface)
        mock_html_fetcher = AsyncMock(spec=HtmlTableFetchInterface)
        
        openmeteo_repo = WeatherAPIOpenMeteoRepository(mock_http)
        jma_repo = WeatherJMARepository(mock_html_fetcher)
        
        # Check class names for identification
        assert 'OpenMeteo' in openmeteo_repo.__class__.__name__
        assert 'JMA' in jma_repo.__class__.__name__

