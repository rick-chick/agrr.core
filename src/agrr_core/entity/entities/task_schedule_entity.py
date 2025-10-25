"""Task schedule entity.

Represents a scheduled agricultural task with GDD-based timing and execution conditions.
This entity models the execution plan for agricultural tasks.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class TaskSchedule:
    """Represents a scheduled agricultural task.
    
    Fields:
    - task_id: Identifier for the task
    - stage_order: Stage order number
    - gdd_trigger: GDD trigger point
    - gdd_tolerance: GDD tolerance range
    - priority: Execution priority
    - precipitation_max: Maximum precipitation for execution (mm)
    - wind_speed_max: Maximum wind speed for execution (m/s)
    - temperature_min: Minimum temperature for execution (℃) - optional
    - temperature_max: Maximum temperature for execution (℃) - optional
    - description: Task description
    """
    
    task_id: str
    stage_order: int
    gdd_trigger: float
    gdd_tolerance: float
    priority: int
    precipitation_max: float
    wind_speed_max: float
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    description: str = ""
    
    def is_startup_task(self) -> bool:
        """Return True if this is a startup task (gdd_tolerance = 0)."""
        return self.gdd_tolerance == 0
    
    def is_ongoing_task(self) -> bool:
        """Return True if this is an ongoing task (gdd_tolerance > 0)."""
        return self.gdd_tolerance > 0
    
    def get_execution_window(self) -> Tuple[float, float]:
        """Get the execution window (gdd_trigger - gdd_tolerance, gdd_trigger + gdd_tolerance).
        
        Returns:
            Tuple of (min_gdd, max_gdd) for execution window
        """
        return (self.gdd_trigger - self.gdd_tolerance, self.gdd_trigger + self.gdd_tolerance)
    
    def can_execute_at_gdd(self, current_gdd: float) -> bool:
        """Check if task can be executed at current GDD.
        
        Args:
            current_gdd: Current cumulative GDD
            
        Returns:
            True if task can be executed, False otherwise
        """
        min_gdd, max_gdd = self.get_execution_window()
        return min_gdd <= current_gdd <= max_gdd
