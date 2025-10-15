"""Weather gateway adapter for managing multiple weather gateway implementations.

This adapter allows switching between different weather data sources (File, API, JMA)
while maintaining a unified interface to the UseCase layer.
"""

from typing import List, Optional

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway


class WeatherGatewayAdapter(WeatherGateway):
    """Adapter for managing multiple weather gateway implementations.
    
    This gateway provides a unified interface while delegating to appropriate
    weather gateways based on the operation:
    - File gateway for file-based operations
    - API gateway for location-based queries
    """

    def __init__(
        self, 
        file_gateway: Optional[WeatherGateway] = None,
        api_gateway: Optional[WeatherGateway] = None
    ):
        """Initialize weather gateway adapter.
        
        Args:
            file_gateway: Gateway for file-based weather data
            api_gateway: Gateway for API-based weather data (Open-Meteo or JMA)
        """
        self.file_gateway = file_gateway
        self.api_gateway = api_gateway

    async def get(self) -> List[WeatherData]:
        """Get weather data from configured source.
        
        Returns:
            List of WeatherData entities
            
        Note:
            Repository is configured with its data source at initialization.
        """
        if self.file_gateway is None:
            raise ValueError("File gateway not initialized")
        return await self.file_gateway.get()

    async def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination."""
        raise NotImplementedError("Weather data creation not implemented in WeatherGatewayAdapter")

    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """Get weather data by location and date range."""
        if self.api_gateway is None:
            raise ValueError("API gateway not initialized")
        return await self.api_gateway.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
    
    async def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get 16-day weather forecast starting from tomorrow."""
        if self.api_gateway is None:
            raise ValueError("API gateway not initialized")
        return await self.api_gateway.get_forecast(latitude, longitude)

