"""Dependency injection container for prediction services."""

from typing import Dict, Any, Optional

from agrr_core.adapter.repositories.open_meteo_weather_repository import OpenMeteoWeatherRepository
from agrr_core.adapter.repositories.storage_weather_repository import StorageWeatherRepository
from agrr_core.adapter.repositories.external_data_weather_repository import ExternalDataWeatherRepository
from agrr_core.adapter.services.integrated_prediction_service import IntegratedPredictionService
from agrr_core.adapter.services.visualization_service import VisualizationService
from agrr_core.usecase.ports.input.weather_data_input_port import WeatherDataInputPort
from agrr_core.usecase.ports.input.advanced_prediction_input_port import AdvancedPredictionInputPort
from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort
from agrr_core.usecase.interactors.advanced_predict_weather_interactor import AdvancedPredictWeatherInteractor


class PredictionContainer:
    """Dependency injection container for prediction services."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize container with configuration."""
        self.config = config or {}
        self._instances = {}
    
    def get_weather_repository(self) -> WeatherDataInputPort:
        """Get weather repository instance."""
        if 'weather_repository' not in self._instances:
            repository_type = self.config.get('weather_repository_type', 'api')
            
            if repository_type == 'storage':
                storage_path = self.config.get('storage_path', 'data/weather')
                self._instances['weather_repository'] = StorageWeatherRepository(storage_path=storage_path)
            elif repository_type == 'external':
                fallback_repo = None
                if self.config.get('enable_fallback', False):
                    # Create fallback API repository
                    base_url = self.config.get('open_meteo_base_url', 'https://archive-api.open-meteo.com/v1/archive')
                    fallback_repo = OpenMeteoWeatherRepository(base_url=base_url)
                self._instances['weather_repository'] = ExternalDataWeatherRepository(fallback_repository=fallback_repo)
            else:  # Default to API
                base_url = self.config.get('open_meteo_base_url', 'https://archive-api.open-meteo.com/v1/archive')
                self._instances['weather_repository'] = OpenMeteoWeatherRepository(base_url=base_url)
        
        return self._instances['weather_repository']
    
    def get_advanced_prediction_input_port(self) -> AdvancedPredictionInputPort:
        """Get advanced prediction input port instance."""
        if 'advanced_prediction_input_port' not in self._instances:
            # Use integrated prediction service as input port
            prediction_service = self.get_integrated_prediction_service()
            self._instances['advanced_prediction_input_port'] = prediction_service
        return self._instances['advanced_prediction_input_port']
    
    def get_advanced_prediction_output_port(self) -> AdvancedPredictionOutputPort:
        """Get advanced prediction output port instance."""
        if 'advanced_prediction_output_port' not in self._instances:
            # Use integrated prediction service as output port
            prediction_service = self.get_integrated_prediction_service()
            self._instances['advanced_prediction_output_port'] = prediction_service
        return self._instances['advanced_prediction_output_port']
    
    def get_prediction_presenter_output_port(self) -> PredictionPresenterOutputPort:
        """Get prediction presenter output port instance."""
        if 'prediction_presenter_output_port' not in self._instances:
            visualization_service = self.get_visualization_service()
            self._instances['prediction_presenter_output_port'] = visualization_service
        return self._instances['prediction_presenter_output_port']
    
    def get_integrated_prediction_service(self) -> IntegratedPredictionService:
        """Get integrated prediction service instance."""
        if 'integrated_prediction_service' not in self._instances:
            self._instances['integrated_prediction_service'] = IntegratedPredictionService()
        return self._instances['integrated_prediction_service']
    
    def get_visualization_service(self) -> VisualizationService:
        """Get visualization service instance."""
        if 'visualization_service' not in self._instances:
            self._instances['visualization_service'] = VisualizationService()
        return self._instances['visualization_service']
    
    def get_advanced_predict_weather_interactor(self) -> AdvancedPredictWeatherInteractor:
        """Get advanced predict weather interactor instance."""
        if 'advanced_predict_weather_interactor' not in self._instances:
            weather_repository = self.get_weather_repository()
            prediction_input_port = self.get_advanced_prediction_input_port()
            prediction_output_port = self.get_advanced_prediction_output_port()
            prediction_presenter = self.get_prediction_presenter_output_port()
            
            self._instances['advanced_predict_weather_interactor'] = AdvancedPredictWeatherInteractor(
                weather_data_input_port=weather_repository,
                advanced_prediction_input_port=prediction_input_port,
                advanced_prediction_output_port=prediction_output_port,
                prediction_presenter_output_port=prediction_presenter
            )
        return self._instances['advanced_predict_weather_interactor']
    
    def get_external_data_repository(self) -> Optional[ExternalDataWeatherRepository]:
        """Get external data repository if configured."""
        weather_repository = self.get_weather_repository()
        if isinstance(weather_repository, ExternalDataWeatherRepository):
            return weather_repository
        return None
    
    def inject_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        weather_data_list: list,
        location: Optional[object] = None
    ) -> None:
        """Inject weather data into external repository if available."""
        external_repo = self.get_external_data_repository()
        if external_repo:
            external_repo.inject_weather_data(latitude, longitude, weather_data_list, location)
        else:
            raise ValueError("External data repository not configured. Set weather_repository_type to 'external'")
    
    def clear_injected_data(self) -> None:
        """Clear injected data from external repository."""
        external_repo = self.get_external_data_repository()
        if external_repo:
            external_repo.clear_injected_data()
    
    def get_repository_info(self) -> Dict[str, Any]:
        """Get information about the configured repository."""
        weather_repository = self.get_weather_repository()
        info = {
            'repository_type': type(weather_repository).__name__,
            'config': self.config
        }
        
        if isinstance(weather_repository, ExternalDataWeatherRepository):
            info.update(weather_repository.get_injection_info())
        elif isinstance(weather_repository, StorageWeatherRepository):
            # Note: This would need to be made async in a real implementation
            info['storage_path'] = weather_repository.storage_path
        
        return info
