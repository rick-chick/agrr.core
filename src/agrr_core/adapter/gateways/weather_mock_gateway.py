"""Weather mock gateway implementation for testing and development.

This gateway returns mock weather data based on last year's same period data.
Used for testing and development when real weather data is not available.
"""

import logging
import math
import random
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, date
import json
from pathlib import Path

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.weather_location_entity import Location
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway

class WeatherMockGateway(WeatherGateway):
    """Mock gateway that returns last year's same period weather data.
    
    This gateway is useful for:
    - Testing and development
    - When real weather APIs are unavailable
    - Demonstrating functionality without external dependencies
    
    The mock data is generated based on last year's same period data
    with slight variations to simulate realistic weather patterns.
    """
    
    def __init__(self, mock_data_file: str = None):
        """Initialize mock weather gateway.
        
        Args:
            mock_data_file: Optional path to mock data file (JSON format)
                          If None, generates synthetic data
        """
        self.mock_data_file = mock_data_file
        self.logger = logging.getLogger(__name__)
        self._mock_data_cache = None
    
    def get(self) -> List[WeatherData]:
        """Get mock weather data from configured source.
        
        Returns:
            List of WeatherData entities (last 30 days)
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        return self.get_by_location_and_date_range(
            latitude=35.6762,  # Tokyo coordinates
            longitude=139.6503,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
    
    def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create mock weather data at destination.
        
        Args:
            weather_data: Weather data to save
            destination: Output file path
        """
        # Convert WeatherData to JSON format
        data_list = []
        for data in weather_data:
            data_dict = {
                "time": data.time.isoformat(),
                "temperature_2m_max": data.temperature_2m_max,
                "temperature_2m_min": data.temperature_2m_min,
                "temperature_2m_mean": data.temperature_2m_mean,
                "precipitation_sum": data.precipitation_sum,
                "sunshine_duration": data.sunshine_duration,
                "wind_speed_10m": data.wind_speed_10m,
                "weather_code": data.weather_code
            }
            data_list.append(data_dict)
        
        # Create output data structure
        output_data = {
            "latitude": 35.6762,
            "longitude": 139.6503,
            "data": data_list
        }
        
        # Write to file
        Path(destination).write_text(
            json.dumps(output_data, indent=2, ensure_ascii=False)
        )
        
        self.logger.info(f"Mock weather data saved to {destination}")
    
    def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """Get mock weather data for location and date range.
        
        Returns last year's same period data with slight variations.
        
        Args:
            latitude: Latitude
            longitude: Longitude  
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            WeatherDataWithLocationDTO containing mock weather data
        """
        try:
            # Parse date range
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Calculate last year's same period
            last_year_start = start_dt.replace(year=start_dt.year - 1)
            last_year_end = end_dt.replace(year=end_dt.year - 1)
            
            self.logger.info(
                f"Generating mock data for ({latitude}, {longitude}) "
                f"from {start_date} to {end_date} "
                f"(based on last year: {last_year_start.date()} to {last_year_end.date()})"
            )
            
            # Generate mock weather data
            weather_data_list = self._generate_mock_weather_data(
                latitude, longitude, start_dt, end_dt, last_year_start, last_year_end
            )
            
            # Create location
            location = Location(
                latitude=latitude,
                longitude=longitude,
                elevation=None,
                timezone="Asia/Tokyo"  # Default timezone for mock data
            )
            
            return WeatherDataWithLocationDTO(
                weather_data_list=weather_data_list,
                location=location
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate mock weather data: {e}")
            raise
    
    def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get mock weather forecast.
        
        Returns 16-day forecast based on last year's same period.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            WeatherDataWithLocationDTO containing 16-day forecast
        """
        # Generate 16-day forecast starting from tomorrow
        tomorrow = datetime.now().date() + timedelta(days=1)
        forecast_end = tomorrow + timedelta(days=15)
        
        return self.get_by_location_and_date_range(
            latitude=latitude,
            longitude=longitude,
            start_date=tomorrow.strftime("%Y-%m-%d"),
            end_date=forecast_end.strftime("%Y-%m-%d")
        )
    
    def _generate_mock_weather_data(
        self,
        latitude: float,
        longitude: float,
        start_dt: datetime,
        end_dt: datetime,
        last_year_start: datetime,
        last_year_end: datetime
    ) -> List[WeatherData]:
        """Generate mock weather data based on last year's same period.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            start_dt: Current period start date
            end_dt: Current period end date
            last_year_start: Last year's start date
            last_year_end: Last year's end date
            
        Returns:
            List of WeatherData entities
        """
        weather_data_list = []
        current_date = start_dt
        
        while current_date <= end_dt:
            # Calculate corresponding date last year
            last_year_date = current_date.replace(year=current_date.year - 1)
            
            # Generate mock data for this date
            mock_data = self._generate_daily_mock_data(
                latitude, longitude, current_date, last_year_date
            )
            
            weather_data_list.append(mock_data)
            current_date += timedelta(days=1)
        
        return weather_data_list
    
    def _generate_daily_mock_data(
        self,
        latitude: float,
        longitude: float,
        current_date: datetime,
        last_year_date: datetime
    ) -> WeatherData:
        """Generate mock weather data for a single day.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            current_date: Current date
            last_year_date: Corresponding date last year
            
        Returns:
            WeatherData entity for the day
        """
        # Base temperature based on season and location
        base_temp = self._get_seasonal_base_temperature(latitude, longitude, current_date)
        
        # Add some randomness (±3°C)
        import random
        temp_variation = random.uniform(-3.0, 3.0)
        
        # Generate temperature values
        temp_mean = base_temp + temp_variation
        temp_max = temp_mean + random.uniform(2.0, 6.0)  # 2-6°C higher than mean
        temp_min = temp_mean - random.uniform(2.0, 6.0)  # 2-6°C lower than mean
        
        # Generate precipitation (30% chance of rain)
        precipitation = 0.0
        if random.random() < 0.3:  # 30% chance
            precipitation = random.uniform(0.1, 15.0)  # 0.1-15mm
        
        # Generate sunshine duration (6-12 hours)
        sunshine_hours = random.uniform(6.0, 12.0)
        sunshine_duration = sunshine_hours * 3600  # Convert to seconds
        
        # Generate wind speed (1-8 m/s)
        wind_speed = random.uniform(1.0, 8.0)
        
        # Generate weather code (simplified)
        weather_code = self._generate_weather_code(precipitation, sunshine_hours)
        
        return WeatherData(
            time=current_date,
            temperature_2m_max=round(temp_max, 1),
            temperature_2m_min=round(temp_min, 1),
            temperature_2m_mean=round(temp_mean, 1),
            precipitation_sum=round(precipitation, 1),
            sunshine_duration=round(sunshine_duration),
            wind_speed_10m=round(wind_speed, 1),
            weather_code=weather_code
        )
    
    def _get_seasonal_base_temperature(
        self,
        latitude: float,
        longitude: float,
        date: datetime
    ) -> float:
        """Get seasonal base temperature for location and date.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            date: Date
            
        Returns:
            Base temperature in Celsius
        """
        # Simple seasonal model
        day_of_year = date.timetuple().tm_yday
        
        # Northern hemisphere seasonal variation
        if latitude > 0:
            # Summer peak around day 200 (mid-July)
            seasonal_temp = 20 + 10 * math.cos(2 * math.pi * (day_of_year - 200) / 365)
        else:
            # Southern hemisphere (inverted)
            seasonal_temp = 20 + 10 * math.cos(2 * math.pi * (day_of_year - 20) / 365)
        
        # Latitude adjustment (colder at higher latitudes)
        latitude_adjustment = -0.5 * abs(latitude)
        
        return seasonal_temp + latitude_adjustment
    
    def _generate_weather_code(
        self,
        precipitation: float,
        sunshine_hours: float
    ) -> int:
        """Generate weather code based on conditions.
        
        Args:
            precipitation: Precipitation amount (mm)
            sunshine_hours: Sunshine duration (hours)
            
        Returns:
            Weather code (0-3)
        """
        if precipitation > 5.0:
            return 3  # Heavy rain
        elif precipitation > 0.1:
            return 2  # Light rain
        elif sunshine_hours < 4.0:
            return 1  # Cloudy
        else:
            return 0  # Clear
