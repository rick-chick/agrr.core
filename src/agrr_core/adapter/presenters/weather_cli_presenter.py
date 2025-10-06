"""CLI weather presenter for adapter layer."""

from typing import Dict, Any
from datetime import datetime
import sys
import json

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
from agrr_core.usecase.ports.output.weather_presenter_output_port import WeatherPresenterOutputPort


class WeatherCLIPresenter(WeatherPresenterOutputPort):
    """CLI presenter for weather data display in terminal."""
    
    def __init__(self, output_stream=sys.stdout):
        """Initialize CLI presenter with output stream."""
        self.output_stream = output_stream
    
    def format_weather_data(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Format a single weather data entity to response format."""
        return {
            "location": {
                "latitude": weather_data.location.latitude,
                "longitude": weather_data.location.longitude,
            },
            "date": weather_data.date.isoformat(),
            "temperature": weather_data.temperature,
            "humidity": weather_data.humidity,
            "precipitation": weather_data.precipitation,
            "wind_speed": weather_data.wind_speed,
            "wind_direction": weather_data.wind_direction,
        }
    
    def format_weather_data_dto(self, dto: WeatherDataResponseDTO) -> Dict[str, Any]:
        """Format weather data DTO to response format."""
        return {
            "time": dto.time,
            "temperature_2m_max": dto.temperature_2m_max,
            "temperature_2m_min": dto.temperature_2m_min,
            "temperature_2m_mean": dto.temperature_2m_mean,
            "precipitation_sum": dto.precipitation_sum,
            "sunshine_duration": dto.sunshine_duration,
            "sunshine_hours": dto.sunshine_hours,
            "wind_speed_10m": dto.wind_speed_10m,
            "weather_code": dto.weather_code,
        }
    
    def format_weather_data_list_dto(self, dto: WeatherDataListResponseDTO) -> Dict[str, Any]:
        """Format weather data list DTO to response format."""
        result = {
            "data": [self.format_weather_data_dto(item) for item in dto.data],
            "total_count": dto.total_count,
        }
        
        # Include location information if available
        if dto.location:
            result["location"] = {
                "latitude": dto.location.latitude,
                "longitude": dto.location.longitude,
                "elevation": dto.location.elevation,
                "timezone": dto.location.timezone,
            }
        
        return result
    
    def format_error(self, error_message: str, error_code: str = "WEATHER_ERROR") -> Dict[str, Any]:
        """Format error response."""
        return {
            "error": {
                "code": error_code,
                "message": error_message,
            },
            "success": False,
        }
    
    def format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format success response with data."""
        return {
            "success": True,
            "data": data,
        }
    
    def display_weather_data(self, weather_data_list: WeatherDataListResponseDTO) -> None:
        """Display weather data in a formatted table for CLI."""
        if not weather_data_list.data:
            self.output_stream.write("No weather data available.\n")
            return
        
        # Header
        self.output_stream.write("\n" + "="*80 + "\n")
        self.output_stream.write("WEATHER FORECAST\n")
        self.output_stream.write("="*80 + "\n")
        
        # Location information
        if weather_data_list.location:
            loc = weather_data_list.location
            self.output_stream.write(f"\nLocation: {loc.latitude:.4f}°N, {loc.longitude:.4f}°E")
            if loc.elevation is not None:
                self.output_stream.write(f" | Elevation: {loc.elevation:.0f}m")
            if loc.timezone:
                self.output_stream.write(f" | Timezone: {loc.timezone}")
            self.output_stream.write("\n")
        
        self.output_stream.write("\n")
        
        # Table header
        header = f"{'Date':<12} {'Max Temp':<10} {'Min Temp':<10} {'Avg Temp':<10} {'Precip':<8} {'Sunshine':<10} {'Wind Speed':<12} {'Weather':<8}"
        self.output_stream.write(header + "\n")
        self.output_stream.write("-" * len(header) + "\n")
        
        # Data rows
        for item in weather_data_list.data:
            date_str = self._format_date(item.time)
            max_temp = self._format_temperature(item.temperature_2m_max)
            min_temp = self._format_temperature(item.temperature_2m_min)
            avg_temp = self._format_temperature(item.temperature_2m_mean)
            precip = self._format_precipitation(item.precipitation_sum)
            sunshine = self._format_sunshine(item.sunshine_hours)
            wind_speed = self._format_wind_speed(item.wind_speed_10m)
            weather_code = self._format_weather_code(item.weather_code)
            
            row = f"{date_str:<12} {max_temp:<10} {min_temp:<10} {avg_temp:<10} {precip:<8} {sunshine:<10} {wind_speed:<12} {weather_code:<8}"
            self.output_stream.write(row + "\n")
        
        self.output_stream.write("\n" + "="*80 + "\n")
        self.output_stream.write(f"Total records: {weather_data_list.total_count}\n")
        self.output_stream.write("="*80 + "\n\n")
    
    def display_weather_data_json(self, weather_data_list: WeatherDataListResponseDTO) -> None:
        """Display weather data in JSON format."""
        data = self.format_weather_data_list_dto(weather_data_list)
        output = self.format_success(data)
        json_output = json.dumps(output, indent=2, ensure_ascii=False)
        self.output_stream.write(json_output + "\n")
    
    def display_error(self, error_message: str, error_code: str = "WEATHER_ERROR", json_output: bool = False) -> None:
        """Display error message for CLI."""
        if json_output:
            error_data = self.format_error(error_message, error_code)
            json_str = json.dumps(error_data, indent=2, ensure_ascii=False)
            self.output_stream.write(json_str + "\n")
        else:
            try:
                self.output_stream.write(f"\n❌ Error [{error_code}]: {error_message}\n\n")
            except UnicodeEncodeError:
                # Fallback for systems that don't support Unicode emojis
                self.output_stream.write(f"\n[ERROR] {error_code}: {error_message}\n\n")
    
    def display_success_message(self, message: str) -> None:
        """Display success message for CLI."""
        try:
            self.output_stream.write(f"\n✅ {message}\n\n")
        except UnicodeEncodeError:
            # Fallback for systems that don't support Unicode emojis
            self.output_stream.write(f"\n[SUCCESS] {message}\n\n")
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            # Fallback to first 10 characters if it looks like a date
            if len(date_str) >= 10 and date_str[4] == '-' and date_str[7] == '-':
                return date_str[:10]
            return date_str  # Return original string for completely invalid formats
    
    def _format_temperature(self, temp: float) -> str:
        """Format temperature for display."""
        if temp is None:
            return "N/A"
        return f"{temp:.1f}°C"
    
    def _format_precipitation(self, precip: float) -> str:
        """Format precipitation for display."""
        if precip is None:
            return "N/A"
        return f"{precip:.1f}mm"
    
    def _format_sunshine(self, sunshine: float) -> str:
        """Format sunshine duration for display."""
        if sunshine is None:
            return "N/A"
        return f"{sunshine:.1f}h"
    
    def _format_wind_speed(self, wind_speed: float) -> str:
        """Format wind speed for display."""
        if wind_speed is None:
            return "N/A"
        return f"{wind_speed:.1f}km/h"
    
    def _format_weather_code(self, weather_code: int) -> str:
        """Format weather code for display."""
        if weather_code is None:
            return "N/A"
        return str(weather_code)
