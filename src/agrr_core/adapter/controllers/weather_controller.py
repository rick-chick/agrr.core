"""Weather controller for handling weather-related requests."""

from typing import Dict, Any

from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.interactors.predict_weather_interactor import PredictWeatherInteractor
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.usecase.dto.prediction_request_dto import PredictionRequestDTO


class WeatherController:
    """Controller for weather-related operations."""
    
    def __init__(
        self,
        fetch_weather_data_interactor: FetchWeatherDataInteractor,
        predict_weather_interactor: PredictWeatherInteractor
    ):
        self.fetch_weather_data_interactor = fetch_weather_data_interactor
        self.predict_weather_interactor = predict_weather_interactor
    
    async def get_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Get weather data for specified location and date range."""
        request = WeatherDataRequestDTO(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        return await self.fetch_weather_data_interactor.execute(request)
    
    async def predict_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        prediction_days: int = 365
    ) -> Dict[str, Any]:
        """Predict weather for specified location and date range."""
        request = PredictionRequestDTO(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            prediction_days=prediction_days
        )
        return await self.predict_weather_interactor.execute(request)
    
    def get_weather_data_sync(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Synchronous version of get_weather_data."""
        request = WeatherDataRequestDTO(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
        # Note: This should be made async or use a sync version of the interactor
        import asyncio
        return asyncio.run(self.fetch_weather_data_interactor.execute(request))
    
    def predict_weather_sync(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        prediction_days: int = 365
    ) -> Dict[str, Any]:
        """Synchronous version of predict_weather."""
        request = PredictionRequestDTO(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            prediction_days=prediction_days
        )
        # Note: This should be made async or use a sync version of the interactor
        import asyncio
        return asyncio.run(self.predict_weather_interactor.execute(request))
