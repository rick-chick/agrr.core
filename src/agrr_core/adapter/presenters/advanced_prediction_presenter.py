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
    
    async def present_model_evaluation(self, evaluation: ModelAccuracyDTO) -> Dict[str, Any]:
        """Present model evaluation result in appropriate format."""
        return {
            "success": True,
            "data": {
                "model_type": evaluation.model_type,
                "metric": evaluation.metric,
                "mae": evaluation.mae,
                "mse": evaluation.mse,
                "rmse": evaluation.rmse,
                "mape": evaluation.mape,
                "r2_score": evaluation.r2_score,
                "evaluation_date": evaluation.evaluation_date,
                "test_data_points": evaluation.test_data_points
            }
        }
    
    async def present_batch_prediction_result(self, result: BatchPredictionResponseDTO) -> Dict[str, Any]:
        """Present batch prediction result in appropriate format."""
        return {
            "success": True,
            "data": {
                "results": [
                    {
                        "location": item["location"],
                        "prediction": await self.present_prediction_result(item["prediction"]),
                        "status": item["status"]
                    }
                    for item in result.results
                ],
                "summary": result.summary,
                "errors": result.errors,
                "processing_time": result.processing_time
            }
        }
    
    async def present_model_list(self, models: list) -> Dict[str, Any]:
        """Present list of available models."""
        return {
            "success": True,
            "data": {
                "models": models,
                "count": len(models)
            }
        }
    
    async def present_model_info(self, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Present model information."""
        return {
            "success": True,
            "data": model_info
        }
