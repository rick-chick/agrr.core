"""Prediction service implementation for adapter layer."""

from typing import Dict, Any

from agrr_core.adapter.interfaces.prediction_service_interface import PredictionServiceInterface
from agrr_core.usecase.interactors.predict_weather_interactor import PredictWeatherInteractor
from agrr_core.usecase.dto.prediction_request_dto import PredictionRequestDTO
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_error import WeatherError
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError


class PredictionServiceImpl(PredictionServiceInterface):
    """Implementation of prediction service for adapter layer."""
    
    def __init__(self, predict_weather_interactor: PredictWeatherInteractor):
        self.predict_weather_interactor = predict_weather_interactor
    
    async def predict_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        prediction_days: int = 365
    ) -> Dict[str, Any]:
        """Predict weather for specified location and date range."""
        try:
            request = PredictionRequestDTO(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                prediction_days=prediction_days
            )
            
            result = await self.predict_weather_interactor.execute(request)
            
            return {
                "success": True,
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
                "forecast": [
                    {
                        "date": item.date,
                        "predicted_value": item.predicted_value,
                        "confidence_lower": item.confidence_lower,
                        "confidence_upper": item.confidence_upper,
                    }
                    for item in result.forecast
                ],
                "model_metrics": result.model_metrics
            }
            
        except InvalidLocationError as e:
            return {
                "success": False,
                "error": "Invalid location parameters",
                "message": str(e)
            }
        except InvalidDateRangeError as e:
            return {
                "success": False,
                "error": "Invalid date range parameters",
                "message": str(e)
            }
        except PredictionError as e:
            return {
                "success": False,
                "error": "Prediction error",
                "message": str(e)
            }
        except WeatherAPIError as e:
            return {
                "success": False,
                "error": "Weather API error",
                "message": str(e)
            }
        except WeatherError as e:
            return {
                "success": False,
                "error": "Weather service error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Internal server error",
                "message": str(e)
            }
    
    def predict_weather_sync(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        prediction_days: int = 365
    ) -> Dict[str, Any]:
        """Synchronous version of predict_weather."""
        import asyncio
        return asyncio.run(self.predict_weather(latitude, longitude, start_date, end_date, prediction_days))
