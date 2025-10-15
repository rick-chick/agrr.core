"""Prediction gateway implementation."""

from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast
from agrr_core.usecase.gateways.prediction_gateway import PredictionGateway
from agrr_core.adapter.interfaces.io.file_service_interface import FileServiceInterface
from agrr_core.adapter.interfaces.ml.prediction_service_interface import PredictionServiceInterface


class PredictionGatewayImpl(PredictionGateway):
    """Implementation of prediction gateway.
    
    This gateway depends on interface abstractions, following the Dependency Inversion Principle.
    All dependencies are injected as interfaces, not concrete implementations.
    """
    
    def __init__(
        self, 
        file_repository: FileServiceInterface,
        prediction_service: PredictionServiceInterface
    ):
        """Initialize prediction gateway with interface abstractions.
        
        Args:
            file_repository: File repository abstraction
            prediction_service: Prediction service abstraction (ARIMA, LightGBM, etc.)
        """
        self.file_repository = file_repository
        self.prediction_service = prediction_service
    
    async def read_historical_data(self, source: str) -> List[WeatherData]:
        """Read historical weather data from source file.
        
        Args:
            source: Path to historical weather data file
            
        Returns:
            List of WeatherData entities
        """
        return await self.file_repository.read_weather_data_from_file(source)
    
    async def create(self, predictions: List[Forecast], destination: str) -> None:
        """Create predictions at destination."""
        await self.file_repository.write_predictions_to_file(
            predictions,
            destination,
            'auto',
            include_metadata=True
        )
    
    async def predict(
        self,
        historical_data: List[WeatherData],
        metric: str,
        config: dict
    ) -> List[Forecast]:
        """Predict weather metrics using historical data.
        
        Args:
            historical_data: Historical weather data
            metric: Metric to predict (e.g., 'temperature')
            config: Prediction configuration including 'prediction_days'
            
        Returns:
            List of forecast entities
        """
        prediction_days = config.get('prediction_days', 30)
        return await self.prediction_service.predict(
            historical_data=historical_data,
            metric=metric,
            prediction_days=prediction_days,
            model_config=config
        )
