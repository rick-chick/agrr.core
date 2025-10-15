"""Tests for CLI container."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from agrr_core.framework.agrr_core_container import AgrrCoreContainer, WeatherCliContainer


class TestWeatherCliContainer:
    """Test cases for weather CLI container."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'open_meteo_base_url': 'https://test-api.open-meteo.com/v1/archive'
        }
        self.container = WeatherCliContainer(self.config)
    
    def test_get_weather_repository(self):
        """Test getting weather repository instance."""
        repo = self.container.get_weather_repository()
        
        assert repo is not None
        assert hasattr(repo, 'file_gateway')
        assert hasattr(repo, 'api_gateway')
        
        # Test singleton behavior
        repo2 = self.container.get_weather_repository()
        assert repo is repo2
    
    def test_get_cli_presenter(self):
        """Test getting CLI presenter instance."""
        presenter = self.container.get_cli_presenter()
        
        assert presenter is not None
        
        # Test singleton behavior
        presenter2 = self.container.get_cli_presenter()
        assert presenter is presenter2
    
    def test_get_fetch_weather_interactor(self):
        """Test getting fetch weather interactor instance."""
        interactor = self.container.get_fetch_weather_interactor()
        
        assert interactor is not None
        assert interactor.weather_gateway is not None
        assert interactor.weather_presenter_output_port is not None
        
        # Test singleton behavior
        interactor2 = self.container.get_fetch_weather_interactor()
        assert interactor is interactor2
    
    def test_get_cli_controller(self):
        """Test getting CLI controller instance."""
        controller = self.container.get_cli_controller()
        
        assert controller is not None
        assert controller.weather_gateway is not None
        assert controller.cli_presenter is not None
        
        # Test singleton behavior
        controller2 = self.container.get_cli_controller()
        assert controller is controller2
    
    @pytest.mark.asyncio
    async def test_run_cli(self):
        """Test running CLI application."""
        # Mock the controller's run method
        mock_controller = MagicMock()
        mock_controller.run = AsyncMock()
        
        with patch.object(self.container, 'get_cli_controller', return_value=mock_controller):
            await self.container.run_cli(['weather', '--location', '35.6762,139.6503'])
            
            mock_controller.run.assert_called_once_with(['weather', '--location', '35.6762,139.6503'])
    
    def test_container_without_config(self):
        """Test container initialization without config."""
        container = WeatherCliContainer()
        
        # Should use default config
        repo = container.get_weather_repository()
        assert repo is not None
        assert hasattr(repo, 'file_gateway')
        assert hasattr(repo, 'api_gateway')
    
    def test_get_time_series_service(self):
        """Test getting time series service instance."""
        service = self.container.get_time_series_service()
        
        assert service is not None
        assert hasattr(service, 'create_model')
        assert hasattr(service, 'check_stationarity')
        assert hasattr(service, 'make_stationary')
        
        # Test singleton behavior
        service2 = self.container.get_time_series_service()
        assert service is service2
    
    def test_get_prediction_arima_service(self):
        """Test getting ARIMA prediction service instance."""
        service = self.container.get_prediction_arima_service()
        
        assert service is not None
        assert hasattr(service, 'time_series_service')
        assert hasattr(service, 'predict_multiple_metrics')
        assert hasattr(service, '_predict_single_metric')
        
        # Test singleton behavior
        service2 = self.container.get_prediction_arima_service()
        assert service is service2
    
    def test_get_prediction_arima_service_dependency_injection(self):
        """Test that prediction service gets time series service injected."""
        service = self.container.get_prediction_arima_service()
        time_series_service = self.container.get_time_series_service()
        
        assert service.time_series_service is time_series_service