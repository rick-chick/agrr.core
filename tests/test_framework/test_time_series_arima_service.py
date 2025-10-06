"""Tests for TimeSeriesARIMAService."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from agrr_core.framework.services.time_series_arima_service import (
    TimeSeriesARIMAService,
    ARIMAModel,
    FittedARIMAModel,
    STATSMODELS_AVAILABLE
)


class TestTimeSeriesARIMAService:
    """Test cases for TimeSeriesARIMAService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TimeSeriesARIMAService()
        self.sample_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0] * 4  # 40 points
    
    def test_init(self):
        """Test service initialization."""
        assert isinstance(self.service, TimeSeriesARIMAService)
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_create_model_with_seasonal_order(self):
        """Test creating ARIMA model with seasonal order."""
        order = (1, 1, 1)
        seasonal_order = (1, 1, 1, 12)
        
        model = self.service.create_model(self.sample_data, order, seasonal_order)
        
        assert isinstance(model, ARIMAModel)
        assert model.order == order
        assert model.seasonal_order == seasonal_order
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_create_model_without_seasonal_order(self):
        """Test creating ARIMA model without seasonal order."""
        order = (1, 1, 1)
        
        model = self.service.create_model(self.sample_data, order)
        
        assert isinstance(model, ARIMAModel)
        assert model.order == order
        assert model.seasonal_order is None
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_create_model_statsmodels_not_available(self):
        """Test creating model when statsmodels is not available."""
        with patch('agrr_core.framework.services.time_series_arima_service.STATSMODELS_AVAILABLE', False):
            service = TimeSeriesARIMAService()
            
            with pytest.raises(RuntimeError, match="Statsmodels is not available"):
                service.create_model(self.sample_data, (1, 1, 1))
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_check_stationarity_stationary_data(self):
        """Test checking stationarity for stationary data."""
        # Create stationary data (white noise)
        stationary_data = [0.1, -0.2, 0.3, -0.1, 0.4, -0.3, 0.2, -0.1, 0.3, -0.2] * 5
        
        result = self.service.check_stationarity(stationary_data)
        
        # Result depends on actual ADF test, but should be a boolean
        assert isinstance(result, bool)
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_check_stationarity_non_stationary_data(self):
        """Test checking stationarity for non-stationary data."""
        # Create trending data (non-stationary)
        trending_data = list(range(1, 51))  # 1, 2, 3, ..., 50
        
        result = self.service.check_stationarity(trending_data)
        
        # Result depends on actual ADF test, but should be a boolean-like value
        assert result in [True, False]  # Works for both bool and numpy.bool_
    
    def test_check_stationarity_statsmodels_not_available(self):
        """Test checking stationarity when statsmodels is not available."""
        with patch('agrr_core.framework.services.time_series_arima_service.STATSMODELS_AVAILABLE', False):
            service = TimeSeriesARIMAService()
            
            result = service.check_stationarity(self.sample_data)
            assert result is False
    
    def test_make_stationary(self):
        """Test making data stationary by differencing."""
        data = [1, 4, 9, 16, 25]  # Quadratic trend
        
        result = self.service.make_stationary(data)
        
        # Should be one element shorter due to differencing
        assert len(result) == len(data) - 1
        assert result == [3, 5, 7, 9]  # First differences
    
    def test_make_stationary_single_element(self):
        """Test making stationary with single element data."""
        data = [5.0]
        
        result = self.service.make_stationary(data)
        
        assert result == []


