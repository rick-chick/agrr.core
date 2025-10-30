"""Model management input port interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ModelManagementInputPort(ABC):
    """Interface for model management interactor operations."""
    
    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available prediction models."""
        pass
    
    @abstractmethod
    def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        pass
    
    @abstractmethod
    def compare_models(
        self,
        historical_data: List,
        test_data: List,
        metrics: List[str],
        model_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare performance of different models."""
        pass
