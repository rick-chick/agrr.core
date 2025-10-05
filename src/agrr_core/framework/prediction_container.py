"""Dependency injection container for prediction services."""

from typing import Dict, Any, Optional

from agrr_core.adapter.repositories.weather_memory_repository import WeatherMemoryRepository
from agrr_core.adapter.repositories.weather_storage_repository import WeatherStorageRepository
from agrr_core.adapter.repositories.weather_external_repository import WeatherExternalRepository
from agrr_core.adapter.services.prediction_integrated_service import PredictionIntegratedService
from agrr_core.adapter.services.prediction_visualization_service import PredictionVisualizationService
from agrr_core.usecase.gateways.weather_repository_gateway import WeatherRepositoryGateway
from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort


class PredictionContainer:
    """Dependency injection container for prediction services."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize container with configuration."""
        self.config = config or {}
        self._instances = {}
    
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
                    fallback_repo = WeatherMemoryRepository()
                self._instances['weather_repository'] = WeatherExternalRepository(fallback_repository=fallback_repo)
            else:  # Default to in-memory
                self._instances['weather_repository'] = WeatherMemoryRepository()
        
        return self._instances['weather_repository']
    
    def get_advanced_prediction_input_port(self):  # -> AdvancedPredictionInputPort:  # Type not available
        """Get advanced prediction input port instance."""
        if 'advanced_prediction_input_port' not in self._instances:
            # Use integrated prediction service as input port
            prediction_service = self.get_integrated_prediction_service()
            self._instances['advanced_prediction_input_port'] = prediction_service
        return self._instances['advanced_prediction_input_port']
    
    def get_advanced_prediction_output_port(self) -> AdvancedPredictionOutputPort:
        """Get advanced prediction output port instance."""
        if 'advanced_prediction_output_port' not in self._instances:
            from agrr_core.adapter.presenters.advanced_prediction_presenter import PredictionAdvancedPresenter
            self._instances['advanced_prediction_output_port'] = PredictionAdvancedPresenter()
        return self._instances['advanced_prediction_output_port']
    
    def get_prediction_presenter_output_port(self) -> PredictionPresenterOutputPort:
        """Get prediction presenter output port instance."""
        if 'prediction_presenter_output_port' not in self._instances:
            from agrr_core.adapter.presenters.prediction_presenter import PredictionPresenter
            self._instances['prediction_presenter_output_port'] = PredictionPresenter()
        return self._instances['prediction_presenter_output_port']
    
    def get_integrated_prediction_service(self) -> PredictionIntegratedService:
        """Get integrated prediction service instance."""
        if 'integrated_prediction_service' not in self._instances:
            self._instances['integrated_prediction_service'] = PredictionIntegratedService()
        return self._instances['integrated_prediction_service']
    
    def get_visualization_service(self) -> PredictionVisualizationService:
        """Get visualization service instance."""
        if 'visualization_service' not in self._instances:
            self._instances['visualization_service'] = PredictionVisualizationService()
        return self._instances['visualization_service']
    
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