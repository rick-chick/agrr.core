"""Model management interactor."""

from typing import Dict, Any, List

from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.gateways.weather_data_repository_gateway import WeatherDataRepositoryGateway
from agrr_core.usecase.gateways.prediction_service_gateway import PredictionServiceGateway
from agrr_core.usecase.ports.input.model_management_input_port import ModelManagementInputPort


class ModelManagementInteractor(ModelManagementInputPort):
    """Interactor for model management operations."""
    
    def __init__(
        self, 
        weather_data_repository_gateway: WeatherDataRepositoryGateway,
        prediction_service_gateway: PredictionServiceGateway
    ):
        self.weather_data_repository_gateway = weather_data_repository_gateway
        self.prediction_service_gateway = prediction_service_gateway
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available prediction models."""
        try:
            models = await self.weather_data_repository_gateway.get_available_models()
            return [{"name": model, "type": model} for model in models]
        except Exception as e:
            raise PredictionError(f"Failed to get available models: {e}")
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        try:
            return await self.prediction_service_gateway.get_model_info(model_type)
        except Exception as e:
            raise PredictionError(f"Failed to get model info for {model_type}: {e}")
    
    async def compare_models(
        self,
        historical_data: List,
        test_data: List,
        metrics: List[str],
        model_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare performance of different models."""
        try:
            # This would need to be implemented in the prediction service gateway
            raise PredictionError("Model comparison not yet implemented")
        except Exception as e:
            raise PredictionError(f"Model comparison failed: {e}")
