"""External data injection weather repository implementation."""

from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.usecase.ports.input.weather_data_input_port import WeatherDataInputPort


class ExternalDataWeatherRepository(WeatherDataInputPort):
    """Repository that allows external data injection without API calls."""
    
    def __init__(self, fallback_repository: Optional[WeatherDataInputPort] = None):
        self.fallback_repository = fallback_repository
        self._injected_data: Dict[str, List[WeatherData]] = {}
        self._location_metadata: Dict[str, Location] = {}
    
    def inject_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        weather_data_list: List[WeatherData],
        location: Optional[Location] = None
    ) -> None:
        """Inject weather data for a specific location."""
        location_key = self._get_location_key(latitude, longitude)
        self._injected_data[location_key] = weather_data_list
        
        if location is None:
            location = Location(latitude=latitude, longitude=longitude)
        self._location_metadata[location_key] = location
    
    def clear_injected_data(self) -> None:
        """Clear all injected data."""
        self._injected_data.clear()
        self._location_metadata.clear()
    
    def has_data_for_location(self, latitude: float, longitude: float) -> bool:
        """Check if data is available for location."""
        location_key = self._get_location_key(latitude, longitude)
        return location_key in self._injected_data
    
    def _get_location_key(self, latitude: float, longitude: float) -> str:
        """Generate key for location."""
        return f"{latitude:.6f}_{longitude:.6f}"
    
    async def save_weather_data(self, weather_data: List[WeatherData]) -> None:
        """Save weather data (delegate to fallback repository if available)."""
        if self.fallback_repository:
            await self.fallback_repository.save_weather_data(weather_data)
    
    async def get_weather_data_by_location_and_date_range(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Tuple[List[WeatherData], Location]:
        """Get weather data, checking injected data first, then fallback.
        
        Returns:
            Tuple of (weather_data_list, location) where location contains
            the actual coordinates and metadata.
        """
        location_key = self._get_location_key(latitude, longitude)
        
        # Check if data is injected for this location
        if location_key in self._injected_data:
            weather_data_list = self._injected_data[location_key]
            location = self._location_metadata.get(location_key, Location(latitude=latitude, longitude=longitude))
            
            # Filter by date range
            start_datetime = datetime.fromisoformat(start_date)
            end_datetime = datetime.fromisoformat(end_date)
            
            filtered_data = [
                data for data in weather_data_list
                if start_datetime <= data.time <= end_datetime
            ]
            
            return filtered_data, location
        
        # Fallback to another repository if available
        if self.fallback_repository:
            return await self.fallback_repository.get_weather_data_by_location_and_date_range(
                latitude, longitude, start_date, end_date
            )
        
        # No data available
        location = Location(latitude=latitude, longitude=longitude)
        return [], location
    
    def get_injection_info(self) -> Dict[str, Any]:
        """Get information about injected data."""
        return {
            'injected_locations': len(self._injected_data),
            'total_data_points': sum(len(data) for data in self._injected_data.values()),
            'locations': [
                {
                    'key': key,
                    'data_points': len(data),
                    'location': {
                        'latitude': self._location_metadata.get(key, Location(0, 0)).latitude,
                        'longitude': self._location_metadata.get(key, Location(0, 0)).longitude
                    }
                }
                for key, data in self._injected_data.items()
            ]
        }
