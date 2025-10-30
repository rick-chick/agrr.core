"""Task schedule generation interactor.

Use case interactor for generating task schedules using LLM gateway.
"""

from agrr_core.usecase.gateways.task_schedule_generation_gateway import TaskScheduleGenerationGateway
from agrr_core.usecase.dto.task_schedule_generation_request_dto import TaskScheduleGenerationRequestDTO
from agrr_core.entity.entities.task_schedule_result_entity import TaskScheduleResult

class TaskScheduleGenerationInteractor:
    """Interactor for task schedule generation.
    
    This interactor orchestrates the task schedule generation process
    using the gateway and handles business logic.
    """
    
    def __init__(self, gateway: TaskScheduleGenerationGateway):
        """Initialize interactor.
        
        Args:
            gateway: Task schedule generation gateway
        """
        self.gateway = gateway
    
    def execute(self, request: TaskScheduleGenerationRequestDTO) -> TaskScheduleResult:
        """Generate task schedule for a crop.
        
        Args:
            request: Task schedule generation request
            
        Returns:
            Generated task schedule result
            
        Raises:
            ValueError: If request is invalid
            RuntimeError: If generation fails
        """
        # Validate request
        if not request.validate():
            raise ValueError("Invalid request data")
        
        try:
            # Generate task schedule using gateway
            result = self.gateway.generate_task_schedule(
                crop_name=request.crop_name,
                variety=request.variety,
                stage_requirements=request.stage_requirements,
                agricultural_tasks=request.agricultural_tasks
            )
            
            # Validate generated result
            if not self.gateway.validate_task_schedule(result):
                raise RuntimeError("Generated task schedule is invalid")
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Task schedule generation failed: {str(e)}")
    
    def generate_for_crop(
        self,
        crop_name: str,
        variety: str,
        stage_requirements: list,
        agricultural_tasks: list
    ) -> TaskScheduleResult:
        """Generate task schedule for a crop (convenience method).
        
        Args:
            crop_name: Name of the crop
            variety: Variety name
            stage_requirements: List of stage requirements
            agricultural_tasks: List of agricultural tasks
            
        Returns:
            Generated task schedule result
        """
        request = TaskScheduleGenerationRequestDTO(
            crop_name=crop_name,
            variety=variety,
            stage_requirements=stage_requirements,
            agricultural_tasks=agricultural_tasks
        )
        
        return self.execute(request)
