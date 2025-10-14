"""Weather gateway implementation."""

from typing import List, Optional

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.adapter.interfaces.weather_repository_interface import WeatherRepositoryInterface


class WeatherGatewayImpl(WeatherGateway):
    """Implementation of weather gateway.
    
    This gateway depends on WeatherRepositoryInterface abstraction,
    not specific implementations (file, SQL, memory, API, etc.).
    All dependencies are injected as interfaces, following the Dependency Inversion Principle.
    """

    def __init__(
        self, 
        weather_repository: Optional[WeatherRepositoryInterface] = None,
        weather_api_repository: Optional[WeatherRepositoryInterface] = None
    ):
        """Initialize weather gateway with repository abstractions.
        
        Args:
            weather_repository: Repository abstraction for weather data (file, SQL, memory, etc.)
            weather_api_repository: API repository abstraction for external weather data
        """
        self.weather_repository = weather_repository
        self.weather_api_repository = weather_api_repository

    async def get(self) -> List[WeatherData]:
        """Get weather data from configured repository.
        
        Returns:
            List of WeatherData entities
            
        Note:
            Repository is configured with its data source at initialization.
        """
        if self.weather_repository is None:
            raise ValueError("WeatherRepository not initialized")
        return await self.weather_repository.get()

    async def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination."""
        raise NotImplementedError("Weather data creation not implemented in WeatherFileRepository")

    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """Get weather data by location and date range."""
        return await self.weather_api_repository.get_by_location_and_date_range(
            latitude, longitude, start_date, end_date
        )
    
    async def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get 16-day weather forecast starting from tomorrow."""
        return await self.weather_api_repository.get_forecast(latitude, longitude)