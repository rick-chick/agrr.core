"""Prediction gateway implementation."""

from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast
from agrr_core.usecase.gateways.prediction_gateway import PredictionGateway
from agrr_core.adapter.interfaces.file_repository_interface import FileRepositoryInterface
from agrr_core.adapter.services.prediction_arima_service import PredictionARIMAService


class PredictionGatewayImpl(PredictionGateway):
    """Implementation of prediction gateway."""
    
    def __init__(
        self, 
        file_repository: FileRepositoryInterface,
        prediction_service: PredictionARIMAService
    ):
        """Initialize prediction gateway."""
        self.file_repository = file_repository
        self.prediction_service = prediction_service
    
    
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
        """Predict weather metrics using historical data."""
        return await self.prediction_service._predict_single_metric(
            historical_data,
            metric,
            config
        )
