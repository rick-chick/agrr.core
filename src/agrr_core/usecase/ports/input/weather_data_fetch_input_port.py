"""Fetch weather data input port interface."""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO


class FetchWeatherDataInputPort(ABC):
    """Interface for fetch weather data interactor operations."""
    
    @abstractmethod
    async def execute(self, request: WeatherDataRequestDTO) -> None:
        """Execute weather data fetching."""
        pass
