"""Prediction presenter output port interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from agrr_core.entity.entities.forecast import Forecast
from agrr_core.usecase.dto.prediction_response_dto import PredictionResponseDTO


class PredictionPresenterOutputPort(ABC):
    """Interface for weather prediction presentation output operations."""
    
    @abstractmethod
    def format_forecast(self, forecast: Forecast) -> Dict[str, Any]:
        """Format a single forecast entity to response format."""
        pass
    
    @abstractmethod
    def format_prediction_dto(self, dto: PredictionResponseDTO) -> Dict[str, Any]:
        """Format prediction DTO to response format."""
        pass
    
    @abstractmethod
    def format_error(self, error_message: str, error_code: str = "PREDICTION_ERROR") -> Dict[str, Any]:
        """Format error response."""
        pass
    
    @abstractmethod
    def format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format success response with data."""
        pass
