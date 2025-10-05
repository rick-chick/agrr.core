"""Predict weather input port interface."""

from abc import ABC, abstractmethod

from agrr_core.usecase.dto.prediction_request_dto import PredictionRequestDTO
from agrr_core.usecase.dto.prediction_response_dto import PredictionResponseDTO


class PredictWeatherInputPort(ABC):
    """Interface for predict weather interactor operations."""
    
    @abstractmethod
    async def execute(self, request: PredictionRequestDTO) -> PredictionResponseDTO:
        """Execute weather prediction."""
        pass
