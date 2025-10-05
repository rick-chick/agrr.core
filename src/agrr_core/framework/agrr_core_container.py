"""Unified dependency injection container for agrr.core application."""

import asyncio
from typing import Dict, Any, Optional

from agrr_core.adapter.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository
from agrr_core.adapter.repositories.weather_storage_repository import WeatherStorageRepository
from agrr_core.adapter.repositories.weather_external_repository import WeatherExternalRepository
from agrr_core.adapter.repositories.weather_memory_repository import WeatherMemoryRepository
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.adapter.controllers.weather_cli_controller import WeatherCLIController
from agrr_core.adapter.services.prediction_integrated_service import PredictionIntegratedService
from agrr_core.usecase.interactors.weather_fetch_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.interactors.prediction_multi_metric_interactor import MultiMetricPredictionInteractor
from agrr_core.usecase.interactors.prediction_evaluate_interactor import ModelEvaluationInteractor
from agrr_core.usecase.interactors.prediction_batch_interactor import BatchPredictionInteractor
from agrr_core.usecase.interactors.prediction_manage_interactor import ModelManagementInteractor
from agrr_core.usecase.gateways.weather_repository_gateway import WeatherRepositoryGateway
from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort


class AgrrCoreContainer:
    """Unified dependency injection container for agrr.core application."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize container with configuration."""
        self.config = config or {}
        self._instances = {}
    
    # Weather Repository Management
    def get_weather_repository(self) -> WeatherRepositoryGateway:
        """Get weather repository instance."""
        if 'weather_repository' not in self._instances:
            repository_type = self.config.get('weather_repository_type', 'api')
            
            if repository_type == 'storage':
                storage_path = self.config.get('storage_path', 'data/weather')
                self._instances['weather_repository'] = WeatherStorageRepository(storage_path=storage_path)
            elif repository_type == 'external':
                fallback_repo = None
                if self.config.get('enable_fallback', False):
                    # Create fallback API repository
                    base_url = self.config.get('open_meteo_base_url', 'https://archive-api.open-meteo.com/v1/archive')
                    fallback_repo = WeatherAPIOpenMeteoRepository(base_url=base_url)
                self._instances['weather_repository'] = WeatherExternalRepository(fallback_repository=fallback_repo)
            elif repository_type == 'memory':
                self._instances['weather_repository'] = WeatherMemoryRepository()
            else:  # Default to API
                base_url = self.config.get('open_meteo_base_url', 'https://archive-api.open-meteo.com/v1/archive')
                self._instances['weather_repository'] = WeatherAPIOpenMeteoRepository(base_url=base_url)
        
        return self._instances['weather_repository']
    
    # CLI Components
    def get_cli_presenter(self) -> WeatherCLIPresenter:
        """Get CLI presenter instance."""
        if 'cli_presenter' not in self._instances:
            self._instances['cli_presenter'] = WeatherCLIPresenter()
        return self._instances['cli_presenter']
    
    def get_fetch_weather_interactor(self) -> FetchWeatherDataInteractor:
        """Get fetch weather interactor instance."""
        if 'fetch_weather_interactor' not in self._instances:
            weather_repository = self.get_weather_repository()
            cli_presenter = self.get_cli_presenter()
            self._instances['fetch_weather_interactor'] = FetchWeatherDataInteractor(
                weather_repository_gateway=weather_repository,
                weather_presenter_output_port=cli_presenter
            )
        return self._instances['fetch_weather_interactor']
    
    def get_cli_controller(self) -> WeatherCLIController:
        """Get CLI controller instance."""
        if 'cli_controller' not in self._instances:
            weather_repository = self.get_weather_repository()
            cli_presenter = self.get_cli_presenter()
            self._instances['cli_controller'] = WeatherCLIController(
                weather_repository=weather_repository,
                cli_presenter=cli_presenter
            )
        return self._instances['cli_controller']
    
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
    
    def get_advanced_prediction_output_port(self) -> AdvancedPredictionOutputPort:
        """Get advanced prediction output port instance."""
        if 'advanced_prediction_output_port' not in self._instances:
            from agrr_core.adapter.presenters.advanced_prediction_presenter import PredictionAdvancedPresenter
            self._instances['advanced_prediction_output_port'] = PredictionAdvancedPresenter()
        return self._instances['advanced_prediction_output_port']
    
    def get_prediction_api_advanced_controller(self):
        """Get prediction API advanced controller instance."""
        if 'prediction_api_advanced_controller' not in self._instances:
            from agrr_core.adapter.controllers.prediction_api_advanced_controller import PredictionAPIAdvancedController
            
            multi_metric_input_port = self.get_multi_metric_prediction_input_port()
            model_evaluation_input_port = self.get_model_evaluation_input_port()
            batch_prediction_input_port = self.get_batch_prediction_input_port()
            model_management_input_port = self.get_model_management_input_port()
            
            self._instances['prediction_api_advanced_controller'] = PredictionAPIAdvancedController(
                multi_metric_prediction_input_port=multi_metric_input_port,
                model_evaluation_input_port=model_evaluation_input_port,
                batch_prediction_input_port=batch_prediction_input_port,
                model_management_input_port=model_management_input_port
            )
        return self._instances['prediction_api_advanced_controller']
    
    # Service Components
    def get_integrated_prediction_service(self) -> PredictionIntegratedService:
        """Get integrated prediction service instance."""
        if 'integrated_prediction_service' not in self._instances:
            self._instances['integrated_prediction_service'] = PredictionIntegratedService()
        return self._instances['integrated_prediction_service']
    
    
    # Utility Methods
    def get_external_data_repository(self) -> Optional[WeatherExternalRepository]:
        """Get external data repository if available."""
        weather_repository = self.get_weather_repository()
        if isinstance(weather_repository, WeatherExternalRepository):
            return weather_repository
        return None
    
    def get_prediction_data_from_repository(self, location_key: str) -> Optional[list]:
        """Get prediction data from repository if available."""
        weather_repository = self.get_weather_repository()
        if isinstance(weather_repository, WeatherExternalRepository):
            return weather_repository.get_prediction_data(location_key)
        elif isinstance(weather_repository, WeatherStorageRepository):
            # Storage repositories might also have prediction data
            return None
        return None
    
    def inject_external_data(self, location_key: str, weather_data: list) -> None:
        """Inject external weather data for testing or simulation."""
        weather_repository = self.get_weather_repository()
        if isinstance(weather_repository, WeatherExternalRepository):
            weather_repository.inject_weather_data(location_key, weather_data)
    
    def clear_external_data(self, location_key: str) -> None:
        """Clear injected external data."""
        weather_repository = self.get_weather_repository()
        if isinstance(weather_repository, WeatherExternalRepository):
            weather_repository.clear_injected_data(location_key)
    
    # Application Entry Points
    async def run_cli(self, args: list = None) -> None:
        """Run CLI application with dependency injection."""
        controller = self.get_cli_controller()
        await controller.run(args)
    
    def get_weather_cli_container(self):
        """Get weather CLI container for backward compatibility."""
        return WeatherCliContainer(self.config)
    
    def get_prediction_container(self):
        """Get prediction container for backward compatibility."""
        return PredictionContainer(self.config)


