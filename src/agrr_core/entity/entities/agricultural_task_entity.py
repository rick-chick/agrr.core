"""Agricultural task entity.

Represents an agricultural task with execution conditions and time requirements.
This entity models the basic information needed for task scheduling.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AgriculturalTask:
    """Represents an agricultural task with execution conditions.
    
    Fields:
    - task_id: Unique identifier for the task
    - task_name: Human-readable task name
    - description: Task description
    - time_per_sqm: Time required per square meter (hours)
    - weather_dependency: Weather dependency level (high/medium/low)
    - precipitation_max: Maximum precipitation for execution (mm)
    - wind_speed_max: Maximum wind speed for execution (m/s)
    - temperature_min: Minimum temperature for execution (℃) - optional
    - temperature_max: Maximum temperature for execution (℃) - optional
    """
    
    task_id: str
    task_name: str
    description: str
    time_per_sqm: float
    weather_dependency: str
    precipitation_max: float
    wind_speed_max: float
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    
    def is_weather_dependent(self) -> bool:
        """Return True if task is weather dependent."""
        return self.weather_dependency in ["high", "medium"]
    
    def can_execute_in_weather(self, precipitation: float, wind_speed: float, temperature: Optional[float] = None) -> bool:
        """Check if task can be executed in given weather conditions.
        
        Args:
            precipitation: Current precipitation (mm)
            wind_speed: Current wind speed (m/s)
            temperature: Current temperature (℃) - optional
            
        Returns:
            True if task can be executed, False otherwise
        """
        # Check precipitation
        if precipitation > self.precipitation_max:
            return False
        
        # Check wind speed
        if wind_speed > self.wind_speed_max:
            return False
        
        # Check temperature if specified
        if temperature is not None and self.temperature_min is not None:
            if temperature < self.temperature_min:
                return False
        
        if temperature is not None and self.temperature_max is not None:
            if temperature > self.temperature_max:
                return False
        
        return True
