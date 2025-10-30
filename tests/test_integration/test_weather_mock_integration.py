"""Integration tests for weather mock mode."""

import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from agrr_core.framework.agrr_core_container import AgrrCoreContainer
from agrr_core.adapter.controllers.weather_cli_predict_controller import WeatherCliPredictController

class TestWeatherMockIntegration:
    """Integration tests for weather mock mode."""

    def test_mock_weather_data_generation(self):
        """Test generating mock weather data through container."""
        # Create container with mock configuration
        config = {
            'weather_data_source': 'mock'
        }
        container = AgrrCoreContainer(config)
        
        # Get mock weather gateway
        weather_gateway = container.get_weather_mock_gateway()
        
        # Test getting weather data
        result = weather_gateway.get_by_location_and_date_range(
            latitude=35.6762,
            longitude=139.6503,
            start_date="2024-01-01",
            end_date="2024-01-07"
        )
        
        # Assertions
        assert result is not None
        assert result.location is not None
        assert len(result.weather_data_list) == 7
        
        # Check that data is realistic
        for data in result.weather_data_list:
            assert data.temperature_2m_max is not None
            assert data.temperature_2m_min is not None
            assert data.temperature_2m_mean is not None
            assert data.temperature_2m_max >= data.temperature_2m_mean
            assert data.temperature_2m_min <= data.temperature_2m_mean

    def test_mock_prediction_generation(self):
        """Test generating mock predictions through container."""
        # Create container
        container = AgrrCoreContainer()
        
        # Get mock prediction gateway
        prediction_gateway = container.get_prediction_gateway(model_type='mock')
        
        # Create test historical data
        historical_data = [
            {
                "time": "2023-06-15T00:00:00",
                "temperature_2m_max": 28.0,
                "temperature_2m_min": 18.0,
                "temperature_2m_mean": 23.0,
                "precipitation_sum": 0.0,
                "sunshine_duration": 36000,
                "wind_speed_10m": 5.0,
                "weather_code": 0
            },
            {
                "time": "2023-06-16T00:00:00",
                "temperature_2m_max": 30.0,
                "temperature_2m_min": 20.0,
                "temperature_2m_mean": 25.0,
                "precipitation_sum": 2.0,
                "sunshine_duration": 28800,
                "wind_speed_10m": 3.0,
                "weather_code": 1
            }
        ]
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "latitude": 35.6762,
                "longitude": 139.6503,
                "data": historical_data
            }, f)
            input_file = f.name
        
        try:
            # Test single metric prediction
            predictions = prediction_gateway.predict(
                historical_data=prediction_gateway.read_historical_data(input_file),
                metric='temperature',
                config={'prediction_days': 3}
            )
            
            # Assertions
            assert len(predictions) == 3
            assert all(pred.predicted_value is not None for pred in predictions)
            assert all(pred.confidence_lower is not None for pred in predictions)
            assert all(pred.confidence_upper is not None for pred in predictions)
            
            # Test multi-metric prediction
            multi_predictions = prediction_gateway.predict_multiple_metrics(
                historical_data=prediction_gateway.read_historical_data(input_file),
                metrics=['temperature', 'temperature_max', 'temperature_min'],
                config={'prediction_days': 3}
            )
            
            # Assertions
            assert len(multi_predictions) == 3
            assert 'temperature' in multi_predictions
            assert 'temperature_max' in multi_predictions
            assert 'temperature_min' in multi_predictions
            
            for metric, preds in multi_predictions.items():
                assert len(preds) == 3
                assert all(pred.predicted_value is not None for pred in preds)
        
        finally:
            Path(input_file).unlink()

    def test_mock_cli_controller(self):
        """Test mock mode through CLI controller."""
        # Create container with mock configuration
        config = {
            'weather_data_source': 'mock'
        }
        container = AgrrCoreContainer(config)
        
        # Get controller with mock gateways
        weather_gateway = container.get_weather_gateway()
        prediction_gateway = container.get_prediction_gateway(model_type='mock')
        cli_presenter = container.get_cli_presenter()
        
        controller = WeatherCliPredictController(
            weather_gateway=weather_gateway,
            prediction_gateway=prediction_gateway,
            cli_presenter=cli_presenter
        )
        
        # Create test input file with sufficient records (30+ days)
        test_data = {
            "latitude": 35.6762,
            "longitude": 139.6503,
            "data": []
        }
        
        # Generate 30 days of test data
        base_date = datetime(2023, 6, 1)
        for i in range(30):
            current_date = base_date + timedelta(days=i)
            test_data["data"].append({
                "time": current_date.strftime("%Y-%m-%dT00:00:00"),
                "temperature_2m_max": 25.0 + i * 0.1,
                "temperature_2m_min": 15.0 + i * 0.1,
                "temperature_2m_mean": 20.0 + i * 0.1,
                "precipitation_sum": i % 3 == 0 and 5.0 or 0.0,
                "sunshine_duration": 36000,
                "wind_speed_10m": 5.0,
                "weather_code": 0
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            input_file = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            # Test CLI arguments
            args = [
                '--input', input_file,
                '--output', output_file,
                '--days', '3',
                '--model', 'mock'
            ]
            
            # Run controller
            controller.handle_predict_command(
                controller.create_argument_parser().parse_args(args)
            )
            
            # Check output file was created
            assert Path(output_file).exists()
            
            # Check output content
            with open(output_file, 'r', encoding='utf-8') as f:
                output_data = json.load(f)
            
            assert 'predictions' in output_data
            assert 'model_type' in output_data
            assert output_data['model_type'] == 'Mock'
            assert len(output_data['predictions']) == 3
            
            # Check prediction structure
            for pred in output_data['predictions']:
                assert 'date' in pred
                assert 'temperature' in pred
                assert 'temperature_confidence_lower' in pred
                assert 'temperature_confidence_upper' in pred
        
        finally:
            Path(input_file).unlink()
            Path(output_file).unlink()

    def test_mock_vs_real_data_consistency(self):
        """Test that mock data is consistent with real data patterns."""
        container = AgrrCoreContainer({'weather_data_source': 'mock'})
        weather_gateway = container.get_weather_mock_gateway()
        
        # Get mock data for a week
        result = weather_gateway.get_by_location_and_date_range(
            latitude=35.6762,
            longitude=139.6503,
            start_date="2024-06-01",
            end_date="2024-06-07"
        )
        
        # Check temperature consistency
        for data in result.weather_data_list:
            # Temperature relationships should be logical
            assert data.temperature_2m_max >= data.temperature_2m_mean
            assert data.temperature_2m_min <= data.temperature_2m_mean
            
            # Values should be reasonable for Tokyo in June (adjusted for mock data)
            assert 0.0 <= data.temperature_2m_min <= 40.0
            assert 0.0 <= data.temperature_2m_max <= 50.0
            assert 0.0 <= data.temperature_2m_mean <= 45.0
            
            # Precipitation should be non-negative
            assert data.precipitation_sum >= 0.0
            
            # Sunshine duration should be reasonable (0-24 hours)
            assert 0.0 <= data.sunshine_duration <= 86400  # 24 hours in seconds
            
            # Wind speed should be reasonable
            assert 0.0 <= data.wind_speed_10m <= 20.0
            
            # Weather code should be valid
            assert 0 <= data.weather_code <= 3

    def test_mock_prediction_accuracy_simulation(self):
        """Test that mock predictions simulate realistic accuracy patterns."""
        container = AgrrCoreContainer()
        prediction_gateway = container.get_prediction_gateway(model_type='mock')
        
        # Create historical data with known patterns
        historical_data = [
            {
                "time": "2023-06-15T00:00:00",
                "temperature_2m_max": 28.0,
                "temperature_2m_min": 18.0,
                "temperature_2m_mean": 23.0,
                "precipitation_sum": 0.0,
                "sunshine_duration": 36000,
                "wind_speed_10m": 5.0,
                "weather_code": 0
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "latitude": 35.6762,
                "longitude": 139.6503,
                "data": historical_data
            }, f)
            input_file = f.name
        
        try:
            # Generate predictions
            predictions = prediction_gateway.predict(
                historical_data=prediction_gateway.read_historical_data(input_file),
                metric='temperature',
                config={'prediction_days': 5}
            )
            
            # Check that predictions are based on historical data
            # (should be similar to historical value with some variation)
            historical_temp = 23.0
            predicted_temps = [p.predicted_value for p in predictions]
            
            # Predictions should be within reasonable range of historical data
            for temp in predicted_temps:
                assert 15.0 <= temp <= 35.0  # Reasonable temperature range
                # Should be within ±10°C of historical data
                assert abs(temp - historical_temp) <= 10.0
            
            # Confidence intervals should be reasonable
            for pred in predictions:
                confidence_range = pred.confidence_upper - pred.confidence_lower
                assert 1.0 <= confidence_range <= 10.0  # Reasonable confidence range
                assert pred.confidence_lower <= pred.predicted_value <= pred.confidence_upper
        
        finally:
            Path(input_file).unlink()
