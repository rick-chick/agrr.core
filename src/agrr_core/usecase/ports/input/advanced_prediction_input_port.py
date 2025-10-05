"""Advanced weather prediction input port interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

from agrr_core.usecase.dto.advanced_prediction_response_dto import AdvancedPredictionResponseDTO
from agrr_core.usecase.dto.model_accuracy_dto import ModelAccuracyDTO
from agrr_core.usecase.dto.batch_prediction_response_dto import BatchPredictionResponseDTO
from agrr_core.usecase.dto.multi_metric_prediction_request_dto import MultiMetricPredictionRequestDTO
from agrr_core.usecase.dto.model_evaluation_request_dto import ModelEvaluationRequestDTO
from agrr_core.usecase.dto.batch_prediction_request_dto import BatchPredictionRequestDTO


class AdvancedPredictionInputPort(ABC):
    """Interface for advanced weather prediction interactor operations."""
    
    @abstractmethod
    async def execute_multi_metric_prediction(self, request: MultiMetricPredictionRequestDTO) -> AdvancedPredictionResponseDTO:
        """Execute multi-metric weather prediction."""
        pass
    
    @abstractmethod
    async def execute_model_evaluation(self, request: ModelEvaluationRequestDTO) -> ModelAccuracyDTO:
        """Execute model evaluation."""
        pass
    
    @abstractmethod
    async def execute_batch_prediction(self, request: BatchPredictionRequestDTO) -> BatchPredictionResponseDTO:
        """Execute batch prediction for multiple locations."""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available prediction models."""
        pass
    
    @abstractmethod
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        pass
    
    @abstractmethod
    async def compare_models(
        self,
        historical_data: List,
        test_data: List,
        metrics: List[str],
        model_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare performance of different models."""
        pass
