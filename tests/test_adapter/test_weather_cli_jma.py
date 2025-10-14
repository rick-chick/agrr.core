"""Tests for CLI with JMA data source."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import pandas as pd

from agrr_core.framework.agrr_core_container import WeatherCliContainer, AgrrCoreContainer
from agrr_core.framework.repositories.weather_jma_repository import WeatherJMARepository
from agrr_core.framework.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository


class TestWeatherCLIWithJMA:
    """Test CLI with JMA data source option."""
    
    def test_container_config_openmeteo_default(self):
        """Test that default data source is openmeteo."""
        config = {}
        container = AgrrCoreContainer(config)
        
        # Should use OpenMeteo by default
        weather_gateway = container.get_weather_gateway_impl()
        assert weather_gateway is not None
        
        # Check that OpenMeteo repository is created
        openmeteo_repo = container.get_weather_api_repository()
        assert isinstance(openmeteo_repo, WeatherAPIOpenMeteoRepository)
    
    def test_container_config_jma(self):
        """Test that JMA data source can be configured."""
        config = {
            'weather_data_source': 'jma'
        }
        container = AgrrCoreContainer(config)
        
        # Should use JMA when configured
        jma_repo = container.get_weather_jma_repository()
        assert isinstance(jma_repo, WeatherJMARepository)
    
    def test_container_csv_downloader_creation(self):
        """Test CSV downloader is created correctly."""
        config = {
            'csv_download_timeout': 60
        }
        container = AgrrCoreContainer(config)
        
        csv_downloader = container.get_csv_downloader()
        assert csv_downloader is not None
        assert csv_downloader.timeout == 60
    
    def test_weather_cli_container_with_jma(self):
        """Test WeatherCliContainer with JMA configuration."""
        config = {
            'weather_data_source': 'jma'
        }
        container = WeatherCliContainer(config)
        
        # Should inherit JMA configuration
        weather_repo = container.get_weather_repository()
        assert weather_repo is not None
    
    def test_data_source_switching(self):
        """Test that data source can be switched via config."""
        # Test OpenMeteo
        config_openmeteo = {'weather_data_source': 'openmeteo'}
        container1 = AgrrCoreContainer(config_openmeteo)
        
        # Create gateway - should use OpenMeteo
        gateway1 = container1.get_weather_gateway_impl()
        assert gateway1 is not None
        
        # Test JMA
        config_jma = {'weather_data_source': 'jma'}
        container2 = AgrrCoreContainer(config_jma)
        
        # Create gateway - should use JMA
        gateway2 = container2.get_weather_gateway_impl()
        assert gateway2 is not None
        
        # Gateways should be different instances
        assert gateway1 is not gateway2


class TestCLIArgumentParsing:
    """Test CLI argument parsing for data-source option."""
    
    @pytest.mark.asyncio
    async def test_cli_weather_with_data_source_jma(self):
        """Test that --data-source jma is accepted."""
        from agrr_core.adapter.controllers.weather_cli_controller import WeatherCliFetchController
        from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
        from agrr_core.adapter.gateways.weather_gateway_impl import WeatherGatewayImpl
        from agrr_core.framework.repositories.weather_file_repository import WeatherFileRepository
        from agrr_core.framework.repositories.file_repository import FileRepository
        from agrr_core.framework.repositories.csv_downloader import CsvDownloader
        
        # Create mocked components
        file_repo = FileRepository()
        weather_file_repo = WeatherFileRepository(file_repo, "test_weather.json")
        csv_downloader = CsvDownloader()
        jma_repo = WeatherJMARepository(csv_downloader)
        
        weather_gateway = WeatherGatewayImpl(
            weather_repository=weather_file_repo,
            weather_api_repository=jma_repo
        )
        presenter = WeatherCLIPresenter()
        
        controller = WeatherCliFetchController(
            weather_gateway=weather_gateway,
            cli_presenter=presenter
        )
        
        # Create parser and parse args
        parser = controller.create_argument_parser()
        
        # Test that data-source option is accepted
        args = parser.parse_args([
            'weather',
            '--location', '35.6895,139.6917',
            '--days', '7',
            '--data-source', 'jma'
        ])
        
        assert args.command == 'weather'
        assert args.data_source == 'jma'
        assert args.location == '35.6895,139.6917'
        assert args.days == 7
    
    @pytest.mark.asyncio
    async def test_cli_weather_data_source_default(self):
        """Test that data-source defaults to openmeteo."""
        from agrr_core.adapter.controllers.weather_cli_controller import WeatherCliFetchController
        from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
        from agrr_core.adapter.gateways.weather_gateway_impl import WeatherGatewayImpl
        from agrr_core.framework.repositories.weather_file_repository import WeatherFileRepository
        from agrr_core.framework.repositories.file_repository import FileRepository
        from agrr_core.framework.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository
        from agrr_core.framework.repositories.http_client import HttpClient
        
        # Create mocked components
        file_repo = FileRepository()
        weather_file_repo = WeatherFileRepository(file_repo, "test_weather.json")
        http_client = HttpClient("https://test.com")
        openmeteo_repo = WeatherAPIOpenMeteoRepository(http_client)
        
        weather_gateway = WeatherGatewayImpl(
            weather_repository=weather_file_repo,
            weather_api_repository=openmeteo_repo
        )
        presenter = WeatherCLIPresenter()
        
        controller = WeatherCliFetchController(
            weather_gateway=weather_gateway,
            cli_presenter=presenter
        )
        
        # Create parser and parse args (no --data-source specified)
        parser = controller.create_argument_parser()
        
        args = parser.parse_args([
            'weather',
            '--location', '35.6895,139.6917',
            '--days', '7'
        ])
        
        # Should default to openmeteo
        assert args.data_source == 'openmeteo'
    
    def test_data_source_choices_validation(self):
        """Test that only valid data sources are accepted."""
        from agrr_core.adapter.controllers.weather_cli_controller import WeatherCliFetchController
        from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
        from agrr_core.adapter.gateways.weather_gateway_impl import WeatherGatewayImpl
        from agrr_core.framework.repositories.weather_file_repository import WeatherFileRepository
        from agrr_core.framework.repositories.file_repository import FileRepository
        from agrr_core.framework.repositories.http_client import HttpClient
        from agrr_core.framework.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository
        
        # Create mocked components
        file_repo = FileRepository()
        weather_file_repo = WeatherFileRepository(file_repo, "test_weather.json")
        http_client = HttpClient("https://test.com")
        openmeteo_repo = WeatherAPIOpenMeteoRepository(http_client)
        
        weather_gateway = WeatherGatewayImpl(
            weather_repository=weather_file_repo,
            weather_api_repository=openmeteo_repo
        )
        presenter = WeatherCLIPresenter()
        
        controller = WeatherCliFetchController(
            weather_gateway=weather_gateway,
            cli_presenter=presenter
        )
        
        parser = controller.create_argument_parser()
        
        # Invalid data source should raise error
        with pytest.raises(SystemExit):
            parser.parse_args([
                'weather',
                '--location', '35.6895,139.6917',
                '--data-source', 'invalid'
            ])

