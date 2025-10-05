"""Weather gateway implementation."""

from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.adapter.repositories.weather_file_repository import WeatherFileRepository
from agrr_core.adapter.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository


class WeatherGatewayImpl(WeatherGateway):
    """Implementation of weather gateway."""

    def __init__(
        self, 
        weather_file_repository: WeatherFileRepository,
        weather_api_repository: WeatherAPIOpenMeteoRepository
    ):
        """Initialize weather gateway."""
        self.weather_file_repository = weather_file_repository
        self.weather_api_repository = weather_api_repository

    async def get(self, source: str) -> List[WeatherData]:
        """Get weather data from source."""
        return await self.weather_file_repository.read_weather_data_from_file(source)

    async def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination."""
        raise NotImplementedError("Weather data creation not implemented in WeatherFileRepository")

    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> List[WeatherData]:
        """Get weather data by location and date range."""
        return await self.weather_api_repository.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
