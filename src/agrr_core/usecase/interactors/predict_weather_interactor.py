"""Predict weather interactor."""

from agrr_core.entity import Location, DateRange
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.ports.input.predict_weather_input_port import PredictWeatherInputPort
from agrr_core.usecase.gateways.weather_repository_gateway import WeatherRepositoryGateway
from agrr_core.usecase.gateways.prediction_repository_gateway import PredictionRepositoryGateway
from agrr_core.usecase.ports.output.weather_prediction_output_port import WeatherPredictionOutputPort
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.prediction_request_dto import PredictionRequestDTO
from agrr_core.usecase.dto.prediction_response_dto import PredictionResponseDTO
from agrr_core.usecase.dto.forecast_response_dto import ForecastResponseDTO


class PredictWeatherInteractor(PredictWeatherInputPort):
    """Interactor for weather prediction."""
    
    def __init__(
        self, 
        weather_repository_gateway: WeatherRepositoryGateway,
        prediction_repository_gateway: PredictionRepositoryGateway,
        weather_prediction_output_port: WeatherPredictionOutputPort,
        prediction_presenter_output_port: PredictionPresenterOutputPort
    ):
        self.weather_repository_gateway = weather_repository_gateway
        self.prediction_repository_gateway = prediction_repository_gateway
        self.weather_prediction_output_port = weather_prediction_output_port
        self.prediction_presenter_output_port = prediction_presenter_output_port
    
    async def execute(self, request: PredictionRequestDTO) -> None:
        """Execute weather prediction."""
        try:
            # Validate location
            location = Location(request.latitude, request.longitude)
            
            # Validate date range
            date_range = DateRange(request.start_date, request.end_date)
            
            # Get historical weather data (returns tuple of data and location)
            historical_data_list, actual_location = await self.weather_repository_gateway.get_weather_data_by_location_and_date_range(
                location.latitude,
                location.longitude,
                date_range.start_date,
                date_range.end_date
            )
            
            if not historical_data_list:
                raise PredictionError("No historical data available for prediction")
            
            # Use prediction service to generate forecasts
            forecasts = await self.weather_prediction_output_port.predict_weather(
                historical_data_list, 
                request.prediction_days
            )
            
            # Save forecasts
            await self.prediction_repository_gateway.save_forecast(forecasts)
            
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
            forecast_response = []
            for forecast in forecasts:
                forecast_dto = ForecastResponseDTO(
                    date=forecast.date.isoformat(),
                    predicted_value=forecast.predicted_value,
                    confidence_lower=forecast.confidence_lower,
                    confidence_upper=forecast.confidence_upper
                )
                forecast_response.append(forecast_dto)
            
            response_dto = PredictionResponseDTO(
                historical_data=historical_response,
                forecast=forecast_response,
                model_metrics={
                    'training_data_points': len(historical_data_list),
                    'prediction_days': request.prediction_days,
                    'model_type': 'Prophet'
                }
            )
            
            # Use presenter to format response
            formatted_response = self.prediction_presenter_output_port.format_prediction_dto(response_dto)
            return self.prediction_presenter_output_port.format_success(formatted_response)
            
        except (ValueError, InvalidLocationError, InvalidDateRangeError) as e:
            error_response = self.prediction_presenter_output_port.format_error(f"Invalid request parameters: {e}")
            return error_response
        except Exception as e:
            error_response = self.prediction_presenter_output_port.format_error(f"Prediction failed: {e}")
            return error_response