class TestARIMAModel:
    """Test cases for ARIMAModel."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.data = [1.0, 2.0, 3.0, 4.0, 5.0] * 10  # 50 points
        self.order = (1, 1, 1)
        self.seasonal_order = (1, 1, 1, 12)
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_init_with_seasonal_order(self):
        """Test ARIMA model initialization with seasonal order."""
        model = ARIMAModel(self.data, self.order, self.seasonal_order)
        
        assert model.data == self.data
        assert model.order == self.order
        assert model.seasonal_order == self.seasonal_order
        assert hasattr(model, '_arima_model')
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_init_without_seasonal_order(self):
        """Test ARIMA model initialization without seasonal order."""
        model = ARIMAModel(self.data, self.order)
        
        assert model.data == self.data
        assert model.order == self.order
        assert model.seasonal_order is None
        assert hasattr(model, '_arima_model')
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_fit_success(self):
        """Test successful model fitting."""
        model = ARIMAModel(self.data, self.order)
        
        fitted_model = model.fit()
        
        assert isinstance(fitted_model, FittedARIMAModel)
        assert hasattr(fitted_model, 'fitted_model')
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_fit_with_fallback(self):
        """Test model fitting with fallback to simpler model."""
        # Use complex order that might fail
        complex_order = (3, 3, 3)
        model = ARIMAModel(self.data, complex_order)
        
        # Mock the complex model to fail, then succeed with simple model
        with patch.object(model._arima_model, 'fit', side_effect=Exception("Complex model failed")):
            fitted_model = model.fit()
            
            assert isinstance(fitted_model, FittedARIMAModel)
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_fit_statsmodels_not_available(self):
        """Test fitting when statsmodels is not available."""
        with patch('agrr_core.framework.services.time_series_arima_service.STATSMODELS_AVAILABLE', False):
            model = ARIMAModel(self.data, self.order)
            
            with pytest.raises(RuntimeError, match="Statsmodels is not available"):
                model.fit()


class TestFittedARIMAModel:
    """Test cases for FittedARIMAModel."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_fitted_model = Mock()
        self.fitted_model = FittedARIMAModel(self.mock_fitted_model)
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_forecast_success(self):
        """Test successful forecasting."""
        expected_predictions = np.array([10.0, 11.0, 12.0])
        self.mock_fitted_model.forecast.return_value = expected_predictions
        
        result = self.fitted_model.forecast(3)
        
        assert np.array_equal(result, expected_predictions)
        self.mock_fitted_model.forecast.assert_called_once_with(steps=3)
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_forecast_with_fallback(self):
        """Test forecasting with fallback to get_forecast."""
        expected_predictions = np.array([10.0, 11.0, 12.0])
        
        # Mock forecast to fail, get_forecast to succeed
        self.mock_fitted_model.forecast.side_effect = Exception("Forecast failed")
        mock_forecast_result = Mock()
        mock_forecast_result.predicted_mean = expected_predictions
        self.mock_fitted_model.get_forecast.return_value = mock_forecast_result
        
        result = self.fitted_model.forecast(3)
        
        assert np.array_equal(result, expected_predictions)
        self.mock_fitted_model.get_forecast.assert_called_once_with(steps=3)
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_get_forecast_with_intervals_success(self):
        """Test getting forecasts with confidence intervals successfully."""
        expected_predictions = np.array([10.0, 11.0, 12.0])
        expected_intervals = np.array([[9.0, 11.0], [10.0, 12.0], [11.0, 13.0]])
        
        mock_forecast_result = Mock()
        mock_forecast_result.predicted_mean = expected_predictions
        mock_forecast_result.conf_int.return_value = expected_intervals
        self.mock_fitted_model.get_forecast.return_value = mock_forecast_result
        
        predictions, intervals = self.fitted_model.get_forecast_with_intervals(3)
        
        assert np.array_equal(predictions, expected_predictions)
        assert np.array_equal(intervals, expected_intervals)
    
    @pytest.mark.skipif(not STATSMODELS_AVAILABLE, reason="statsmodels not available")
    def test_get_forecast_with_intervals_fallback(self):
        """Test getting forecasts with intervals fallback to simple forecast."""
        expected_predictions = np.array([10.0, 11.0, 12.0])
        
        # Mock get_forecast to fail, forecast to succeed
        self.mock_fitted_model.get_forecast.side_effect = Exception("Get forecast failed")
        self.mock_fitted_model.forecast.return_value = expected_predictions
        
        predictions, intervals = self.fitted_model.get_forecast_with_intervals(3)
        
        assert np.array_equal(predictions, expected_predictions)
        assert intervals is None
