"""Use case interactor for weather prediction from data."""

from typing import List
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast
from agrr_core.entity.validators.weather_validator import WeatherValidator
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.prediction_gateway import PredictionGateway


class WeatherPredictInteractor:
    """Use case interactor for weather prediction from data."""
    
    def __init__(
        self,
        weather_gateway: WeatherGateway,
        prediction_gateway: PredictionGateway
    ):
        """Initialize weather prediction from data interactor."""
        self.weather_gateway = weather_gateway
        self.prediction_gateway = prediction_gateway
    
    async def execute(
        self,
        input_source: str,
        output_destination: str,
        prediction_days: int
    ) -> List[Forecast]:
        """
        Execute weather prediction from data.
        
        Args:
            input_source: Input data source (file path, database connection, etc.)
            output_destination: Output destination (file path, database, etc.)
            prediction_days: Number of days to predict
            
        Returns:
            List of forecast predictions
            
        Raises:
            ValueError: If validation fails
            FileError: If operations fail
        """
        # Validate input data source
        if not WeatherValidator.validate_source_format(input_source):
            raise ValueError("Invalid input data source format")
        
        # Validate output destination
        if not WeatherValidator.validate_destination_format(output_destination):
            raise ValueError("Invalid output destination format")
        
        # Get weather data from input source
        historical_data = await self.prediction_gateway.read_historical_data(input_source)
        
        # Validate weather data quality with detailed error information
        is_valid, error_message = WeatherValidator.validate_weather_data_detailed(historical_data)
        if not is_valid:
            raise ValueError(error_message)
        
        # Generate predictions
        predictions = await self.prediction_gateway.predict(
            historical_data, 
            'temperature', 
            {'prediction_days': prediction_days}
        )
        
        # Create predictions
        await self.prediction_gateway.create(predictions, output_destination)
        
        return predictions
