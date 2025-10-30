"""Model evaluation input port interface."""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.model_evaluation_request_dto import ModelEvaluationRequestDTO
from agrr_core.usecase.dto.model_accuracy_dto import ModelAccuracyDTO

class ModelEvaluationInputPort(ABC):
    """Interface for model evaluation interactor operations."""
    
    @abstractmethod
    def execute(self, request: ModelEvaluationRequestDTO) -> ModelAccuracyDTO:
        """Execute model evaluation."""
        pass