# Backward Compatibility Classes
class WeatherCliContainer(AgrrCoreContainer):
    """Weather CLI container for backward compatibility."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
    
    def get_weather_repository(self) -> WeatherRepositoryGateway:
        """Get weather repository instance with CLI defaults."""
        if 'weather_repository' not in self._instances:
            repository_type = self.config.get('weather_repository_type', 'api')
            
            if repository_type == 'storage':
                storage_path = self.config.get('storage_path', 'data/weather')
                self._instances['weather_repository'] = WeatherStorageRepository(storage_path=storage_path)
            elif repository_type == 'external':
                fallback_repo = None
                if self.config.get('enable_fallback', False):
                    base_url = self.config.get('open_meteo_base_url', 'https://archive-api.open-meteo.com/v1/archive')
                    fallback_repo = WeatherAPIOpenMeteoRepository(base_url=base_url)
                self._instances['weather_repository'] = WeatherExternalRepository(fallback_repository=fallback_repo)
            else:  # Default to API
                base_url = self.config.get('open_meteo_base_url', 'https://archive-api.open-meteo.com/v1/archive')
                self._instances['weather_repository'] = WeatherAPIOpenMeteoRepository(base_url=base_url)
        
        return self._instances['weather_repository']


class PredictionContainer(AgrrCoreContainer):
    """Prediction container for backward compatibility."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
    
    def get_weather_repository(self) -> WeatherRepositoryGateway:
        """Get weather repository instance with prediction defaults."""
        if 'weather_repository' not in self._instances:
            repository_type = self.config.get('weather_repository_type', 'memory')
            
            if repository_type == 'storage':
                storage_path = self.config.get('storage_path', 'data/weather')
                self._instances['weather_repository'] = WeatherStorageRepository(storage_path=storage_path)
            elif repository_type == 'external':
                fallback_repo = None
                if self.config.get('enable_fallback', False):
                    fallback_repo = WeatherMemoryRepository()
                self._instances['weather_repository'] = WeatherExternalRepository(fallback_repository=fallback_repo)
            else:  # Default to in-memory
                self._instances['weather_repository'] = WeatherMemoryRepository()
        
        return self._instances['weather_repository']
