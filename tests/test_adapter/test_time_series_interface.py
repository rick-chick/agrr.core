"""Tests for TimeSeriesInterface."""

import pytest
import numpy as np
from abc import ABC

from agrr_core.framework.interfaces.time_series_interface import (
    TimeSeriesInterface,
    TimeSeriesModel,
    FittedTimeSeriesModel
)


class TestTimeSeriesInterface:
    """Test cases for TimeSeriesInterface."""
    
    def test_is_abstract_base_class(self):
        """Test that TimeSeriesInterface is an abstract base class."""
        assert issubclass(TimeSeriesInterface, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            TimeSeriesInterface()
    
    def test_abstract_methods(self):
        """Test that interface has required abstract methods."""
        # Check that abstract methods exist
        assert hasattr(TimeSeriesInterface, 'create_model')
        assert hasattr(TimeSeriesInterface, 'check_stationarity')
        assert hasattr(TimeSeriesInterface, 'make_stationary')
        
        # Check that they are abstract
        assert getattr(TimeSeriesInterface.create_model, '__isabstractmethod__', False)
        assert getattr(TimeSeriesInterface.check_stationarity, '__isabstractmethod__', False)
        assert getattr(TimeSeriesInterface.make_stationary, '__isabstractmethod__', False)


class TestTimeSeriesModel:
    """Test cases for TimeSeriesModel."""
    
    def test_is_abstract_base_class(self):
        """Test that TimeSeriesModel is an abstract base class."""
        assert issubclass(TimeSeriesModel, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            TimeSeriesModel()
    
    def test_abstract_methods(self):
        """Test that model has required abstract methods."""
        # Check that abstract method exists
        assert hasattr(TimeSeriesModel, 'fit')
        
        # Check that it is abstract
        assert getattr(TimeSeriesModel.fit, '__isabstractmethod__', False)


class TestFittedTimeSeriesModel:
    """Test cases for FittedTimeSeriesModel."""
    
    def test_is_abstract_base_class(self):
        """Test that FittedTimeSeriesModel is an abstract base class."""
        assert issubclass(FittedTimeSeriesModel, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            FittedTimeSeriesModel()
    
    def test_abstract_methods(self):
        """Test that fitted model has required abstract methods."""
        # Check that abstract methods exist
        assert hasattr(FittedTimeSeriesModel, 'forecast')
        assert hasattr(FittedTimeSeriesModel, 'get_forecast_with_intervals')
        
        # Check that they are abstract
        assert getattr(FittedTimeSeriesModel.forecast, '__isabstractmethod__', False)
        assert getattr(FittedTimeSeriesModel.get_forecast_with_intervals, '__isabstractmethod__', False)


class ConcreteTimeSeriesInterface(TimeSeriesInterface):
    """Concrete implementation for testing."""
    
    def create_model(self, data, order, seasonal_order=None):
        return ConcreteTimeSeriesModel(data, order, seasonal_order)
    
    def check_stationarity(self, data):
        return len(data) > 10  # Simple test
    
    def make_stationary(self, data):
        return data[1:] if len(data) > 1 else []


class ConcreteTimeSeriesModel(TimeSeriesModel):
    """Concrete model implementation for testing."""
    
    def __init__(self, data, order, seasonal_order=None):
        self.data = data
        self.order = order
        self.seasonal_order = seasonal_order
    
    def fit(self):
        return ConcreteFittedTimeSeriesModel(self.data)


class ConcreteFittedTimeSeriesModel(FittedTimeSeriesModel):
    """Concrete fitted model implementation for testing."""
    
    def __init__(self, data):
        self.data = data
    
    def forecast(self, steps):
        return np.array([1.0] * steps)
    
    def get_forecast_with_intervals(self, steps):
        predictions = np.array([1.0] * steps)
        intervals = np.array([[0.5, 1.5]] * steps)
        return predictions, intervals


class TestConcreteImplementation:
    """Test cases for concrete implementations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.interface = ConcreteTimeSeriesInterface()
        self.data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]  # 11 elements > 10
    
    def test_interface_implementation(self):
        """Test concrete interface implementation."""
        # Test create_model
        model = self.interface.create_model(self.data, (1, 1, 1))
        assert isinstance(model, ConcreteTimeSeriesModel)
        
        # Test check_stationarity
        assert self.interface.check_stationarity(self.data) is True  # len > 10
        assert self.interface.check_stationarity([1, 2]) is False  # len <= 10
        
        # Test make_stationary
        result = self.interface.make_stationary(self.data)
        assert result == [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
    
    def test_model_implementation(self):
        """Test concrete model implementation."""
        model = ConcreteTimeSeriesModel(self.data, (1, 1, 1))
        
        assert model.data == self.data
        assert model.order == (1, 1, 1)
        assert model.seasonal_order is None
        
        # Test fit
        fitted_model = model.fit()
        assert isinstance(fitted_model, ConcreteFittedTimeSeriesModel)
    
    def test_fitted_model_implementation(self):
        """Test concrete fitted model implementation."""
        fitted_model = ConcreteFittedTimeSeriesModel(self.data)
        
        # Test forecast
        predictions = fitted_model.forecast(3)
        assert len(predictions) == 3
        assert all(p == 1.0 for p in predictions)
        
        # Test get_forecast_with_intervals
        predictions, intervals = fitted_model.get_forecast_with_intervals(3)
        assert len(predictions) == 3
        assert len(intervals) == 3
        assert all(p == 1.0 for p in predictions)
        assert all(interval[0] == 0.5 and interval[1] == 1.5 for interval in intervals)
