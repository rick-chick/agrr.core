"""Prediction presenter for formatting weather prediction responses."""

from typing import Dict, Any, List

from agrr_core.entity.entities.forecast import Forecast
from agrr_core.usecase.dto.prediction_response_dto import PredictionResponseDTO
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort


class PredictionPresenter(PredictionPresenterOutputPort):
    """Presenter for formatting weather prediction responses."""
    
    def format_forecast(self, forecast: Forecast) -> Dict[str, Any]:
        """Format a single forecast entity to response format."""
        return {
            "location": {
                "latitude": forecast.location.latitude,
                "longitude": forecast.location.longitude,
            },
            "date": forecast.date.isoformat(),
            "predicted_temperature": forecast.predicted_temperature,
            "predicted_humidity": forecast.predicted_humidity,
            "predicted_precipitation": forecast.predicted_precipitation,
            "predicted_wind_speed": forecast.predicted_wind_speed,
            "predicted_wind_direction": forecast.predicted_wind_direction,
            "confidence": forecast.confidence,
        }
    
    def format_forecast_list(self, forecast_list: List[Forecast]) -> Dict[str, Any]:
        """Format a list of forecast entities to response format."""
        return {
            "forecasts": [self.format_forecast(forecast) for forecast in forecast_list],
            "count": len(forecast_list),
        }
    
    def format_prediction_dto(self, dto: PredictionResponseDTO) -> Dict[str, Any]:
        """Format prediction DTO to response format."""
        return {
            "historical_data": dto.historical_data,
            "forecast": dto.forecast,
            "model_metrics": dto.model_metrics,
        }
    
    def format_error(self, error_message: str, error_code: str = "PREDICTION_ERROR") -> Dict[str, Any]:
        """Format error response."""
        return {
            "error": {
                "code": error_code,
                "message": error_message,
            },
            "success": False,
        }
    
    def format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format success response with data."""
        return {
            "success": True,
            "data": data,
        }
