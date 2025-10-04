"""Storage-based weather repository implementation."""

from typing import List, Tuple, Optional
from datetime import datetime
import json
import os

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.usecase.ports.input.weather_data_input_port import WeatherDataInputPort


class StorageWeatherRepository(WeatherDataInputPort):
    """Repository for weather data stored in local storage."""
    
    def __init__(self, storage_path: str = "data/weather"):
        self.storage_path = storage_path
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self) -> None:
        """Ensure storage directory exists."""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _get_location_key(self, latitude: float, longitude: float) -> str:
        """Generate storage key for location."""
        return f"{latitude:.6f}_{longitude:.6f}"
    
    def _get_storage_file_path(self, location_key: str) -> str:
        """Get storage file path for location."""
        return os.path.join(self.storage_path, f"{location_key}.json")
    
    async def save_weather_data(self, weather_data: List[WeatherData], location: Optional[Location] = None) -> None:
        """Save weather data to storage."""
        if not weather_data:
            return
        
        # Use location from first data point if not provided
        if location is None:
            location = Location(latitude=0.0, longitude=0.0)  # Default location
        
        location_key = self._get_location_key(location.latitude, location.longitude)
        file_path = self._get_storage_file_path(location_key)
        
        # Load existing data
        existing_data = await self._load_weather_data_from_file(file_path)
        
        # Merge with new data (avoid duplicates by time)
        existing_times = {data.time.isoformat() for data in existing_data}
        new_data = [data for data in weather_data if data.time.isoformat() not in existing_times]
        
        if new_data:
            all_data = existing_data + new_data
            # Sort by time
            all_data.sort(key=lambda x: x.time)
            
            # Save to file
            await self._save_weather_data_to_file(file_path, all_data, location)
    
    async def get_weather_data_by_location_and_date_range(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Tuple[List[WeatherData], Location]:
        """Get weather data from storage.
        
        Returns:
            Tuple of (weather_data_list, location) where location contains
            the requested coordinates and metadata from storage.
        """
        location_key = self._get_location_key(latitude, longitude)
        file_path = self._get_storage_file_path(location_key)
        
        if not os.path.exists(file_path):
            # Return empty data with requested location
            location = Location(latitude=latitude, longitude=longitude)
            return [], location
        
        # Load data from file
        weather_data_list, location = await self._load_weather_data_from_file(file_path)
        
        # Filter by date range
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)
        
        filtered_data = [
            data for data in weather_data_list
            if start_datetime <= data.time <= end_datetime
        ]
        
        return filtered_data, location
    
    async def _load_weather_data_from_file(self, file_path: str) -> Tuple[List[WeatherData], Location]:
        """Load weather data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            location_data = data.get('location', {})
            location = Location(
                latitude=location_data.get('latitude', 0.0),
                longitude=location_data.get('longitude', 0.0),
                elevation=location_data.get('elevation'),
                timezone=location_data.get('timezone')
            )
            
            weather_data_list = []
            for item in data.get('weather_data', []):
                weather_data = WeatherData(
                    time=datetime.fromisoformat(item['time']),
                    temperature_2m_max=item.get('temperature_2m_max'),
                    temperature_2m_min=item.get('temperature_2m_min'),
                    temperature_2m_mean=item.get('temperature_2m_mean'),
                    precipitation_sum=item.get('precipitation_sum'),
                    sunshine_duration=item.get('sunshine_duration'),
                )
                weather_data_list.append(weather_data)
            
            return weather_data_list, location
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
            raise WeatherDataNotFoundError(f"Failed to load weather data from storage: {e}")
    
    async def _save_weather_data_to_file(self, file_path: str, weather_data_list: List[WeatherData], location: Location) -> None:
        """Save weather data to JSON file."""
        data = {
            'location': {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'elevation': location.elevation,
                'timezone': location.timezone
            },
            'weather_data': [
                {
                    'time': data.time.isoformat(),
                    'temperature_2m_max': data.temperature_2m_max,
                    'temperature_2m_min': data.temperature_2m_min,
                    'temperature_2m_mean': data.temperature_2m_mean,
                    'precipitation_sum': data.precipitation_sum,
                    'sunshine_duration': data.sunshine_duration,
                }
                for data in weather_data_list
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def clear_storage(self) -> None:
        """Clear all stored weather data."""
        if os.path.exists(self.storage_path):
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.storage_path, filename)
                    os.remove(file_path)
    
    async def get_storage_info(self) -> dict:
        """Get information about stored data."""
        if not os.path.exists(self.storage_path):
            return {'total_files': 0, 'total_data_points': 0}
        
        total_files = 0
        total_data_points = 0
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                file_path = os.path.join(self.storage_path, filename)
                try:
                    weather_data_list, _ = await self._load_weather_data_from_file(file_path)
                    total_files += 1
                    total_data_points += len(weather_data_list)
                except WeatherDataNotFoundError:
                    continue
        
        return {
            'total_files': total_files,
            'total_data_points': total_data_points,
            'storage_path': self.storage_path
        }
