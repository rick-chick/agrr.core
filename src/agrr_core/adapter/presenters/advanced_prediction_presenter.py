"""Advanced prediction presenter implementation for adapter layer."""

from typing import Dict, Any

from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort
from agrr_core.usecase.dto.advanced_prediction_response_dto import (
    AdvancedPredictionResponseDTO,
    ModelAccuracyDTO,
    BatchPredictionResponseDTO
)

class PredictionAdvancedPresenter(AdvancedPredictionOutputPort):
    """Implementation of advanced prediction presenter."""
    
    async def present_prediction_result(self, result: AdvancedPredictionResponseDTO) -> Dict[str, Any]:
        """Present prediction result in appropriate format."""
        return {
            "success": True,
            "data": {
                "historical_data": [
                    {
                        "time": item.time,
                        "temperature_2m_max": item.temperature_2m_max,
                        "temperature_2m_min": item.temperature_2m_min,
                        "temperature_2m_mean": item.temperature_2m_mean,
                        "precipitation_sum": item.precipitation_sum,
                        "sunshine_duration": item.sunshine_duration,
                        "sunshine_hours": item.sunshine_hours,
                    }
                    for item in result.historical_data
                ],
                "forecasts": {
                    metric: [
                        {
                            "date": forecast.date,
                            "predicted_value": forecast.predicted_value,
                            "confidence_lower": forecast.confidence_lower,
                            "confidence_upper": forecast.confidence_upper
                        }
                        for forecast in forecasts
                    ]
                    for metric, forecasts in result.forecasts.items()
                },
                "model_metrics": result.model_metrics,
                "prediction_metadata": result.prediction_metadata
            }
        }
    
