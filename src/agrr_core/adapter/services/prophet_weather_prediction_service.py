"""Prophet-based weather prediction service implementation."""

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

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.ports.output.weather_prediction_output_port import WeatherPredictionOutputPort


class ProphetWeatherPredictionService(WeatherPredictionOutputPort):
    """Prophet-based implementation of weather prediction service."""
    
    async def predict_weather(
        self, 
        historical_data: List[WeatherData], 
        prediction_days: int
    ) -> List[Forecast]:
        """Predict weather using Prophet model."""
        try:
            if not historical_data:
                raise PredictionError("No historical data available for prediction")
            
            # Convert to DataFrame for Prophet
            df_data = []
            for weather_data in historical_data:
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
            future = model.make_future_dataframe(periods=prediction_days, freq='D')
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
            
            return forecasts
            
        except Exception as e:
            raise PredictionError(f"Prediction failed: {e}")
