"""Advanced prediction controller implementation for adapter layer."""

from typing import Dict, Any

from agrr_core.usecase.ports.input.advanced_prediction_input_port import AdvancedPredictionInputPort
from agrr_core.usecase.interactors.advanced_predict_weather_interactor import AdvancedPredictWeatherInteractor
from agrr_core.usecase.dto.prediction_config_dto import (
    MultiMetricPredictionRequestDTO,
    ModelEvaluationRequestDTO,
    BatchPredictionRequestDTO
)


class AdvancedPredictionController:
    """Implementation of advanced prediction controller."""
    
    def __init__(self, interactor: AdvancedPredictWeatherInteractor):
        self.interactor = interactor
    
    async def execute_multi_metric_prediction(self, request: MultiMetricPredictionRequestDTO) -> Any:
        """Execute multi-metric weather prediction."""
        return await self.interactor.execute_multi_metric_prediction(request)
    
    async def execute_model_evaluation(self, request: ModelEvaluationRequestDTO) -> Any:
        """Execute model evaluation."""
        return await self.interactor.execute_model_evaluation(request)
    
    async def execute_batch_prediction(self, request: BatchPredictionRequestDTO) -> Any:
        """Execute batch prediction for multiple locations."""
        return await self.interactor.execute_batch_prediction(request)
    
    async def get_available_models(self) -> list:
        """Get available prediction models."""
        return await self.interactor.get_available_models()
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        return await self.interactor.get_model_info(model_type)
    
    async def compare_models(
        self,
        historical_data: list,
        test_data: list,
        metrics: list,
        model_configs: list
    ) -> Dict[str, Any]:
        """Compare performance of different models."""
        return await self.interactor.compare_models(historical_data, test_data, metrics, model_configs)
