"""Tests for prediction model gateway implementation."""

import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import Mock, AsyncMock

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.adapter.gateways.prediction_model_gateway_impl import PredictionModelGatewayImpl


def create_sample_weather_data(days: int = 100) -> List[WeatherData]:
    """Create sample weather data."""
    data = []
    start_date = datetime(2024, 1, 1)
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        weather = WeatherData(
            time=date,
            temperature_2m_max=20.0,
            temperature_2m_min=10.0,
            temperature_2m_mean=15.0,
            precipitation_sum=0.0,
            sunshine_duration=10000.0
        )
        data.append(weather)
    
    return data


def create_sample_forecasts(days: int = 7) -> List[Forecast]:
    """Create sample forecast data."""
    forecasts = []
    start_date = datetime(2024, 4, 1)
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        forecast = Forecast(
            date=date,
            predicted_value=15.0 + i * 0.1,
            confidence_lower=14.0,
            confidence_upper=16.0
        )
        forecasts.append(forecast)
    
    return forecasts


class TestPredictionModelGatewayImpl:
    """Test prediction model gateway implementation."""
    
    def test_init_with_single_model(self):
        """Test initialization with single model."""
        mock_model = Mock()
        mock_model.get_required_data_days = Mock(return_value=30)
        
        gateway = PredictionModelGatewayImpl(arima_service=mock_model)
        
        assert 'arima' in gateway.models
        assert gateway.default_model == 'arima'
    
    def test_init_with_both_models(self):
        """Test initialization with both models."""
        mock_arima = Mock()
        mock_lightgbm = Mock()
        
        gateway = PredictionModelGatewayImpl(
            arima_service=mock_arima,
            lightgbm_service=mock_lightgbm,
            default_model='lightgbm'
        )
        
        assert 'arima' in gateway.models
        assert 'lightgbm' in gateway.models
        assert gateway.default_model == 'lightgbm'
    
    def test_init_without_models(self):
        """Test initialization without any models raises error."""
        with pytest.raises(ValueError, match="At least one prediction model"):
            gateway = PredictionModelGatewayImpl()
    
    @pytest.mark.asyncio
    async def test_predict_with_default_model(self):
        """Test prediction using default model."""
        mock_model = AsyncMock()
        mock_model.get_required_data_days = Mock(return_value=30)
        mock_model.predict = AsyncMock(return_value=create_sample_forecasts())
        
        gateway = PredictionModelGatewayImpl(arima_service=mock_model)
        historical_data = create_sample_weather_data(100)
        
        forecasts = await gateway.predict(
            historical_data,
            metric='temperature',
            prediction_days=7
        )
        
        assert len(forecasts) == 7
        mock_model.predict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_with_specific_model(self):
        """Test prediction with specific model type."""
        mock_arima = AsyncMock()
        mock_arima.get_required_data_days = Mock(return_value=30)
        mock_arima.predict = AsyncMock(return_value=create_sample_forecasts())
        
        mock_lgb = AsyncMock()
        mock_lgb.get_required_data_days = Mock(return_value=90)
        mock_lgb.predict = AsyncMock(return_value=create_sample_forecasts())
        
        gateway = PredictionModelGatewayImpl(
            arima_service=mock_arima,
            lightgbm_service=mock_lgb
        )
        
        historical_data = create_sample_weather_data(100)
        
        # Predict with LightGBM
        forecasts = await gateway.predict(
            historical_data,
            metric='temperature',
            prediction_days=7,
            model_type='lightgbm'
        )
        
        mock_lgb.predict.assert_called_once()
        mock_arima.predict.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_predict_with_unavailable_model(self):
        """Test prediction with unavailable model raises error."""
        mock_model = AsyncMock()
        mock_model.get_required_data_days = Mock(return_value=30)
        
        gateway = PredictionModelGatewayImpl(arima_service=mock_model)
        historical_data = create_sample_weather_data(100)
        
        with pytest.raises(PredictionError, match="not available"):
            await gateway.predict(
                historical_data,
                metric='temperature',
                prediction_days=7,
                model_type='prophet'  # Not available
            )
    
    @pytest.mark.asyncio
    async def test_predict_with_insufficient_data(self):
        """Test prediction with insufficient data raises error."""
        mock_model = AsyncMock()
        mock_model.get_required_data_days = Mock(return_value=100)
        
        gateway = PredictionModelGatewayImpl(arima_service=mock_model)
        historical_data = create_sample_weather_data(50)  # Not enough
        
        with pytest.raises(PredictionError, match="Insufficient data"):
            await gateway.predict(
                historical_data,
                metric='temperature',
                prediction_days=7
            )
    
    @pytest.mark.asyncio
    async def test_evaluate(self):
        """Test model evaluation."""
        mock_model = AsyncMock()
        mock_model.evaluate = AsyncMock(return_value={'mae': 1.5, 'rmse': 2.0})
        
        gateway = PredictionModelGatewayImpl(arima_service=mock_model)
        
        test_data = create_sample_weather_data(7)
        predictions = create_sample_forecasts(7)
        
        metrics = await gateway.evaluate(
            test_data, predictions, 'temperature'
        )
        
        assert 'mae' in metrics
        assert metrics['mae'] == 1.5
    
    async def test_get_model_info_single(self):
        """Test getting info for single model."""
        mock_model = Mock()
        mock_model.get_model_info = Mock(return_value={
            'model_type': 'arima',
            'model_name': 'ARIMA'
        })
        
        gateway = PredictionModelGatewayImpl(arima_service=mock_model)
        
        # get_model_info is async and requires model_type parameter
        info = await gateway.get_model_info('arima')
        
        assert info['model_type'] == 'arima'
        assert info['model_name'] == 'ARIMA'
    
    async def test_get_model_info_all(self):
        """Test getting info for all models."""
        mock_arima = Mock()
        mock_arima.get_model_info = Mock(return_value={'model_type': 'arima'})
        
        mock_lgb = Mock()
        mock_lgb.get_model_info = Mock(return_value={'model_type': 'lightgbm'})
        
        gateway = PredictionModelGatewayImpl(
            arima_service=mock_arima,
            lightgbm_service=mock_lgb
        )
        
        # get_model_info now requires model_type, test with specific model
        info_arima = await gateway.get_model_info('arima')
        info_lgb = await gateway.get_model_info('lightgbm')
        
        assert info_arima['model_type'] == 'arima'
        assert info_lgb['model_type'] == 'lightgbm'
    
    def test_get_available_models(self):
        """Test getting list of available models."""
        mock_arima = Mock()
        mock_lgb = Mock()
        
        gateway = PredictionModelGatewayImpl(
            arima_service=mock_arima,
            lightgbm_service=mock_lgb
        )
        
        models = gateway.get_available_models()
        
        assert 'arima' in models
        assert 'lightgbm' in models
        assert len(models) == 2
    
    @pytest.mark.asyncio
    async def test_predict_ensemble_equal_weights(self):
        """Test ensemble prediction with equal weights."""
        # Mock ARIMA: predicts 15.0°C
        mock_arima = AsyncMock()
        mock_arima.get_required_data_days = Mock(return_value=30)
        arima_forecasts = [
            Forecast(datetime(2024, 4, i+1), 15.0, 14.0, 16.0)
            for i in range(7)
        ]
        mock_arima.predict = AsyncMock(return_value=arima_forecasts)
        
        # Mock LightGBM: predicts 17.0°C
        mock_lgb = AsyncMock()
        mock_lgb.get_required_data_days = Mock(return_value=90)
        lgb_forecasts = [
            Forecast(datetime(2024, 4, i+1), 17.0, 16.0, 18.0)
            for i in range(7)
        ]
        mock_lgb.predict = AsyncMock(return_value=lgb_forecasts)
        
        gateway = PredictionModelGatewayImpl(
            arima_service=mock_arima,
            lightgbm_service=mock_lgb
        )
        
        historical_data = create_sample_weather_data(100)
        
        ensemble_forecasts = await gateway.predict_ensemble(
            historical_data,
            metric='temperature',
            prediction_days=7,
            model_types=['arima', 'lightgbm']
        )
        
        # Should be average of 15.0 and 17.0 = 16.0
        assert len(ensemble_forecasts) == 7
        assert abs(ensemble_forecasts[0].predicted_value - 16.0) < 0.01
    
    @pytest.mark.asyncio
    async def test_predict_ensemble_weighted(self):
        """Test ensemble prediction with custom weights."""
        mock_arima = AsyncMock()
        mock_arima.get_required_data_days = Mock(return_value=30)
        arima_forecasts = [
            Forecast(datetime(2024, 4, i+1), 15.0, 14.0, 16.0)
            for i in range(7)
        ]
        mock_arima.predict = AsyncMock(return_value=arima_forecasts)
        
        mock_lgb = AsyncMock()
        mock_lgb.get_required_data_days = Mock(return_value=90)
        lgb_forecasts = [
            Forecast(datetime(2024, 4, i+1), 17.0, 16.0, 18.0)
            for i in range(7)
        ]
        mock_lgb.predict = AsyncMock(return_value=lgb_forecasts)
        
        gateway = PredictionModelGatewayImpl(
            arima_service=mock_arima,
            lightgbm_service=mock_lgb
        )
        
        historical_data = create_sample_weather_data(100)
        
        # 70% ARIMA, 30% LightGBM
        ensemble_forecasts = await gateway.predict_ensemble(
            historical_data,
            metric='temperature',
            prediction_days=7,
            model_types=['arima', 'lightgbm'],
            weights=[0.7, 0.3]
        )
        
        # Should be 0.7*15.0 + 0.3*17.0 = 10.5 + 5.1 = 15.6
        assert len(ensemble_forecasts) == 7
        assert abs(ensemble_forecasts[0].predicted_value - 15.6) < 0.01

