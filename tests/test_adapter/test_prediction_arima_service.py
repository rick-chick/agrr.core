"""Tests for PredictionARIMAService."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from agrr_core.adapter.services.prediction_arima_service import PredictionARIMAService
from agrr_core.entity import WeatherData, Forecast
from agrr_core.adapter.interfaces.time_series_interface import TimeSeriesInterface, TimeSeriesModel, FittedTimeSeriesModel
from agrr_core.entity.exceptions.prediction_error import PredictionError


class MockTimeSeriesModel(TimeSeriesModel):
    """Mock time series model for testing."""
    
    def __init__(self, data, order, seasonal_order=None):
        self.data = data
        self.order = order
        self.seasonal_order = seasonal_order
    
    def fit(self):
        return MockFittedTimeSeriesModel()


class MockFittedTimeSeriesModel(FittedTimeSeriesModel):
    """Mock fitted time series model for testing."""
    
    def forecast(self, steps):
        import numpy as np
        return np.array([20.0] * steps)
    
    def get_forecast_with_intervals(self, steps):
        import numpy as np
        predictions = np.array([20.0] * steps)
        intervals = np.array([[18.0, 22.0]] * steps)
        return predictions, intervals


class MockTimeSeriesInterface(TimeSeriesInterface):
    """Mock time series interface for testing."""
    
    def __init__(self):
        self.check_stationarity_called = False
        self.make_stationary_called = False
        self.create_model_called = False
    
    def create_model(self, data, order, seasonal_order=None):
        self.create_model_called = True
        return MockTimeSeriesModel(data, order, seasonal_order)
    
    def check_stationarity(self, data):
        self.check_stationarity_called = True
        return False  # Always return False for testing
    
    def make_stationary(self, data):
        self.make_stationary_called = True
        return data[1:]  # Simple differencing


class TestPredictionARIMAService:
    """Test cases for PredictionARIMAService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_time_series_service = MockTimeSeriesInterface()
        self.service = PredictionARIMAService(self.mock_time_series_service)
        
        # Create sample weather data
        base_date = datetime(2024, 1, 1)
        self.sample_weather_data = [
            WeatherData(
                time=base_date + timedelta(days=i),
                temperature_2m_mean=15.0 + i,
                temperature_2m_max=20.0 + i,
                temperature_2m_min=10.0 + i,
                precipitation_sum=1.0 + i * 0.1,
                sunshine_duration=8.0 + i * 0.2
            )
            for i in range(40)  # 40 data points
        ]
    
    def test_init(self):
        """Test service initialization."""
        assert self.service.time_series_service == self.mock_time_series_service
    
    @pytest.mark.asyncio
    async def test_predict_multiple_metrics_success(self):
        """Test successful multiple metrics prediction."""
        metrics = ['temperature']
        model_config = {'prediction_days': 3}
        
        result = await self.service.predict_multiple_metrics(
            self.sample_weather_data, metrics, model_config
        )
        
        assert 'temperature' in result
        assert len(result['temperature']) == 3
        
        # Check that time series service methods were called
        assert self.mock_time_series_service.check_stationarity_called
        assert self.mock_time_series_service.make_stationary_called
        assert self.mock_time_series_service.create_model_called
    
    @pytest.mark.asyncio
    async def test_predict_multiple_metrics_failure(self):
        """Test multiple metrics prediction with failure."""
        # Mock the time series service to raise an exception
        self.mock_time_series_service.create_model = Mock(side_effect=Exception("Model creation failed"))
        
        metrics = ['temperature']
        model_config = {'prediction_days': 3}
        
        with pytest.raises(PredictionError, match="Failed to predict temperature"):
            await self.service.predict_multiple_metrics(
                self.sample_weather_data, metrics, model_config
            )
    
    @pytest.mark.asyncio
    async def test_predict_single_metric_success(self):
        """Test successful single metric prediction."""
        metric = 'temperature'
        model_config = {'prediction_days': 3}
        
        result = await self.service._predict_single_metric(
            self.sample_weather_data, metric, model_config
        )
        
        assert len(result) == 3
        for forecast in result:
            assert isinstance(forecast, Forecast)
            assert forecast.predicted_value == 20.0
            assert forecast.confidence_lower == 18.0
            assert forecast.confidence_upper == 22.0
    
    @pytest.mark.asyncio
    async def test_predict_single_metric_insufficient_data(self):
        """Test prediction with insufficient data."""
        # Create data with less than 30 points
        insufficient_data = self.sample_weather_data[:10]
        
        metric = 'temperature'
        model_config = {'prediction_days': 3}
        
        with pytest.raises(PredictionError, match="Insufficient data for temperature. Need at least 30 data points"):
            await self.service._predict_single_metric(
                insufficient_data, metric, model_config
            )
    
    @pytest.mark.asyncio
    async def test_predict_single_metric_stationary_data(self):
        """Test prediction with stationary data."""
        # Mock the time series service to return stationary data
        self.mock_time_series_service.check_stationarity = Mock(return_value=True)
        
        metric = 'temperature'
        model_config = {'prediction_days': 3}
        
        result = await self.service._predict_single_metric(
            self.sample_weather_data, metric, model_config
        )
        
        assert len(result) == 3
        # Should not call make_stationary for stationary data
        assert not self.mock_time_series_service.make_stationary_called
    
    @pytest.mark.asyncio
    async def test_predict_single_metric_with_fallback_model(self):
        """Test prediction with model fitting fallback."""
        # Mock model fitting to fail first time, succeed with simpler model
        mock_model = Mock()
        mock_fitted_model = MockFittedTimeSeriesModel()
        
        # First call fails, second call succeeds
        mock_model.fit = Mock(side_effect=[Exception("Complex model failed"), mock_fitted_model])
        self.mock_time_series_service.create_model = Mock(return_value=mock_model)
        
        metric = 'temperature'
        model_config = {'prediction_days': 3}
        
        result = await self.service._predict_single_metric(
            self.sample_weather_data, metric, model_config
        )
        
        assert len(result) == 3
        # Should have been called twice (complex model, then simple model)
        assert mock_model.fit.call_count == 2
    
    def test_extract_metric_data_temperature(self):
        """Test extracting temperature metric data."""
        data = self.service._extract_metric_data(self.sample_weather_data, 'temperature')
        
        assert len(data) == 40
        assert data[0] == 15.0  # First temperature value
        assert data[-1] == 54.0  # Last temperature value (15.0 + 39)
    
    def test_extract_metric_data_precipitation(self):
        """Test extracting precipitation metric data."""
        data = self.service._extract_metric_data(self.sample_weather_data, 'precipitation')
        
        assert len(data) == 40
        assert data[0] == 1.0  # First precipitation value
        assert data[-1] == 4.9  # Last precipitation value (1.0 + 39 * 0.1)
    
    def test_extract_metric_data_sunshine(self):
        """Test extracting sunshine metric data."""
        data = self.service._extract_metric_data(self.sample_weather_data, 'sunshine')
        
        assert len(data) == 40
        assert data[0] == 8.0  # First sunshine value
        assert data[-1] == 15.8  # Last sunshine value (8.0 + 39 * 0.2)
    
    def test_extract_metric_data_unknown_metric(self):
        """Test extracting unknown metric data."""
        data = self.service._extract_metric_data(self.sample_weather_data, 'unknown_metric')
        
        assert len(data) == 0  # Should be empty for unknown metric
    
    def test_extract_metric_data_with_none_values(self):
        """Test extracting metric data with None values."""
        # Create weather data with some None values
        weather_data_with_nones = [
            WeatherData(
                time=datetime(2024, 1, 1) + timedelta(days=i),
                temperature_2m_mean=15.0 + i if i % 2 == 0 else None,  # Every other value is None
                temperature_2m_max=20.0 + i,
                temperature_2m_min=10.0 + i,
                precipitation_sum=1.0 + i * 0.1,
                sunshine_duration=8.0 + i * 0.2
            )
            for i in range(40)
        ]
        
        data = self.service._extract_metric_data(weather_data_with_nones, 'temperature')
        
        # Should only include non-None values
        assert len(data) == 20  # Half the values
        assert all(val is not None for val in data)
    
    @pytest.mark.asyncio
    async def test_evaluate_model_accuracy(self):
        """Test model accuracy evaluation."""
        # Create test data and predictions
        test_data = self.sample_weather_data[:10]
        predictions = [
            Forecast(date=datetime(2024, 2, 1), predicted_value=20.0),
            Forecast(date=datetime(2024, 2, 2), predicted_value=21.0),
            Forecast(date=datetime(2024, 2, 3), predicted_value=22.0)
        ]
        
        result = await self.service.evaluate_model_accuracy(test_data, predictions, 'temperature')
        
        assert 'mae' in result
        assert 'mse' in result
        assert 'rmse' in result
        assert 'mape' in result
        
        # All metrics should be numeric
        assert isinstance(result['mae'], float)
        assert isinstance(result['mse'], float)
        assert isinstance(result['rmse'], float)
        assert isinstance(result['mape'], float)
    
    @pytest.mark.asyncio
    async def test_train_model(self):
        """Test model training."""
        model_config = {'order': (1, 1, 1)}
        metric = 'temperature'
        
        result = await self.service.train_model(self.sample_weather_data, model_config, metric)
        
        assert result['model_type'] == 'arima'
        assert result['metric'] == metric
        assert result['training_samples'] == 40
        assert result['status'] == 'trained'
    
    @pytest.mark.asyncio
    async def test_get_model_info(self):
        """Test getting model information."""
        model_type = 'arima'
        
        result = await self.service.get_model_info(model_type)
        
        assert result['model_type'] == 'arima'
        assert 'description' in result
        assert 'supports_confidence_intervals' in result
        assert 'min_training_samples' in result
        assert 'recommended_order' in result
        assert 'recommended_seasonal_order' in result
    
    @pytest.mark.asyncio
    async def test_predict_with_confidence_intervals(self):
        """Test prediction with confidence intervals."""
        prediction_days = 5
        confidence_level = 0.95
        model_config = {'order': (1, 1, 1)}
        
        result = await self.service.predict_with_confidence_intervals(
            self.sample_weather_data, prediction_days, confidence_level, model_config
        )
        
        assert len(result) == 5
        for forecast in result:
            assert isinstance(forecast, Forecast)
            assert forecast.confidence_lower is not None
            assert forecast.confidence_upper is not None
    
    @pytest.mark.asyncio
    async def test_batch_predict(self):
        """Test batch prediction."""
        historical_data_list = [self.sample_weather_data, self.sample_weather_data]
        model_config = {'order': (1, 1, 1)}
        metrics = ['temperature']
        
        result = await self.service.batch_predict(historical_data_list, model_config, metrics)
        
        assert len(result) == 2
        for batch_result in result:
            assert 'temperature' in batch_result
            assert len(batch_result['temperature']) == 30  # Default prediction days
    
    @pytest.mark.asyncio
    async def test_batch_predict_with_errors(self):
        """Test batch prediction with some failures."""
        # Create one valid dataset and one that will cause an error
        valid_data = self.sample_weather_data
        invalid_data = self.sample_weather_data[:5]  # Too few data points
        
        historical_data_list = [valid_data, invalid_data]
        model_config = {'order': (1, 1, 1)}
        metrics = ['temperature']
        
        result = await self.service.batch_predict(historical_data_list, model_config, metrics)
        
        assert len(result) == 2
        assert 'temperature' in result[0]  # First batch should succeed
        assert 'error' in result[1]  # Second batch should have error
