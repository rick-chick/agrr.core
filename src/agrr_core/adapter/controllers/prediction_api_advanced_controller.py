"""Advanced prediction controller implementation for adapter layer."""

from typing import Dict, Any

from agrr_core.usecase.ports.input.multi_metric_prediction_input_port import MultiMetricPredictionInputPort
from agrr_core.usecase.ports.input.model_evaluation_input_port import ModelEvaluationInputPort
from agrr_core.usecase.ports.input.batch_prediction_input_port import BatchPredictionInputPort
from agrr_core.usecase.ports.input.model_management_input_port import ModelManagementInputPort
from agrr_core.usecase.dto.prediction_config_dto import (
    MultiMetricPredictionRequestDTO,
    ModelEvaluationRequestDTO,
    BatchPredictionRequestDTO
)


class PredictionAPIAdvancedController:
    """Implementation of advanced prediction controller."""
    
    def __init__(
        self,
        multi_metric_prediction_input_port: MultiMetricPredictionInputPort,
        model_evaluation_input_port: ModelEvaluationInputPort,
        batch_prediction_input_port: BatchPredictionInputPort,
        model_management_input_port: ModelManagementInputPort
    ):
        self.multi_metric_prediction_input_port = multi_metric_prediction_input_port
        self.model_evaluation_input_port = model_evaluation_input_port
        self.batch_prediction_input_port = batch_prediction_input_port
        self.model_management_input_port = model_management_input_port
    
    async def execute_multi_metric_prediction(self, request: MultiMetricPredictionRequestDTO) -> Any:
        """Execute multi-metric weather prediction."""
        return await self.multi_metric_prediction_input_port.execute(request)
    
    async def execute_model_evaluation(self, request: ModelEvaluationRequestDTO) -> Any:
        """Execute model evaluation."""
        return await self.model_evaluation_input_port.execute(request)
    
    async def execute_batch_prediction(self, request: BatchPredictionRequestDTO) -> Any:
        """Execute batch prediction for multiple locations."""
        return await self.batch_prediction_input_port.execute(request)
    
    async def get_available_models(self) -> list:
        """Get available prediction models."""
        return await self.model_management_input_port.get_available_models()
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        return await self.model_management_input_port.get_model_info(model_type)
    
    async def compare_models(
        self,
        historical_data: list,
        test_data: list,
        metrics: list,
        model_configs: list
    ) -> Dict[str, Any]:
        """Compare performance of different models."""
        return await self.model_management_input_port.compare_models(
            historical_data, test_data, metrics, model_configs
        )
