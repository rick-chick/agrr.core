"""Task schedule generation gateway interface.

Abstract gateway for task schedule generation operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from agrr_core.entity.entities.task_schedule_result_entity import TaskScheduleResult

class TaskScheduleGenerationGateway(ABC):
    """Abstract gateway for task schedule generation.
    
    This gateway defines the interface for generating task schedules
    using LLM and other external services.
    """
    
    @abstractmethod
    def generate_task_schedule(
        self,
        crop_name: str,
        variety: str,
        stage_requirements: List[Dict[str, Any]],
        agricultural_tasks: List[Dict[str, Any]]
    ) -> TaskScheduleResult:
        """Generate task schedule for a crop.
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            stage_requirements: List of stage requirements
            agricultural_tasks: List of agricultural tasks
            
        Returns:
            Generated task schedule result
        """
        raise NotImplementedError
    
    @abstractmethod
    def validate_task_schedule(self, task_schedule: TaskScheduleResult) -> bool:
        """Validate generated task schedule.
        
        Args:
            task_schedule: Task schedule to validate
            
        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError
