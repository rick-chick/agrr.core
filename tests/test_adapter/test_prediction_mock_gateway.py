"""Tests for prediction mock gateway."""

import pytest
import json
import tempfile
from datetime import datetime, timedelta, date
from pathlib import Path

from agrr_core.adapter.gateways.prediction_mock_gateway import PredictionMockGateway
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast


class TestPredictionMockGateway:
    """Test cases for PredictionMockGateway."""
    
    def test_init(self):
        """Test gateway initialization."""
        gateway = PredictionMockGateway()
        assert gateway.mock_data_file is None
        assert gateway._mock_data_cache is None
    
    def test_init_with_mock_data_file(self):
        """Test gateway initialization with mock data file."""
        mock_file = "test_mock_data.json"
        gateway = PredictionMockGateway(mock_data_file=mock_file)
        assert gateway.mock_data_file == mock_file
    
    @pytest.mark.asyncio
    async def test_read_historical_data(self, tmp_path):
        """Test reading historical data from file."""
        gateway = PredictionMockGateway()
        
        # Create test JSON file
        test_data = {
            "latitude": 35.6762,
            "longitude": 139.6503,
            "data": [
                {
                    "time": "2024-01-01T00:00:00",
                    "temperature_2m_max": 25.0,
                    "temperature_2m_min": 15.0,
                    "temperature_2m_mean": 20.0,
                    "precipitation_sum": 0.0,
                    "sunshine_duration": 36000,
                    "wind_speed_10m": 5.0,
                    "weather_code": 0
                },
                {
                    "time": "2024-01-02T00:00:00",
                    "temperature_2m_max": 27.0,
                    "temperature_2m_min": 17.0,
                    "temperature_2m_mean": 22.0,
                    "precipitation_sum": 5.0,
                    "sunshine_duration": 28800,
                    "wind_speed_10m": 3.0,
                    "weather_code": 2
                }
            ]
        }
        
        test_file = tmp_path / "test_weather.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Call method
        result = await gateway.read_historical_data(str(test_file))
        
        # Assertions
        assert len(result) == 2
        assert isinstance(result[0], WeatherData)
        assert result[0].time == datetime(2024, 1, 1)
        assert result[0].temperature_2m_max == 25.0
        assert result[0].temperature_2m_min == 15.0
        assert result[0].temperature_2m_mean == 20.0
    
    @pytest.mark.asyncio
    async def test_create_predictions(self, tmp_path):
        """Test creating predictions file."""
        gateway = PredictionMockGateway()
        
        # Create test predictions
        test_predictions = [
            Forecast(
                date=date(2024, 1, 1),
                predicted_value=20.5,
                confidence_lower=18.0,
                confidence_upper=23.0
            ),
            Forecast(
                date=date(2024, 1, 2),
                predicted_value=22.0,
                confidence_lower=19.5,
                confidence_upper=24.5
            )
        ]
        
        # Create output file
        output_file = tmp_path / "test_predictions.json"
        await gateway.create(test_predictions, str(output_file))
        
        # Check that file was created
        assert output_file.exists()
        
        # Check file content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'predictions' in data
        assert 'model_type' in data
        assert 'prediction_days' in data
        assert 'metrics' in data
        
        assert data['model_type'] == 'Mock'
        assert data['prediction_days'] == 2
        assert data['metrics'] == ['temperature']
        
        # Check predictions
        predictions = data['predictions']
        assert len(predictions) == 2
        
        first_pred = predictions[0]
        assert first_pred['date'] == '2024-01-01'
        assert first_pred['predicted_value'] == 20.5
        assert first_pred['confidence_lower'] == 18.0
        assert first_pred['confidence_upper'] == 23.0
    
    @pytest.mark.asyncio
    async def test_predict_single_metric(self):
        """Test predicting single metric."""
        gateway = PredictionMockGateway()
        
        # Create test historical data
        historical_data = [
            WeatherData(
                time=datetime(2023, 6, 15),
                temperature_2m_max=28.0,
                temperature_2m_min=18.0,
                temperature_2m_mean=23.0,
                precipitation_sum=0.0,
                sunshine_duration=36000,
                wind_speed_10m=5.0,
                weather_code=0
            ),
            WeatherData(
                time=datetime(2023, 6, 16),
                temperature_2m_max=30.0,
                temperature_2m_min=20.0,
                temperature_2m_mean=25.0,
                precipitation_sum=2.0,
                sunshine_duration=28800,
                wind_speed_10m=3.0,
                weather_code=1
            )
        ]
        
        # Test configuration
        config = {'prediction_days': 3}
        
        # Call method
        result = await gateway.predict(
            historical_data=historical_data,
            metric='temperature',
            config=config
        )
        
        # Assertions
        assert len(result) == 3
        assert all(isinstance(p, Forecast) for p in result)
        
        # Check that predictions are for future dates
        tomorrow = datetime.now().date() + timedelta(days=1)
        for i, prediction in enumerate(result):
            expected_date = tomorrow + timedelta(days=i)
            assert prediction.date == expected_date
            assert prediction.predicted_value is not None
            assert prediction.confidence_lower is not None
            assert prediction.confidence_upper is not None
            assert prediction.confidence_lower <= prediction.predicted_value
            assert prediction.confidence_upper >= prediction.predicted_value
    
    @pytest.mark.asyncio
    async def test_predict_multiple_metrics(self):
        """Test predicting multiple metrics."""
        gateway = PredictionMockGateway()
        
        # Create test historical data
        historical_data = [
            WeatherData(
                time=datetime(2023, 6, 15),
                temperature_2m_max=28.0,
                temperature_2m_min=18.0,
                temperature_2m_mean=23.0,
                precipitation_sum=0.0,
                sunshine_duration=36000,
                wind_speed_10m=5.0,
                weather_code=0
            )
        ]
        
        # Test configuration
        config = {'prediction_days': 2}
        metrics = ['temperature', 'temperature_max', 'temperature_min']
        
        # Call method
        result = await gateway.predict_multiple_metrics(
            historical_data=historical_data,
            metrics=metrics,
            config=config
        )
        
        # Assertions
        assert isinstance(result, dict)
        assert len(result) == 3
        assert 'temperature' in result
        assert 'temperature_max' in result
        assert 'temperature_min' in result
        
        # Check each metric
        for metric in metrics:
            predictions = result[metric]
            assert len(predictions) == 2
            assert all(isinstance(p, Forecast) for p in predictions)
            
            # Check temperature relationships
            if metric == 'temperature_max':
                for pred in predictions:
                    assert pred.predicted_value > 20.0  # Should be reasonable max temp
            elif metric == 'temperature_min':
                for pred in predictions:
                    assert pred.predicted_value < 25.0  # Should be reasonable min temp
    
    def test_find_historical_value(self):
        """Test finding historical value for specific date and metric."""
        gateway = PredictionMockGateway()
        
        # Create test historical data
        historical_data = [
            WeatherData(
                time=datetime(2023, 6, 15),
                temperature_2m_max=28.0,
                temperature_2m_min=18.0,
                temperature_2m_mean=23.0,
                precipitation_sum=0.0,
                sunshine_duration=36000,
                wind_speed_10m=5.0,
                weather_code=0
            ),
            WeatherData(
                time=datetime(2023, 6, 16),
                temperature_2m_max=30.0,
                temperature_2m_min=20.0,
                temperature_2m_mean=25.0,
                precipitation_sum=2.0,
                sunshine_duration=28800,
                wind_speed_10m=3.0,
                weather_code=1
            )
        ]
        
        # Test finding existing data
        target_date = date(2023, 6, 15)
        
        temp_mean = gateway._find_historical_value(historical_data, target_date, 'temperature')
        temp_max = gateway._find_historical_value(historical_data, target_date, 'temperature_max')
        temp_min = gateway._find_historical_value(historical_data, target_date, 'temperature_min')
        
        assert temp_mean == 23.0
        assert temp_max == 28.0
        assert temp_min == 18.0
        
        # Test finding non-existing data
        non_existing_date = date(2023, 6, 20)
        result = gateway._find_historical_value(historical_data, non_existing_date, 'temperature')
        assert result is None
    
    def test_get_seasonal_average(self):
        """Test getting seasonal average for different metrics."""
        gateway = PredictionMockGateway()
        
        # Test summer date
        summer_date = date(2024, 7, 15)
        summer_temp = gateway._get_seasonal_average(summer_date, 'temperature')
        summer_max = gateway._get_seasonal_average(summer_date, 'temperature_max')
        summer_min = gateway._get_seasonal_average(summer_date, 'temperature_min')
        
        # Test winter date
        winter_date = date(2024, 1, 15)
        winter_temp = gateway._get_seasonal_average(winter_date, 'temperature')
        winter_max = gateway._get_seasonal_average(winter_date, 'temperature_max')
        winter_min = gateway._get_seasonal_average(winter_date, 'temperature_min')
        
        # Assertions
        assert summer_temp > winter_temp
        assert summer_max > winter_max
        assert summer_min > winter_min
        
        # Check temperature relationships
        assert summer_max > summer_temp > summer_min
        assert winter_max > winter_temp > winter_min
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid inputs."""
        gateway = PredictionMockGateway()
        
        # Test with non-existent file
        with pytest.raises(Exception):
            await gateway.read_historical_data("non_existent_file.json")
        
        # Test with invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with pytest.raises(Exception):
                await gateway.read_historical_data(temp_file)
        finally:
            Path(temp_file).unlink()
        
        # Test with empty historical data
        with pytest.raises(Exception):
            await gateway.predict(
                historical_data=[],
                metric='temperature',
                config={'prediction_days': 1}
            )
