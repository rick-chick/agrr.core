"""Unified dependency injection container for agrr.core application."""

import asyncio
from typing import Dict, Any, Optional

from agrr_core.framework.services.io.file_service import FileService
from agrr_core.framework.services.clients.http_client import HttpClient
from agrr_core.framework.services.io.html_table_service import HtmlTableService
from agrr_core.framework.services.io.csv_service import CsvService
from agrr_core.adapter.gateways.weather_api_gateway import WeatherAPIGateway
from agrr_core.adapter.gateways.weather_jma_gateway import WeatherJMAGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.weather_gateway_adapter import WeatherGatewayAdapter
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.adapter.controllers.weather_cli_controller import WeatherCliFetchController
from agrr_core.adapter.controllers.weather_cli_predict_controller import WeatherCliPredictController
from agrr_core.usecase.interactors.weather_predict_interactor import WeatherPredictInteractor
from agrr_core.adapter.gateways.prediction_gateway_impl import PredictionGatewayImpl
from agrr_core.framework.services.ml.arima_prediction_service import ARIMAPredictionService
from agrr_core.framework.services.ml.time_series_arima_service import TimeSeriesARIMAService
from agrr_core.usecase.interactors.weather_fetch_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.interactors.prediction_multi_metric_interactor import MultiMetricPredictionInteractor
from agrr_core.usecase.interactors.prediction_evaluate_interactor import ModelEvaluationInteractor
from agrr_core.usecase.interactors.prediction_batch_interactor import BatchPredictionInteractor
from agrr_core.usecase.interactors.prediction_manage_interactor import ModelManagementInteractor
from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.adapter.interfaces.ml.time_series_service_interface import TimeSeriesServiceInterface


