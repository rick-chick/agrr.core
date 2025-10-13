"""Unified dependency injection container for agrr.core application."""

import asyncio
from typing import Dict, Any, Optional

from agrr_core.adapter.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository
from agrr_core.adapter.repositories.weather_jma_repository import WeatherJMARepository
from agrr_core.framework.repositories.file_repository import FileRepository
from agrr_core.framework.repositories.http_client import HttpClient
from agrr_core.framework.repositories.html_table_fetcher import HtmlTableFetcher
from agrr_core.adapter.gateways.weather_gateway_impl import WeatherGatewayImpl
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.adapter.controllers.weather_cli_controller import WeatherCliFetchController
from agrr_core.adapter.controllers.weather_cli_predict_controller import WeatherCliPredictController
from agrr_core.adapter.repositories.weather_file_repository import WeatherFileRepository
from agrr_core.usecase.interactors.weather_predict_interactor import WeatherPredictInteractor
from agrr_core.adapter.gateways.prediction_gateway_impl import PredictionGatewayImpl
from agrr_core.adapter.services.prediction_arima_service import PredictionARIMAService
from agrr_core.adapter.interfaces.time_series_interface import TimeSeriesInterface
from agrr_core.framework.services.time_series_arima_service import TimeSeriesARIMAService
from agrr_core.usecase.interactors.weather_fetch_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.interactors.prediction_multi_metric_interactor import MultiMetricPredictionInteractor
from agrr_core.usecase.interactors.prediction_evaluate_interactor import ModelEvaluationInteractor
from agrr_core.usecase.interactors.prediction_batch_interactor import BatchPredictionInteractor
from agrr_core.usecase.interactors.prediction_manage_interactor import ModelManagementInteractor
from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway


class AgrrCoreContainer:
    """Unified dependency injection container for agrr.core application."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize container with configuration."""
        self.config = config or {}
        self._instances = {}
    
    # Weather Repository Management

    def get_file_repository_impl(self) -> FileRepository:
        """Get file repository implementation instance."""
        if 'file_repository_impl' not in self._instances:
            self._instances['file_repository_impl'] = FileRepository()
        return self._instances['file_repository_impl']

    def get_http_service_impl(self) -> HttpClient:
        """Get HTTP service implementation instance."""
        if 'http_service_impl' not in self._instances:
            base_url = self.config.get('open_meteo_base_url', 'https://archive-api.open-meteo.com/v1/archive')
            self._instances['http_service_impl'] = HttpClient(base_url=base_url)
        return self._instances['http_service_impl']
    
    def get_forecast_http_service_impl(self) -> HttpClient:
        """Get forecast HTTP service implementation instance."""
        if 'forecast_http_service_impl' not in self._instances:
            base_url = self.config.get('open_meteo_forecast_base_url', 'https://api.open-meteo.com/v1/forecast')
            self._instances['forecast_http_service_impl'] = HttpClient(base_url=base_url)
        return self._instances['forecast_http_service_impl']

    def get_weather_repository(self) -> WeatherGateway:
        """Get weather repository instance."""
        return self.get_weather_gateway_impl()

    def get_weather_gateway_impl(self) -> WeatherGatewayImpl:
        """Get weather gateway instance."""
        if 'weather_gateway' not in self._instances:
            weather_file_repository = self.get_weather_file_repository()
            
            # Get appropriate weather API repository based on data source
            data_source = self.config.get('weather_data_source', 'openmeteo')
            
            if data_source == 'jma':
                weather_api_repository = self.get_weather_jma_repository()
            else:
                weather_api_repository = self.get_weather_api_repository()
            
            self._instances['weather_gateway'] = WeatherGatewayImpl(
                weather_file_repository=weather_file_repository,
                weather_api_repository=weather_api_repository
            )
        
        return self._instances['weather_gateway']
    
    # CLI Components
    def get_cli_presenter(self) -> WeatherCLIPresenter:
        """Get CLI presenter instance."""
        if 'cli_presenter' not in self._instances:
            self._instances['cli_presenter'] = WeatherCLIPresenter()
        return self._instances['cli_presenter']
    
    def get_fetch_weather_interactor(self) -> FetchWeatherDataInteractor:
        """Get fetch weather interactor instance."""
        if 'fetch_weather_interactor' not in self._instances:
            weather_gateway = self.get_weather_gateway()
            cli_presenter = self.get_cli_presenter()
            self._instances['fetch_weather_interactor'] = FetchWeatherDataInteractor(
                weather_gateway=weather_gateway,
                weather_presenter_output_port=cli_presenter
            )
        return self._instances['fetch_weather_interactor']
    
    def get_cli_controller(self) -> WeatherCliFetchController:
        """Get CLI controller instance."""
        if 'cli_controller' not in self._instances:
            weather_gateway = self.get_weather_gateway_impl()  # ← 修正: data_source対応版を使用
            cli_presenter = self.get_cli_presenter()
            self._instances['cli_controller'] = WeatherCliFetchController(
                weather_gateway=weather_gateway,
                cli_presenter=cli_presenter
            )
        return self._instances['cli_controller']
    
    def get_weather_file_repository(self) -> WeatherFileRepository:
        """Get weather file repository instance."""
        if 'weather_file_repository' not in self._instances:
            file_repository_impl = self.get_file_repository_impl()
            self._instances['weather_file_repository'] = WeatherFileRepository(file_repository_impl)
        return self._instances['weather_file_repository']
    
    def get_time_series_service(self) -> TimeSeriesInterface:
        """Get time series service instance."""
        if 'time_series_service' not in self._instances:
            self._instances['time_series_service'] = TimeSeriesARIMAService()
        return self._instances['time_series_service']
    
    def get_prediction_arima_service(self) -> PredictionARIMAService:
        """Get ARIMA prediction service instance."""
        if 'prediction_arima_service' not in self._instances:
            time_series_service = self.get_time_series_service()
            self._instances['prediction_arima_service'] = PredictionARIMAService(time_series_service)
        return self._instances['prediction_arima_service']
    
    def get_weather_api_repository(self) -> WeatherAPIOpenMeteoRepository:
        """Get weather API repository instance."""
        if 'weather_api_repository' not in self._instances:
            http_service_impl = self.get_http_service_impl()
            forecast_http_service_impl = self.get_forecast_http_service_impl()
            self._instances['weather_api_repository'] = WeatherAPIOpenMeteoRepository(
                http_service_impl, 
                forecast_http_service_impl
            )
        return self._instances['weather_api_repository']
    
    def get_html_table_fetcher(self) -> HtmlTableFetcher:
        """Get HTML table fetcher instance."""
        if 'html_table_fetcher' not in self._instances:
            timeout = self.config.get('html_fetch_timeout', 30)
            self._instances['html_table_fetcher'] = HtmlTableFetcher(timeout=timeout)
        return self._instances['html_table_fetcher']
    
    def get_weather_jma_repository(self) -> WeatherJMARepository:
        """Get JMA weather repository instance."""
        if 'weather_jma_repository' not in self._instances:
            html_table_fetcher = self.get_html_table_fetcher()
            self._instances['weather_jma_repository'] = WeatherJMARepository(html_table_fetcher)
        return self._instances['weather_jma_repository']
    
    def get_weather_gateway(self) -> WeatherGateway:
        """Get weather gateway instance."""
        if 'weather_gateway' not in self._instances:
            weather_file_repository = self.get_weather_file_repository()
            weather_api_repository = self.get_weather_api_repository()
            self._instances['weather_gateway'] = WeatherGatewayImpl(
                weather_file_repository=weather_file_repository,
                weather_api_repository=weather_api_repository
            )
        return self._instances['weather_gateway']
    
    def get_prediction_gateway(self) -> PredictionGatewayImpl:
        """Get prediction gateway instance."""
        if 'prediction_gateway' not in self._instances:
            file_repository = self.get_weather_file_repository()
            prediction_service = self.get_prediction_arima_service()
            self._instances['prediction_gateway'] = PredictionGatewayImpl(
                file_repository=file_repository,
                prediction_service=prediction_service
            )
        return self._instances['prediction_gateway']
    
    def get_weather_predict_interactor(self) -> WeatherPredictInteractor:
        """Get weather prediction interactor instance."""
        if 'weather_predict_interactor' not in self._instances:
            weather_gateway = self.get_weather_gateway()
            prediction_gateway = self.get_prediction_gateway()
            self._instances['weather_predict_interactor'] = WeatherPredictInteractor(
                weather_gateway=weather_gateway,
                prediction_gateway=prediction_gateway
            )
        return self._instances['weather_predict_interactor']
    
    def get_file_predict_cli_controller(self) -> WeatherCliPredictController:
        """Get file-based prediction CLI controller instance."""
        if 'file_predict_cli_controller' not in self._instances:
            weather_gateway = self.get_weather_gateway()
            prediction_gateway = self.get_prediction_gateway()
            cli_presenter = self.get_cli_presenter()
            self._instances['file_predict_cli_controller'] = WeatherCliPredictController(
                weather_gateway=weather_gateway,
                prediction_gateway=prediction_gateway,
                cli_presenter=cli_presenter
            )
        return self._instances['file_predict_cli_controller']
    
    # Prediction Components
    def get_multi_metric_prediction_input_port(self) -> MultiMetricPredictionInteractor:
        """Get multi-metric prediction input port instance."""
        if 'multi_metric_prediction_input_port' not in self._instances:
            weather_repository = self.get_weather_repository()
            prediction_presenter = self.get_prediction_presenter_output_port()
            self._instances['multi_metric_prediction_input_port'] = MultiMetricPredictionInteractor(
                weather_data_gateway=weather_repository,
                weather_data_repository_gateway=weather_repository,
                prediction_service_gateway=weather_repository,
                prediction_presenter_output_port=prediction_presenter
            )
        return self._instances['multi_metric_prediction_input_port']
    
    def get_model_evaluation_input_port(self) -> ModelEvaluationInteractor:
        """Get model evaluation input port instance."""
        if 'model_evaluation_input_port' not in self._instances:
            weather_repository = self.get_weather_repository()
            prediction_presenter = self.get_prediction_presenter_output_port()
            self._instances['model_evaluation_input_port'] = ModelEvaluationInteractor(
                prediction_service_gateway=weather_repository,
                prediction_presenter_output_port=prediction_presenter
            )
        return self._instances['model_evaluation_input_port']
    
    def get_batch_prediction_input_port(self) -> BatchPredictionInteractor:
        """Get batch prediction input port instance."""
        if 'batch_prediction_input_port' not in self._instances:
            weather_repository = self.get_weather_repository()
            prediction_presenter = self.get_prediction_presenter_output_port()
            self._instances['batch_prediction_input_port'] = BatchPredictionInteractor(
                weather_data_gateway=weather_repository,
                prediction_service_gateway=weather_repository,
                prediction_presenter_output_port=prediction_presenter
            )
        return self._instances['batch_prediction_input_port']
    
    def get_model_management_input_port(self) -> ModelManagementInteractor:
        """Get model management input port instance."""
        if 'model_management_input_port' not in self._instances:
            weather_repository = self.get_weather_repository()
            prediction_presenter = self.get_prediction_presenter_output_port()
            self._instances['model_management_input_port'] = ModelManagementInteractor(
                prediction_service_gateway=weather_repository,
                prediction_presenter_output_port=prediction_presenter
            )
        return self._instances['model_management_input_port']
    
    def get_prediction_presenter_output_port(self) -> PredictionPresenterOutputPort:
        """Get prediction presenter output port instance."""
        if 'prediction_presenter_output_port' not in self._instances:
            from agrr_core.adapter.presenters.prediction_presenter import PredictionPresenter
            self._instances['prediction_presenter_output_port'] = PredictionPresenter()
        return self._instances['prediction_presenter_output_port']
    
    
    
    # Service Components
    
    
    # Utility Methods
    
    # Application Entry Points
    async def run_cli(self, args: list = None) -> None:
        """Run CLI application with dependency injection."""
        controller = self.get_cli_controller()
        await controller.run(args)
    
    async def run_prediction_cli(self, args: list = None) -> None:
        """Run file-based prediction CLI application with dependency injection."""
        controller = self.get_file_predict_cli_controller()
        await controller.run(args)
    


# Backward Compatibility Classes
class WeatherCliContainer(AgrrCoreContainer):
    """Weather CLI container for backward compatibility."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
    
    def get_weather_repository(self) -> WeatherGateway:
        """Get weather repository instance with CLI defaults."""
        return self.get_weather_gateway_impl()


class PredictionContainer(AgrrCoreContainer):
    """Prediction container for backward compatibility."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
    
    def get_weather_repository(self) -> WeatherGateway:
        """Get weather repository instance with prediction defaults."""
        return self.get_weather_gateway_impl()
