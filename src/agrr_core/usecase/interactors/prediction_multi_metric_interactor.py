"""Multi-metric weather prediction interactor."""

from typing import Dict, Any
from datetime import datetime

from agrr_core.entity import Location, DateRange
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.gateways.weather_data_gateway import WeatherDataGateway
from agrr_core.usecase.gateways.model_config_gateway import ModelConfigGateway
from agrr_core.usecase.gateways.prediction_model_gateway import PredictionModelGateway
from agrr_core.usecase.ports.input.multi_metric_prediction_input_port import MultiMetricPredictionInputPort
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort
from agrr_core.usecase.dto.multi_metric_prediction_request_dto import MultiMetricPredictionRequestDTO
from agrr_core.usecase.dto.advanced_prediction_response_dto import AdvancedPredictionResponseDTO
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.forecast_response_dto import ForecastResponseDTO

class MultiMetricPredictionInteractor(MultiMetricPredictionInputPort):
    """Interactor for multi-metric weather prediction."""
    
    def __init__(
        self, 
        weather_data_gateway: WeatherDataGateway,
        model_config_gateway: ModelConfigGateway,
        prediction_model_gateway: PredictionModelGateway,
        prediction_presenter_output_port: PredictionPresenterOutputPort
    ):
        self.weather_data_gateway = weather_data_gateway
        self.model_config_gateway = model_config_gateway
        self.prediction_model_gateway = prediction_model_gateway
        self.prediction_presenter_output_port = prediction_presenter_output_port
    
    def execute(self, request: MultiMetricPredictionRequestDTO) -> AdvancedPredictionResponseDTO:
        """Execute multi-metric weather prediction."""
        try:
            # Validate location
            location = Location(request.latitude, request.longitude)
            
            # Validate date range
            date_range = DateRange(request.start_date, request.end_date)
            
            # Get historical weather data
            historical_data_list, actual_location = self.weather_data_gateway.get_weather_data_by_location_and_date_range(
                location.latitude,
                location.longitude,
                date_range.start_date,
                date_range.end_date
            )
            
            if not historical_data_list:
                raise PredictionError("No historical data available for prediction")
            
            # Prepare model configuration
            model_config = {
                'model_type': request.config.model_type,
                'prediction_days': request.prediction_days,
                'seasonality': request.config.seasonality,
                'trend': request.config.trend,
                'custom_params': request.config.custom_params,
                'confidence_level': request.config.confidence_level,
                'validation_split': request.config.validation_split
            }
            
            # Use advanced prediction service to generate forecasts
            forecasts_dict = self.prediction_model_gateway.predict_multiple_metrics(
                historical_data_list, 
                request.metrics,
                model_config
            )
            
            # Save forecasts with metadata
            metadata = {
                'model_type': request.config.model_type,
                'location': {
                    'latitude': actual_location.latitude,
                    'longitude': actual_location.longitude,
                    'name': getattr(actual_location, 'name', request.location_name)
                },
                'prediction_date': datetime.now().isoformat(),
                'metrics': request.metrics,
                'config': model_config
            }
            
            all_forecasts = []
            for metric, forecasts in forecasts_dict.items():
                all_forecasts.extend(forecasts)
            
            self.model_config_gateway.save_forecast_with_metadata(
                all_forecasts, metadata
            )
            
            # Convert historical data to response DTOs
            historical_response = []
            for weather_data in historical_data_list:
                response_dto = WeatherDataResponseDTO(
                    time=weather_data.time.isoformat(),
                    temperature_2m_max=weather_data.temperature_2m_max,
                    temperature_2m_min=weather_data.temperature_2m_min,
                    temperature_2m_mean=weather_data.temperature_2m_mean,
                    precipitation_sum=weather_data.precipitation_sum,
                    sunshine_duration=weather_data.sunshine_duration,
                    sunshine_hours=weather_data.sunshine_hours,
                )
                historical_response.append(response_dto)
            
            # Convert forecasts to response DTOs
            forecasts_response = {}
            for metric, forecasts in forecasts_dict.items():
                forecast_list = []
                for forecast in forecasts:
                    forecast_dto = ForecastResponseDTO(
                        date=forecast.date.isoformat(),
                        predicted_value=forecast.predicted_value,
                        confidence_lower=forecast.confidence_lower,
                        confidence_upper=forecast.confidence_upper
                    )
                    forecast_list.append(forecast_dto)
                forecasts_response[metric] = forecast_list
            
            # Prepare model metrics
            model_metrics = {
                'training_data_points': len(historical_data_list),
                'prediction_days': request.prediction_days,
                'model_type': request.config.model_type,
                'metrics_predicted': request.metrics,
                'location': metadata['location']
            }
            
            response_dto = AdvancedPredictionResponseDTO(
                historical_data=historical_response,
                forecasts=forecasts_response,
                model_metrics=model_metrics,
                prediction_metadata=metadata
            )
            
            return response_dto
            
        except (ValueError, InvalidLocationError, InvalidDateRangeError) as e:
            raise PredictionError(f"Invalid request parameters: {e}")
        except Exception as e:
            raise PredictionError(f"Prediction failed: {e}")
