"""Task schedule generation request DTO.

Data transfer object for task schedule generation requests.
"""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass(frozen=True)
class TaskScheduleGenerationRequestDTO:
    """Request DTO for task schedule generation.
    
    Fields:
    - crop_name: Name of the crop
    - variety: Variety name
    - stage_requirements: List of stage requirements
    - agricultural_tasks: List of agricultural tasks
    """
    
    crop_name: str
    variety: str
    stage_requirements: List[Dict[str, Any]]
    agricultural_tasks: List[Dict[str, Any]]
    
    def get_stage_orders(self) -> List[int]:
        """Get list of stage orders from stage requirements.
        
        Returns:
            List of stage order numbers
        """
        return [req.get("stage", {}).get("order", 0) for req in self.stage_requirements]
    
    def get_task_ids(self) -> List[str]:
        """Get list of task IDs from agricultural tasks.
        
        Returns:
            List of task IDs
        """
        return [task.get("task_id", "") for task in self.agricultural_tasks]
    
    def validate(self) -> bool:
        """Validate the request data.
        
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not self.crop_name or not self.variety:
            return False
        
        # Check stage requirements
        if not self.stage_requirements:
            return False
        
        # Check agricultural tasks
        if not self.agricultural_tasks:
            return False
        
        # Check task IDs are unique
        task_ids = self.get_task_ids()
        if len(task_ids) != len(set(task_ids)):
            return False
        
        return True
