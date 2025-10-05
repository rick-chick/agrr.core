"""Batch prediction input port interface."""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.batch_prediction_request_dto import BatchPredictionRequestDTO
from agrr_core.usecase.dto.batch_prediction_response_dto import BatchPredictionResponseDTO


class BatchPredictionInputPort(ABC):
    """Interface for batch prediction interactor operations."""
    
    @abstractmethod
    async def execute(self, request: BatchPredictionRequestDTO) -> BatchPredictionResponseDTO:
        """Execute batch prediction for multiple locations."""
        pass
