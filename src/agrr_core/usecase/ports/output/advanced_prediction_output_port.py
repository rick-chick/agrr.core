"""Advanced weather prediction output port interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from agrr_core.usecase.dto.advanced_prediction_response_dto import AdvancedPredictionResponseDTO
from agrr_core.usecase.dto.model_accuracy_dto import ModelAccuracyDTO
from agrr_core.usecase.dto.batch_prediction_response_dto import BatchPredictionResponseDTO


class AdvancedPredictionOutputPort(ABC):
    """Interface for advanced weather prediction presenter operations."""
    
    @abstractmethod
    async def present_prediction_result(self, result: AdvancedPredictionResponseDTO) -> Dict[str, Any]:
        """Present prediction result in appropriate format."""
        pass
    
    @abstractmethod
    async def present_model_evaluation(self, evaluation: ModelAccuracyDTO) -> Dict[str, Any]:
        """Present model evaluation result in appropriate format."""
        pass
    
    @abstractmethod
    async def present_batch_prediction_result(self, result: BatchPredictionResponseDTO) -> Dict[str, Any]:
        """Present batch prediction result in appropriate format."""
        pass
    
    @abstractmethod
    async def present_model_list(self, models: list) -> Dict[str, Any]:
        """Present list of available models."""
        pass
    
    @abstractmethod
    async def present_model_info(self, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Present model information."""
        pass
