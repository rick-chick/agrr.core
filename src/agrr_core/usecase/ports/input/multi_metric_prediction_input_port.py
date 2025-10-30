"""Multi-metric weather prediction input port interface."""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.multi_metric_prediction_request_dto import MultiMetricPredictionRequestDTO
from agrr_core.usecase.dto.advanced_prediction_response_dto import AdvancedPredictionResponseDTO

class MultiMetricPredictionInputPort(ABC):
    """Interface for multi-metric weather prediction interactor operations."""
    
    @abstractmethod
    def execute(self, request: MultiMetricPredictionRequestDTO) -> AdvancedPredictionResponseDTO:
        """Execute multi-metric weather prediction."""
        pass
