"""Weather gateway implementation."""

from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.adapter.repositories.weather_file_repository import WeatherFileRepository


class WeatherGatewayImpl(WeatherGateway):
    """Implementation of weather gateway."""
    
    def __init__(self, file_repository: WeatherFileRepository):
        """Initialize weather gateway."""
        self.file_repository = file_repository
    
    async def get(self, source: str) -> List[WeatherData]:
        """Get weather data from source."""
        return await self.file_repository.read_weather_data_from_file(source)
    
