"""Model management interactor."""

from typing import Dict, Any, List

from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.gateways.model_config_gateway import ModelConfigGateway
from agrr_core.usecase.gateways.prediction_model_gateway import PredictionModelGateway
from agrr_core.usecase.ports.input.model_management_input_port import ModelManagementInputPort


class ModelManagementInteractor(ModelManagementInputPort):
    """Interactor for model management operations."""
    
    def __init__(
        self, 
        model_config_gateway: ModelConfigGateway,
        prediction_model_gateway: PredictionModelGateway
    ):
        self.model_config_gateway = model_config_gateway
        self.prediction_model_gateway = prediction_model_gateway
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available prediction models."""
        try:
            models = await self.model_config_gateway.get_available_models()
            return [{"name": model, "type": model} for model in models]
        except Exception as e:
            raise PredictionError(f"Failed to get available models: {e}")
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        try:
            return await self.prediction_model_gateway.get_model_info(model_type)
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
