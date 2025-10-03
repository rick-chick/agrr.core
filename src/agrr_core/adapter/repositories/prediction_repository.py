"""Weather prediction repository implementations."""

from typing import List

from agrr_core.entity import Forecast
from agrr_core.usecase.ports.input.weather_prediction_input_port import WeatherPredictionInputPort


class InMemoryPredictionRepository(WeatherPredictionInputPort):
    """In-memory repository for weather predictions (useful for testing)."""
    
    def __init__(self):
        self._forecasts: List[Forecast] = []
    
    async def save_forecast(self, forecasts: List[Forecast]) -> None:
        """Save forecast data to memory."""
        self._forecasts.extend(forecasts)
    
    async def get_forecast_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Forecast]:
        """Get forecast data from memory (filtered by date range)."""
        from datetime import datetime
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)
        
        filtered_forecasts = [
            forecast for forecast in self._forecasts
            if start_datetime <= forecast.date <= end_datetime
        ]
        
        return filtered_forecasts
    
    def clear(self) -> None:
        """Clear all stored forecast data."""
        self._forecasts.clear()
