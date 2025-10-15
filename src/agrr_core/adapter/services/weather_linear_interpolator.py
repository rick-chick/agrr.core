"""Linear interpolation service for weather data (Adapter layer).

This service provides linear interpolation for missing weather data,
implementing the WeatherInterpolator interface.
"""

import numpy as np
from typing import Dict, List
from datetime import date, timedelta

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.gateways.weather_interpolator import WeatherInterpolator
from agrr_core.framework.services.utils.interpolation_service import InterpolationService


class WeatherLinearInterpolator(WeatherInterpolator):
    """Linear interpolation implementation for weather data.
    
    This class uses the shared InterpolationService to apply
    linear interpolation specifically to weather temperature data.
    
    Interpolation strategy (delegated to InterpolationService):
    1. For gaps at the beginning: use first valid value (forward fill)
    2. For gaps at the end: use last valid value (backward fill)
    3. For gaps in the middle: linear interpolation
    """
    
    def interpolate_temperature(
        self,
        weather_by_date: Dict[date, WeatherData],
        sorted_dates: List[date]
    ) -> Dict[date, WeatherData]:
        """Interpolate missing temperature values using linear interpolation.
        
        Args:
            weather_by_date: Dictionary mapping dates to weather data
            sorted_dates: List of dates in chronological order
            
        Returns:
            Dictionary with interpolated weather data (original is not modified)
        """
        # Create a copy to avoid modifying the original
        result = weather_by_date.copy()
        
        # Extract temperature values with proper handling of missing data
        temperatures = []
        for d in sorted_dates:
            if d in weather_by_date and weather_by_date[d].temperature_2m_mean is not None:
                temperatures.append(weather_by_date[d].temperature_2m_mean)
            else:
                temperatures.append(np.nan)
        
        # Apply linear interpolation using shared utility
        interpolated_temps = InterpolationService.interpolate_missing_values(temperatures)
        
        # Update weather data with interpolated values
        for i, d in enumerate(sorted_dates):
            if d not in result or result[d].temperature_2m_mean is None:
                # Create new WeatherData with interpolated temperature
                if d in result:
                    # Update existing data
                    original = result[d]
                    result[d] = WeatherData(
                        time=original.time,
                        temperature_2m_max=original.temperature_2m_max,
                        temperature_2m_min=original.temperature_2m_min,
                        temperature_2m_mean=interpolated_temps[i],
                        precipitation_sum=original.precipitation_sum,
                        sunshine_duration=original.sunshine_duration,
                        wind_speed_10m=original.wind_speed_10m,
                        weather_code=original.weather_code,
                    )
                else:
                    # Create new data for missing date
                    from datetime import datetime
                    result[d] = WeatherData(
                        time=datetime.combine(d, datetime.min.time()),
                        temperature_2m_mean=interpolated_temps[i],
                    )
        
        return result

