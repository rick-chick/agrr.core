"""Advanced prediction controller implementation for adapter layer."""

from typing import Dict, Any

from agrr_core.adapter.services.prediction_integrated_service import PredictionIntegratedService
from agrr_core.usecase.dto.prediction_config_dto import (
    MultiMetricPredictionRequestDTO,
    ModelEvaluationRequestDTO,
    BatchPredictionRequestDTO
)


class PredictionAPIAdvancedController:
    """Implementation of advanced prediction controller."""
    
    def __init__(self, prediction_service: PredictionIntegratedService):
        self.prediction_service = prediction_service
    
    async def execute_multi_metric_prediction(self, request: MultiMetricPredictionRequestDTO) -> Any:
        """Execute multi-metric weather prediction."""
        # Convert DTO to service parameters
        historical_data = request.historical_data
        metrics = request.metrics
        model_config = request.model_config
        
        return await self.prediction_service.predict_multiple_metrics(
            historical_data, metrics, model_config
        )
    
    async def execute_model_evaluation(self, request: ModelEvaluationRequestDTO) -> Any:
        """Execute model evaluation."""
        # Convert DTO to service parameters
        test_data = request.test_data
        predictions = request.predictions
        metric = request.metric
        
        return await self.prediction_service.evaluate_model_accuracy(
            test_data, predictions, metric
        )
    
    async def execute_batch_prediction(self, request: BatchPredictionRequestDTO) -> Any:
        """Execute batch prediction for multiple locations."""
        # Convert DTO to service parameters
        historical_data_list = request.historical_data_list
        model_config = request.model_config
        metrics = request.metrics
        
        return await self.prediction_service.batch_predict(
            historical_data_list, model_config, metrics
        )
    
    async def get_available_models(self) -> list:
        """Get available prediction models."""
        return await self.prediction_service.get_available_models()
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        return await self.prediction_service.get_model_info(model_type)
    
    async def compare_models(
        self,
        historical_data: list,
        test_data: list,
        metrics: list,
        model_configs: list
    ) -> Dict[str, Any]:
        """Compare performance of different models."""
        return await self.prediction_service.compare_models(
            historical_data, test_data, metrics, model_configs
        )
