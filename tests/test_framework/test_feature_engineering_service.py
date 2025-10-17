"""Tests for FeatureEngineeringService."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from agrr_core.framework.services.ml.feature_engineering_service import FeatureEngineeringService
from agrr_core.entity import WeatherData


class TestFeatureEngineeringService:
    """Test cases for FeatureEngineeringService."""
    
    @pytest.fixture
    def sample_weather_data(self):
        """Create sample weather data for testing."""
        data = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(100):  # 100 days of data
            date = base_date + timedelta(days=i)
            weather_data = WeatherData(
                time=date,
                temperature_2m_max=25.0 + np.sin(i / 10) * 5,  # Seasonal pattern
                temperature_2m_min=15.0 + np.sin(i / 10) * 3,
                temperature_2m_mean=20.0 + np.sin(i / 10) * 4,
                precipitation_sum=float(i % 5),
                sunshine_duration=28800.0 + i * 100
            )
            data.append(weather_data)
        
        return data
    
    def test_create_features_basic(self, sample_weather_data):
        """Test basic feature creation."""
        service = FeatureEngineeringService()
        lookback_days = [1, 7, 14, 30]
        
        df = service.create_features(sample_weather_data, 'temperature', lookback_days)
        
        # Check basic columns exist
        assert 'date' in df.columns
        assert 'temperature' in df.columns
        assert 'temp_max' in df.columns
        assert 'temp_min' in df.columns
        
        # Check temporal features
        assert 'year' in df.columns
        assert 'month' in df.columns
        assert 'day_of_year' in df.columns
        assert 'month_sin' in df.columns
        assert 'month_cos' in df.columns
    
    def test_create_features_temperature_lag_features(self, sample_weather_data):
        """Test that temperature lag features are created."""
        service = FeatureEngineeringService()
        lookback_days = [1, 7, 14, 30]
        
        df = service.create_features(sample_weather_data, 'temperature', lookback_days)
        
        # Check lag features for mean temperature
        for lag in lookback_days:
            assert f'temperature_lag{lag}' in df.columns
    
    def test_create_features_temperature_rolling_stats(self, sample_weather_data):
        """Test that temperature rolling statistics are created."""
        service = FeatureEngineeringService()
        
        df = service.create_features(sample_weather_data, 'temperature', [1, 7, 14, 30])
        
        # Check rolling statistics
        for window in [7, 14, 30]:
            assert f'temperature_ma{window}' in df.columns
            assert f'temperature_std{window}' in df.columns
            assert f'temperature_min{window}' in df.columns
            assert f'temperature_max{window}' in df.columns
    
    def test_create_features_temp_max_min_lag_features(self, sample_weather_data):
        """Test that temp_max and temp_min lag features are created for temperature metric."""
        service = FeatureEngineeringService()
        lookback_days = [1, 7, 14, 30]
        
        df = service.create_features(sample_weather_data, 'temperature', lookback_days)
        
        # Check lag features for temp_max and temp_min
        for lag in lookback_days:
            assert f'temp_max_lag{lag}' in df.columns, f"temp_max_lag{lag} should be in columns"
            assert f'temp_min_lag{lag}' in df.columns, f"temp_min_lag{lag} should be in columns"
            
            # Verify values are shifted correctly
            if lag < len(df):
                # Check that lag features are properly shifted
                assert not df[f'temp_max_lag{lag}'].isna().all(), f"temp_max_lag{lag} should have values"
                assert not df[f'temp_min_lag{lag}'].isna().all(), f"temp_min_lag{lag} should have values"
    
    def test_create_features_temp_max_min_rolling_stats(self, sample_weather_data):
        """Test that temp_max and temp_min rolling statistics are created."""
        service = FeatureEngineeringService()
        
        df = service.create_features(sample_weather_data, 'temperature', [1, 7, 14, 30])
        
        # Check rolling statistics for temp_max and temp_min
        for window in [7, 14, 30]:
            assert f'temp_max_ma{window}' in df.columns, f"temp_max_ma{window} should be in columns"
            assert f'temp_min_ma{window}' in df.columns, f"temp_min_ma{window} should be in columns"
            assert f'temp_max_std{window}' in df.columns, f"temp_max_std{window} should be in columns"
            assert f'temp_min_std{window}' in df.columns, f"temp_min_std{window} should be in columns"
            
            # Verify values exist
            assert not df[f'temp_max_ma{window}'].isna().all(), f"temp_max_ma{window} should have values"
            assert not df[f'temp_min_ma{window}'].isna().all(), f"temp_min_ma{window} should have values"
    
    def test_create_features_temp_range(self, sample_weather_data):
        """Test that temperature range is calculated."""
        service = FeatureEngineeringService()
        
        df = service.create_features(sample_weather_data, 'temperature', [1, 7])
        
        # Check temp_range exists
        assert 'temp_range' in df.columns
        
        # Verify calculation
        expected_range = df['temp_max'] - df['temp_min']
        pd.testing.assert_series_equal(df['temp_range'], expected_range, check_names=False)
    
    def test_create_future_features_temp_max_min(self, sample_weather_data):
        """Test that future features include temp_max and temp_min lag features."""
        service = FeatureEngineeringService()
        lookback_days = [1, 7, 14, 30]
        prediction_days = 30
        
        future_df = service.create_future_features(
            sample_weather_data, 'temperature', prediction_days, lookback_days
        )
        
        # Check that future features include temp_max and temp_min lag features
        for lag in lookback_days:
            assert f'temp_max_lag{lag}' in future_df.columns, f"temp_max_lag{lag} should be in future features"
            assert f'temp_min_lag{lag}' in future_df.columns, f"temp_min_lag{lag} should be in future features"
            
            # Verify values are not all NaN
            assert not future_df[f'temp_max_lag{lag}'].isna().all(), f"temp_max_lag{lag} should have values"
            assert not future_df[f'temp_min_lag{lag}'].isna().all(), f"temp_min_lag{lag} should have values"
    
    def test_create_future_features_temp_max_min_rolling_stats(self, sample_weather_data):
        """Test that future features include temp_max and temp_min rolling statistics."""
        service = FeatureEngineeringService()
        prediction_days = 30
        
        future_df = service.create_future_features(
            sample_weather_data, 'temperature', prediction_days, [1, 7, 14, 30]
        )
        
        # Check rolling statistics in future features
        for window in [7, 14, 30]:
            assert f'temp_max_ma{window}' in future_df.columns, f"temp_max_ma{window} should be in future features"
            assert f'temp_min_ma{window}' in future_df.columns, f"temp_min_ma{window} should be in future features"
    
    def test_get_feature_names_includes_temp_max_min(self):
        """Test that get_feature_names() includes temp_max and temp_min features."""
        service = FeatureEngineeringService()
        lookback_days = [1, 7, 14, 30]
        
        feature_names = service.get_feature_names('temperature', lookback_days)
        
        # Check that temp_max and temp_min lag features are included
        for lag in lookback_days:
            assert f'temp_max_lag{lag}' in feature_names, f"temp_max_lag{lag} should be in feature names"
            assert f'temp_min_lag{lag}' in feature_names, f"temp_min_lag{lag} should be in feature names"
        
        # Check that temp_max and temp_min rolling stats are included
        for window in [7, 14, 30]:
            assert f'temp_max_ma{window}' in feature_names, f"temp_max_ma{window} should be in feature names"
            assert f'temp_min_ma{window}' in feature_names, f"temp_min_ma{window} should be in feature names"
            assert f'temp_max_std{window}' in feature_names, f"temp_max_std{window} should be in feature names"
            assert f'temp_min_std{window}' in feature_names, f"temp_min_std{window} should be in feature names"
    
    def test_create_features_no_nan_values(self, sample_weather_data):
        """Test that created features have no NaN values after fill."""
        service = FeatureEngineeringService()
        
        df = service.create_features(sample_weather_data, 'temperature', [1, 7, 14, 30])
        
        # After ffill and bfill, there should be no NaN values
        assert not df.isna().any().any(), "Features should not have NaN values after fill"
    
    def test_create_future_features_no_nan_values(self, sample_weather_data):
        """Test that future features have no NaN values."""
        service = FeatureEngineeringService()
        
        future_df = service.create_future_features(
            sample_weather_data, 'temperature', 30, [1, 7, 14, 30]
        )
        
        # Future features should not have NaN values
        assert not future_df.isna().any().any(), "Future features should not have NaN values"

