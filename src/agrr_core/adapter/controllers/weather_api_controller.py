"""Weather controller for handling weather-related requests."""

from typing import Dict, Any

from agrr_core.adapter.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository
from agrr_core.adapter.services.prediction_integrated_service import PredictionIntegratedService


class WeatherAPIController:
    """Controller for weather-related operations."""
    
    def __init__(
        self,
        weather_repository: WeatherAPIOpenMeteoRepository,
        prediction_service: PredictionIntegratedService
    ):
        self.weather_repository = weather_repository
        self.prediction_service = prediction_service
    
    async def get_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Get weather data for specified location and date range."""
        try:
            weather_data_list, location = await self.weather_repository.get_weather_data_by_location_and_date_range(
                latitude, longitude, start_date, end_date
            )
            
            return {
                'success': True,
                'data': {
                    'data': weather_data_list,
                    'total_count': len(weather_data_list),
                    'location': {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'elevation': location.elevation,
                        'timezone': location.timezone
                    }
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'WEATHER_DATA_ERROR'
                }
            }
    
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
            # First get historical data for training
            weather_data_list, location = await self.weather_repository.get_weather_data_by_location_and_date_range(
                latitude, longitude, start_date, end_date
            )
            
            if not weather_data_list:
                return {
                    'success': False,
                    'error': {
                        'message': 'No historical data available for prediction',
                        'code': 'NO_HISTORICAL_DATA'
                    }
                }
            
            # Use prediction service for forecasting
            model_config = {
                'model_type': 'prophet',
                'prediction_days': prediction_days
            }
            
            metrics = ['temperature', 'precipitation']
            predictions = await self.prediction_service.predict_multiple_metrics(
                weather_data_list, metrics, model_config
            )
            
            return {
                'success': True,
                'data': {
                    'predictions': predictions,
                    'historical_data_count': len(weather_data_list),
                    'location': {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'elevation': location.elevation,
                        'timezone': location.timezone
                    }
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': {
                    'message': str(e),
                    'code': 'PREDICTION_ERROR'
                }
            }
    
    def get_weather_data_sync(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Synchronous version of get_weather_data."""
        import asyncio
        return asyncio.run(self.get_weather_data(latitude, longitude, start_date, end_date))
    
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