class AgrrCoreContainer:
    """Unified dependency injection container for agrr.core application."""
    
    def __init__(self, config: Dict[str, Any] = None, weather_file_path: str = ""):
        """Initialize container with configuration.
        
        Args:
            config: Configuration dictionary
            weather_file_path: Path to weather data file (optional, for file-based operations)
        """
        self.config = config or {}
        self.weather_file_path = weather_file_path
        self._instances = {}
    
    # Weather Repository Management

    def get_file_repository_impl(self) -> FileService:
        """Get file service implementation instance."""
        if 'file_repository_impl' not in self._instances:
            self._instances['file_repository_impl'] = FileService()
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

    def get_weather_gateway_impl(self) -> WeatherGatewayAdapter:
        """Get weather gateway adapter instance."""
        if 'weather_gateway' not in self._instances:
            weather_file_gateway = self.get_weather_file_gateway()
            
            # Get appropriate weather API gateway based on data source
            data_source = self.config.get('weather_data_source', 'openmeteo')
            
            if data_source == 'jma':
                weather_api_gateway = self.get_weather_jma_gateway()
            else:
                weather_api_gateway = self.get_weather_api_gateway()
            
            self._instances['weather_gateway'] = WeatherGatewayAdapter(
                file_gateway=weather_file_gateway,
                api_gateway=weather_api_gateway
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
    
    def get_weather_file_gateway(self) -> WeatherFileGateway:
        """Get weather file gateway instance.
        
        Note: Uses weather_file_path from container initialization.
        """
        if 'weather_file_gateway' not in self._instances:
            file_repository_impl = self.get_file_repository_impl()
            self._instances['weather_file_gateway'] = WeatherFileGateway(
                file_repository_impl, 
                file_path=self.weather_file_path
            )
        return self._instances['weather_file_gateway']
    
    def get_time_series_service(self) -> TimeSeriesServiceInterface:
        """Get time series service instance."""
        if 'time_series_service' not in self._instances:
            self._instances['time_series_service'] = TimeSeriesARIMAService()
        return self._instances['time_series_service']
    
    def get_prediction_arima_service(self) -> ARIMAPredictionService:
        """Get ARIMA prediction service instance (Framework layer)."""
        if 'prediction_arima_service' not in self._instances:
            time_series_service = self.get_time_series_service()
            self._instances['prediction_arima_service'] = ARIMAPredictionService(time_series_service)
        return self._instances['prediction_arima_service']
    
    def get_prediction_lightgbm_service(self):
        """Get LightGBM prediction service instance."""
        if 'prediction_lightgbm_service' not in self._instances:
            from agrr_core.framework.services.ml.lightgbm_prediction_service import LightGBMPredictionService
            self._instances['prediction_lightgbm_service'] = LightGBMPredictionService()
        return self._instances['prediction_lightgbm_service']
    
    def get_weather_api_gateway(self) -> WeatherAPIGateway:
        """Get weather API gateway instance."""
        if 'weather_api_gateway' not in self._instances:
            http_service_impl = self.get_http_service_impl()
            forecast_http_service_impl = self.get_forecast_http_service_impl()
            self._instances['weather_api_gateway'] = WeatherAPIGateway(
                http_service_impl, 
                forecast_http_service_impl
            )
        return self._instances['weather_api_gateway']
    
    def get_html_table_fetcher(self) -> HtmlTableService:
        """Get HTML table service instance."""
        if 'html_table_fetcher' not in self._instances:
            timeout = self.config.get('html_fetch_timeout', 30)
            self._instances['html_table_fetcher'] = HtmlTableService(timeout=timeout)
        return self._instances['html_table_fetcher']
    
    def get_csv_downloader(self) -> CsvService:
        """Get CSV service instance."""
        if 'csv_downloader' not in self._instances:
            timeout = self.config.get('csv_download_timeout', 30)
            self._instances['csv_downloader'] = CsvService(timeout=timeout)
        return self._instances['csv_downloader']
    
    def get_weather_jma_gateway(self) -> WeatherJMAGateway:
        """Get JMA weather gateway instance."""
        if 'weather_jma_gateway' not in self._instances:
            html_table_fetcher = self.get_html_table_fetcher()
            self._instances['weather_jma_gateway'] = WeatherJMAGateway(html_table_fetcher)
        return self._instances['weather_jma_gateway']
    
    def get_weather_gateway(self) -> WeatherGateway:
        """Get weather gateway instance."""
        return self.get_weather_gateway_impl()
    
    def get_prediction_gateway(self, model_type: str = 'arima') -> PredictionGatewayImpl:
        """
        Get prediction gateway instance with specified model.
        
        Args:
            model_type: 'arima' or 'lightgbm' (default: 'arima')
        """
        # Don't cache - create new instance based on model_type
        file_gateway = self.get_weather_file_gateway()
        
        if model_type == 'lightgbm':
            prediction_service = self.get_prediction_lightgbm_service()
        else:  # default to arima
            prediction_service = self.get_prediction_arima_service()
        
        return PredictionGatewayImpl(
            file_repository=file_gateway,
            prediction_service=prediction_service
        )
    
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
        """
        Run file-based prediction CLI application with dependency injection.
        
        Extracts --model option from args and injects appropriate service.
        """
        # Extract model type from args
        model_type = 'arima'  # default
        if args and '--model' in args:
            try:
                model_index = args.index('--model')
                if model_index + 1 < len(args):
                    model_type = args[model_index + 1]
            except (ValueError, IndexError):
                pass
        elif args and '-m' in args:
            try:
                model_index = args.index('-m')
                if model_index + 1 < len(args):
                    model_type = args[model_index + 1]
            except (ValueError, IndexError):
                pass
        
        # Create controller with appropriate service injected
        weather_gateway = self.get_weather_gateway()
        prediction_gateway = self.get_prediction_gateway(model_type=model_type)  # ← モデルを指定
        cli_presenter = self.get_cli_presenter()
        
        controller = WeatherCliPredictController(
            weather_gateway=weather_gateway,
            prediction_gateway=prediction_gateway,
            cli_presenter=cli_presenter
        )
        
        await controller.run(args)
    


# Backward Compatibility Classes
class WeatherCliContainer(AgrrCoreContainer):
    """Weather CLI container for backward compatibility."""
    
    def __init__(self, config: Dict[str, Any] = None, weather_file_path: str = ""):
        super().__init__(config, weather_file_path)
    
    def get_weather_repository(self) -> WeatherGateway:
        """Get weather repository instance with CLI defaults."""
        return self.get_weather_gateway_impl()


class PredictionContainer(AgrrCoreContainer):
    """Prediction container for backward compatibility."""
    
    def __init__(self, config: Dict[str, Any] = None, weather_file_path: str = ""):
        super().__init__(config, weather_file_path)
    
    def get_weather_repository(self) -> WeatherGateway:
        """Get weather repository instance with prediction defaults."""
        return self.get_weather_gateway_impl()
