"""Task schedule result entity.

Represents the result of task schedule generation with crop information and schedules.
This entity models the complete output of the task schedule generation process.
"""

from dataclasses import dataclass
from typing import List

from agrr_core.entity.entities.task_schedule_entity import TaskSchedule


@dataclass(frozen=True)
class TaskScheduleResult:
    """Represents the result of task schedule generation.
    
    Fields:
    - crop_name: Name of the crop
    - variety: Variety name
    - task_schedules: List of task schedules
    - total_duration_days: Total estimated duration in days
    - weather_dependencies: List of weather dependency levels
    """
    
    crop_name: str
    variety: str
    task_schedules: List[TaskSchedule]
    total_duration_days: float
    weather_dependencies: List[str]
    
    def get_schedules_by_stage(self, stage_order: int) -> List[TaskSchedule]:
        """Get task schedules for a specific stage.
        
        Args:
            stage_order: Stage order number
            
        Returns:
            List of task schedules for the specified stage
        """
        return [schedule for schedule in self.task_schedules if schedule.stage_order == stage_order]
    
    def get_schedules_by_priority(self, priority: int) -> List[TaskSchedule]:
        """Get task schedules with a specific priority.
        
        Args:
            priority: Priority level
            
        Returns:
            List of task schedules with the specified priority
        """
        return [schedule for schedule in self.task_schedules if schedule.priority == priority]
    
    def get_startup_tasks(self) -> List[TaskSchedule]:
        """Get startup tasks (gdd_tolerance = 0).
        
        Returns:
            List of startup task schedules
        """
        return [schedule for schedule in self.task_schedules if schedule.is_startup_task()]
    
    def get_ongoing_tasks(self) -> List[TaskSchedule]:
        """Get ongoing tasks (gdd_tolerance > 0).
        
        Returns:
            List of ongoing task schedules
        """
        return [schedule for schedule in self.task_schedules if schedule.is_ongoing_task()]
    
    def get_high_priority_tasks(self) -> List[TaskSchedule]:
        """Get high priority tasks (priority <= 2).
        
        Returns:
            List of high priority task schedules
        """
        return [schedule for schedule in self.task_schedules if schedule.priority <= 2]
