"""Time series ARIMA service implementation for framework layer."""

from typing import List, Tuple, Optional
import numpy as np

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    # Mock classes for testing when statsmodels is not installed
    class ARIMA:
        def __init__(self, data, order=None, seasonal_order=None):
            self.data = data
        def fit(self):
            return self
        def forecast(self, steps):
            return np.array([20.0] * steps)
        def get_forecast(self, steps):
            class Forecast:
                def __init__(self, steps):
                    self.predicted_mean = np.array([20.0] * steps)
                    self.conf_int = np.array([[18.0, 23.0]] * steps)
            return Forecast(steps)
    
    class adfuller:
        @staticmethod
        def __call__(data):
            return [0, 0.05, 0, {}, {}]  # Mock stationary result

from agrr_core.adapter.interfaces.ml.time_series_service_interface import (
    TimeSeriesServiceInterface, 
    TimeSeriesModelInterface, 
    FittedTimeSeriesModelInterface
)


class TimeSeriesARIMAService(TimeSeriesServiceInterface):
    """ARIMA implementation of time series analysis interface."""
    
    def create_model(self, data: List[float], order: Tuple[int, int, int], 
                    seasonal_order: Optional[Tuple[int, int, int, int]] = None) -> 'ARIMAModel':
        """Create ARIMA model with given parameters."""
        if not STATSMODELS_AVAILABLE:
            raise RuntimeError("Statsmodels is not available. Please install statsmodels.")
        
        return ARIMAModel(data, order, seasonal_order)
    
    def check_stationarity(self, data: List[float]) -> bool:
        """Check if data is stationary using Augmented Dickey-Fuller test."""
        if not STATSMODELS_AVAILABLE:
            return False
        
        try:
            result = adfuller(data)
            # If p-value is less than 0.05, data is stationary
            return result[1] < 0.05
        except Exception:
            return False
    
    def make_stationary(self, data: List[float]) -> List[float]:
        """Make data stationary by differencing."""
        # Simple first difference
        diff_data = [data[i] - data[i-1] for i in range(1, len(data))]
        return diff_data


class ARIMAModel(TimeSeriesModelInterface):
    """ARIMA model implementation."""
    
    def __init__(self, data: List[float], order: Tuple[int, int, int], 
                 seasonal_order: Optional[Tuple[int, int, int, int]] = None):
        """Initialize ARIMA model."""
        self.data = data
        self.order = order
        self.seasonal_order = seasonal_order
        
        if STATSMODELS_AVAILABLE:
            self._arima_model = ARIMA(data, order=order, seasonal_order=seasonal_order)
        else:
            self._arima_model = ARIMA(data, order=order, seasonal_order=seasonal_order)
    
    def fit(self) -> 'FittedARIMAModel':
        """Fit the ARIMA model to data."""
        if not STATSMODELS_AVAILABLE:
            raise RuntimeError("Statsmodels is not available. Please install statsmodels.")
        
        try:
            fitted_model = self._arima_model.fit()
            return FittedARIMAModel(fitted_model)
        except Exception as e:
            # Try simpler model if complex one fails
            try:
                simple_order = (1, 1, 0)
                simple_model = ARIMA(self.data, order=simple_order)
                fitted_model = simple_model.fit()
                return FittedARIMAModel(fitted_model)
            except Exception as fallback_e:
                raise RuntimeError(f"Failed to fit ARIMA model: {e}. Fallback also failed: {fallback_e}")


class FittedARIMAModel(FittedTimeSeriesModelInterface):
    """Fitted ARIMA model implementation."""
    
    def __init__(self, fitted_model):
        """Initialize fitted ARIMA model."""
        self.fitted_model = fitted_model
    
    def forecast(self, steps: int) -> np.ndarray:
        """Generate point forecasts."""
        try:
            return self.fitted_model.forecast(steps=steps)
        except Exception:
            # Fallback to get_forecast if forecast method fails
            forecast_result = self.fitted_model.get_forecast(steps=steps)
            return forecast_result.predicted_mean
    
    def get_forecast_with_intervals(self, steps: int) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Generate forecasts with confidence intervals."""
        try:
            forecast_result = self.fitted_model.get_forecast(steps=steps)
            predictions = forecast_result.predicted_mean
            confidence_intervals = forecast_result.conf_int()
            return predictions, confidence_intervals
        except Exception:
            # Fallback to simple forecast without intervals
            predictions = self.forecast(steps)
            return predictions, None
