"""Weather use case interactors."""

from typing import List
import pandas as pd

try:
    from prophet import Prophet
except ImportError:
    # Mock Prophet for testing when not installed
    class Prophet:
        def __init__(self, **kwargs):
            pass
        def fit(self, df):
            pass
        def make_future_dataframe(self, periods, freq):
            return pd.DataFrame({'ds': pd.date_range(start='2024-01-01', periods=periods, freq=freq)})
        def predict(self, future):
            return future.assign(yhat=20.0, yhat_lower=18.0, yhat_upper=23.0)

from agrr_core.entity import WeatherData, Location, DateRange, Forecast
from agrr_core.entity.exceptions.weather_exceptions import (
    InvalidLocationError,
    InvalidDateRangeError,
    PredictionError,
)
from agrr_core.usecase.ports.output.weather_output_port import (
    WeatherDataOutputPort,
    WeatherPredictionOutputPort,
)
from agrr_core.usecase.dto.weather_dto import (
    WeatherDataRequestDTO,
    WeatherDataResponseDTO,
    WeatherDataListResponseDTO,
    PredictionRequestDTO,
    PredictionResponseDTO,
    ForecastResponseDTO,
)


class FetchWeatherDataInteractor:
    """Interactor for fetching weather data."""
    
    def __init__(self, weather_data_output_port: WeatherDataOutputPort):
        self.weather_data_output_port = weather_data_output_port
    
    async def execute(self, request: WeatherDataRequestDTO) -> WeatherDataListResponseDTO:
        """Execute weather data fetching."""
        try:
            # Validate location
            location = Location(request.latitude, request.longitude)
            
            # Validate date range
            date_range = DateRange(request.start_date, request.end_date)
            
            # Get weather data
            weather_data_list = await self.weather_data_output_port.get_weather_data_by_location_and_date_range(
                location.latitude,
                location.longitude,
                date_range.start_date,
                date_range.end_date
            )
            
            # Convert to response DTOs
            response_data = []
            for weather_data in weather_data_list:
                response_dto = WeatherDataResponseDTO(
                    time=weather_data.time.isoformat(),
                    temperature_2m_max=weather_data.temperature_2m_max,
                    temperature_2m_min=weather_data.temperature_2m_min,
                    temperature_2m_mean=weather_data.temperature_2m_mean,
                    precipitation_sum=weather_data.precipitation_sum,
                    sunshine_duration=weather_data.sunshine_duration,
                    sunshine_hours=weather_data.sunshine_hours,
                )
                response_data.append(response_dto)
            
            return WeatherDataListResponseDTO(
                data=response_data,
                total_count=len(response_data)
            )
            
        except (ValueError, InvalidLocationError, InvalidDateRangeError) as e:
            raise InvalidLocationError(f"Invalid request parameters: {e}")


class PredictWeatherInteractor:
    """Interactor for weather prediction."""
    
    def __init__(
        self, 
        weather_data_output_port: WeatherDataOutputPort,
        weather_prediction_output_port: WeatherPredictionOutputPort
    ):
        self.weather_data_output_port = weather_data_output_port
        self.weather_prediction_output_port = weather_prediction_output_port
    
    async def execute(self, request: PredictionRequestDTO) -> PredictionResponseDTO:
        """Execute weather prediction."""
        try:
            # Validate location
            location = Location(request.latitude, request.longitude)
            
            # Validate date range
            date_range = DateRange(request.start_date, request.end_date)
            
            # Get historical weather data
            historical_data_list = await self.weather_data_output_port.get_weather_data_by_location_and_date_range(
                location.latitude,
                location.longitude,
                date_range.start_date,
                date_range.end_date
            )
            
            if not historical_data_list:
                raise PredictionError("No historical data available for prediction")
            
            # Convert to DataFrame for Prophet
            df_data = []
            for weather_data in historical_data_list:
                if weather_data.temperature_2m_mean is not None:
                    df_data.append({
                        'ds': weather_data.time,
                        'y': weather_data.temperature_2m_mean
                    })
            
            if not df_data:
                raise PredictionError("No valid temperature data for prediction")
            
            df = pd.DataFrame(df_data)
            
            # Initialize and fit Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False
            )
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=request.prediction_days, freq='D')
            forecast = model.predict(future)
            
            # Get only future predictions
            future_forecast = forecast[forecast['ds'] > df['ds'].max()]
            
            # Convert forecast to entities
            forecasts = []
            for _, row in future_forecast.iterrows():
                forecast_entity = Forecast(
                    date=row['ds'],
                    predicted_value=row['yhat'],
                    confidence_lower=row.get('yhat_lower'),
                    confidence_upper=row.get('yhat_upper')
                )
                forecasts.append(forecast_entity)
            
            # Save forecasts
            await self.weather_prediction_output_port.save_forecast(forecasts)
            
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
            
            return PredictionResponseDTO(
                historical_data=historical_response,
                forecast=forecast_response,
                model_metrics={
                    'training_data_points': len(df),
                    'prediction_days': request.prediction_days,
                    'model_type': 'Prophet'
                }
            )
            
        except (ValueError, InvalidLocationError, InvalidDateRangeError) as e:
            raise InvalidLocationError(f"Invalid request parameters: {e}")
        except Exception as e:
            raise PredictionError(f"Prediction failed: {e}")
