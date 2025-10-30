"""LightGBM-based weather prediction service implementation (Framework layer)."""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from concurrent.futures import ThreadPoolExecutor
import os
import time

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.adapter.interfaces.ml.prediction_service_interface import PredictionServiceInterface
from agrr_core.framework.services.ml.feature_engineering_service import FeatureEngineeringService

class LightGBMPredictionService(PredictionServiceInterface):
    """LightGBM-based prediction service (Framework layer implementation)."""
    
    def __init__(self, model_params: Optional[Dict[str, Any]] = None):
        """
        Initialize LightGBM prediction service.
        
        Args:
            model_params: Optional LightGBM parameters (defaults to optimized params)
        """
        if not LIGHTGBM_AVAILABLE:
            raise ImportError(
                "LightGBM is not installed. Install with: pip install lightgbm"
            )
        
        # Default optimized parameters
        self.model_params = model_params or {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.01,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'n_estimators': 1000,
            'early_stopping_rounds': 50,
        }
        
        self.feature_engineering = FeatureEngineeringService()
        self.model = None
        self.feature_names = None
    
    def predict(
        self,
        historical_data: List[WeatherData],
        metric: str,
        prediction_days: int,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict future values using LightGBM (implements PredictionModelInterface)."""
        config = {**model_config, 'prediction_days': prediction_days}
        return self._predict_single_metric(historical_data, metric, config)
    
    def evaluate(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate model accuracy (implements PredictionModelInterface)."""
        return self.evaluate_model_accuracy(test_data, predictions, metric)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get LightGBM model information (implements PredictionModelInterface)."""
        return {
            'model_type': 'lightgbm',
            'model_name': 'LightGBM',
            'description': 'Light Gradient Boosting Machine',
            'supports_confidence_intervals': True,
            'min_training_samples': 90,
            'recommended_prediction_days': 90,
            'max_prediction_days': 365,
        }
    
    def get_required_data_days(self) -> int:
        """Get minimum required data days (implements PredictionModelInterface)."""
        return 90
    
    def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using LightGBM with vectorized approach.
        
        Uses multi-task learning to predict all metrics simultaneously,
        eliminating redundant model training.
        """
        prof = os.getenv("AGRR_PROFILE") == "1"
        t_start = time.perf_counter() if prof else 0.0
        
        if len(historical_data) < 90:
            raise PredictionError(
                f"Insufficient data for LightGBM. Need at least 90 data points, got {len(historical_data)}."
            )
        
        # Use vectorized multi-task prediction
        if prof:
            print(f"[PROFILE] LightGBM: starting_vectorized_prediction metrics={metrics}", flush=True)
        
        # Create shared features once
        t_shared_start = time.perf_counter() if prof else 0.0
        shared_features = self._create_shared_features(historical_data, metrics, model_config)
        if prof:
            t_shared_end = time.perf_counter()
            print(f"[PROFILE] LightGBM: shared_features elapsed={t_shared_end-t_shared_start:.3f}s", flush=True)
        
        # Vectorized multi-task prediction
        results = self._predict_multiple_metrics_vectorized(
            historical_data, metrics, model_config, shared_features
        )
        
        if prof:
            t_total = time.perf_counter() - t_start
            print(f"[PROFILE] LightGBM: vectorized_prediction TOTAL elapsed={t_total:.3f}s", flush=True)
        
        return results
    
    def _predict_multiple_metrics_vectorized(
        self,
        historical_data: List[WeatherData],
        metrics: List[str],
        model_config: Dict[str, Any],
        shared_features: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Vectorized multi-task prediction using single model for all metrics."""
        prof = os.getenv("AGRR_PROFILE") == "1"
        t_start = time.perf_counter() if prof else 0.0
        
        # Extract shared features
        base_features = shared_features['base_features']
        lookback_days = shared_features['lookback_days']
        
        # Create multi-target features
        t_multi_start = time.perf_counter() if prof else 0.0
        multi_features_df = self._create_multi_target_features(
            historical_data, metrics, base_features, lookback_days
        )
        
        if prof:
            t_multi_end = time.perf_counter()
            print(f"[PROFILE] LightGBM: multi_target_features elapsed={t_multi_end-t_multi_start:.3f}s", flush=True)
        
        # Prepare training data for multi-task learning
        t_train_start = time.perf_counter() if prof else 0.0
        X, y_dict = self._prepare_multi_target_data(multi_features_df, metrics)
        
        # Split into train/validation
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train_dict = {metric: y_dict[metric][:split_idx] for metric in metrics}
        y_val_dict = {metric: y_dict[metric][split_idx:] for metric in metrics}
        
        if prof:
            t_train_end = time.perf_counter()
            print(f"[PROFILE] LightGBM: multi_target_preparation elapsed={t_train_end-t_train_start:.3f}s features={X.shape[1]} samples={len(X)}", flush=True)
        
        # Train single multi-task model
        t_model_start = time.perf_counter() if prof else 0.0
        models = {}
        
        # Train separate models for each metric (simplified approach)
        # In a true multi-task setup, we would use a single model with multiple outputs
        for metric in metrics:
            y_train = y_train_dict[metric]
            y_val = y_val_dict[metric]
            
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            # Use optimized parameters for faster training
            params = self.model_params.copy()
            params.update({
                'n_estimators': 500,  # Reduced from 1000
                'early_stopping_rounds': 30,  # More aggressive early stopping
                'learning_rate': 0.05,  # Higher learning rate for faster convergence
            })
            params.update(model_config.get('lgb_params', {}))
            
            model = lgb.train(
                params,
                train_data,
                valid_sets=[val_data],
                callbacks=[lgb.early_stopping(params.get('early_stopping_rounds', 30))],
            )
            models[metric] = model
        
        if prof:
            t_model_end = time.perf_counter()
            print(f"[PROFILE] LightGBM: multi_target_training elapsed={t_model_end-t_model_start:.3f}s", flush=True)
        
        # Generate predictions for all metrics
        t_predict_start = time.perf_counter() if prof else 0.0
        prediction_days = model_config.get('prediction_days', 30)
        
        # Create future features for all metrics
        future_df = self._create_multi_target_future_features(
            historical_data, metrics, prediction_days, lookback_days, shared_features['climatological_stats']
        )
        
        # Predict all metrics
        results = {}
        for metric in models:
            # Get feature names used by the model
            feature_names = models[metric].feature_name()
            
            # Create X_future with all required features, filling missing ones with 0
            X_future = pd.DataFrame(index=future_df.index)
            for feature in feature_names:
                if feature in future_df.columns:
                    X_future[feature] = future_df[feature]
                else:
                    # Fill missing features with 0
                    X_future[feature] = 0
            
            # Ensure feature order matches training
            X_future = X_future[feature_names]
            
            predictions = models[metric].predict(X_future, num_iteration=models[metric].best_iteration)
            
            # Create forecast entities
            forecasts = []
            start_date = historical_data[-1].time + timedelta(days=1)
            
            for i, prediction in enumerate(predictions):
                forecast_date = start_date + timedelta(days=i)
                forecast = Forecast(
                    date=forecast_date,
                    predicted_value=float(prediction),
                    confidence_lower=None,  # Simplified for vectorized approach
                    confidence_upper=None
                )
                forecasts.append(forecast)
            
            results[metric] = forecasts
        
        if prof:
            t_predict_end = time.perf_counter()
            t_total = t_predict_end - t_start
            print(f"[PROFILE] LightGBM: multi_target_prediction elapsed={t_predict_end-t_predict_start:.3f}s", flush=True)
            print(f"[PROFILE] LightGBM: vectorized_TOTAL elapsed={t_total:.3f}s", flush=True)
        
        return results
    
    def _create_multi_target_features(
        self,
        historical_data: List[WeatherData],
        metrics: List[str],
        base_features: pd.DataFrame,
        lookback_days: List[int]
    ) -> pd.DataFrame:
        """Create features for multi-target prediction."""
        features_df = base_features.copy()
        
        # Add target columns for all metrics
        for metric in metrics:
            target_col = self.feature_engineering._get_target_column(metric)
            
            if metric == 'temperature':
                # Already in base_features
                continue
            elif metric == 'temperature_max':
                metric_data = [d.temperature_2m_max for d in historical_data]
            elif metric == 'temperature_min':
                metric_data = [d.temperature_2m_min for d in historical_data]
            elif metric == 'precipitation':
                metric_data = [d.precipitation_sum for d in historical_data]
            elif metric == 'sunshine':
                metric_data = [d.sunshine_duration for d in historical_data]
            
            features_df[target_col] = metric_data
        
        return features_df
    
    def _prepare_multi_target_data(
        self,
        features_df: pd.DataFrame,
        metrics: List[str]
    ) -> tuple:
        """Prepare data for multi-target learning."""
        # Get feature names (excluding target columns)
        target_cols = [self.feature_engineering._get_target_column(metric) for metric in metrics]
        feature_cols = [col for col in features_df.columns if col not in target_cols and col != 'date']
        
        X = features_df[feature_cols]
        y_dict = {}
        
        for metric in metrics:
            target_col = self.feature_engineering._get_target_column(metric)
            y_dict[metric] = features_df[target_col].values
        
        return X, y_dict
    
    def _create_multi_target_future_features(
        self,
        historical_data: List[WeatherData],
        metrics: List[str],
        prediction_days: int,
        lookback_days: List[int],
        climatological_stats: Dict[str, Dict[str, Dict[str, float]]]
    ) -> pd.DataFrame:
        """Create future features for multi-target prediction."""
        # Generate future dates
        last_date = historical_data[-1].time
        future_dates = [last_date + timedelta(days=i+1) for i in range(prediction_days)]
        
        future_rows = []
        
        for future_date in future_dates:
            row = {}
            row['date'] = future_date
            
            # Temporal features
            row['year'] = future_date.year
            row['month'] = future_date.month
            row['day'] = future_date.day
            row['day_of_year'] = future_date.timetuple().tm_yday
            row['day_of_week'] = future_date.weekday()
            row['week_of_year'] = future_date.isocalendar()[1]
            row['is_weekend'] = 1 if future_date.weekday() >= 5 else 0
            
            # Cyclical encoding
            row['month_sin'] = np.sin(2 * np.pi * row['month'] / 12)
            row['month_cos'] = np.cos(2 * np.pi * row['month'] / 12)
            row['day_of_year_sin'] = np.sin(2 * np.pi * row['day_of_year'] / 365)
            row['day_of_year_cos'] = np.cos(2 * np.pi * row['day_of_year'] / 365)
            
            # Season flags
            row['is_winter'] = 1 if row['month'] in [12, 1, 2] else 0
            row['is_spring'] = 1 if row['month'] in [3, 4, 5] else 0
            row['is_summer'] = 1 if row['month'] in [6, 7, 8] else 0
            row['is_autumn'] = 1 if row['month'] in [9, 10, 11] else 0
            
            future_rows.append(row)
        
        future_df = pd.DataFrame(future_rows)
        
        # Apply climatological statistics for all metrics
        for metric in metrics:
            target_col = self.feature_engineering._get_target_column(metric)
            climatological_stats_metric = climatological_stats[metric]
            
            for i, future_date in enumerate(future_dates):
                month_day = f"{future_date.month:02d}-{future_date.day:02d}"
                
                if month_day in climatological_stats_metric:
                    stats = climatological_stats_metric[month_day]
                    
                    # Apply climatological values
                    climatological_value = stats['mean']
                    for lag in lookback_days:
                        future_df.loc[i, f'{target_col}_lag{lag}'] = climatological_value
                    
                    # Rolling statistics
                    future_df.loc[i, f'{target_col}_ma7'] = climatological_value
                    future_df.loc[i, f'{target_col}_ma14'] = climatological_value
                    future_df.loc[i, f'{target_col}_ma30'] = climatological_value
                    future_df.loc[i, f'{target_col}_std7'] = stats['std']
                    future_df.loc[i, f'{target_col}_std14'] = stats['std']
                    future_df.loc[i, f'{target_col}_std30'] = stats['std']
                    future_df.loc[i, f'{target_col}_min7'] = stats['min']
                    future_df.loc[i, f'{target_col}_min14'] = stats['min']
                    future_df.loc[i, f'{target_col}_min30'] = stats['min']
                    future_df.loc[i, f'{target_col}_max7'] = stats['max']
                    future_df.loc[i, f'{target_col}_max14'] = stats['max']
                    future_df.loc[i, f'{target_col}_max30'] = stats['max']
                    future_df.loc[i, f'{target_col}_diff1'] = 0
                    future_df.loc[i, f'{target_col}_diff7'] = 0
                    future_df.loc[i, f'{target_col}_ema7'] = climatological_value
                    future_df.loc[i, f'{target_col}_ema30'] = climatological_value
                    
                    # Add cross-metric features for temperature
                    if metric == 'temperature' and 'temp_max_mean' in stats:
                        climatological_max = stats['temp_max_mean']
                        for lag in lookback_days:
                            future_df.loc[i, f'temp_max_lag{lag}'] = climatological_max
                        
                        future_df.loc[i, 'temp_max_ma7'] = climatological_max
                        future_df.loc[i, 'temp_max_ma14'] = climatological_max
                        future_df.loc[i, 'temp_max_ma30'] = climatological_max
                        future_df.loc[i, 'temp_max_std7'] = stats['temp_max_std']
                        future_df.loc[i, 'temp_max_std14'] = stats['temp_max_std']
                        future_df.loc[i, 'temp_max_std30'] = stats['temp_max_std']
                        
                        climatological_min = stats['temp_min_mean']
                        for lag in lookback_days:
                            future_df.loc[i, f'temp_min_lag{lag}'] = climatological_min
                        
                        future_df.loc[i, 'temp_min_ma7'] = climatological_min
                        future_df.loc[i, 'temp_min_ma14'] = climatological_min
                        future_df.loc[i, 'temp_min_ma30'] = climatological_min
                        future_df.loc[i, 'temp_min_std7'] = stats['temp_min_std']
                        future_df.loc[i, 'temp_min_std14'] = stats['temp_min_std']
                        future_df.loc[i, 'temp_min_std30'] = stats['temp_min_std']
                else:
                    raise ValueError(
                        f"No historical data found for date {future_date.strftime('%Y-%m-%d')} (month-day: {month_day}). "
                        f"Metric: {metric}. Need at least 1 historical sample for climatological prediction."
                    )
        
        # Add cross-metric features for temperature
        if 'temperature' in metrics:
            # Add temp_range feature
            for i, future_date in enumerate(future_dates):
                month_day = f"{future_date.month:02d}-{future_date.day:02d}"
                if month_day in climatological_stats['temperature'] and 'temp_max_mean' in climatological_stats['temperature'][month_day]:
                    temp_max = climatological_stats['temperature'][month_day]['temp_max_mean']
                    temp_min = climatological_stats['temperature'][month_day]['temp_min_mean']
                    future_df.loc[i, 'temp_range'] = temp_max - temp_min
                else:
                    future_df.loc[i, 'temp_range'] = 0  # Default value
            
            # Add precipitation features
            future_df['has_precipitation'] = 0  # Unknown for future
            future_df['precip_rolling7'] = 0  # Unknown for future
        
        # Fill any remaining NaN
        future_df = future_df.ffill().bfill().fillna(0)
        
        return future_df
    
    def _create_shared_features(
        self,
        historical_data: List[WeatherData],
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create shared features that can be reused across multiple metrics.
        
        This optimization reduces redundant feature engineering computation.
        """
        prof = os.getenv("AGRR_PROFILE") == "1"
        t_shared_start = time.perf_counter() if prof else 0.0
        
        # Extract lookback days from config
        lookback_days = model_config.get('lookback_days', [1, 7, 14, 30])
        
        # Create base features that are common across all metrics
        t_base_start = time.perf_counter() if prof else 0.0
        base_features = self.feature_engineering.create_features(
            historical_data, 'temperature', lookback_days  # Use temperature as base
        )
        if prof:
            t_base_end = time.perf_counter()
            print(f"[PROFILE] LightGBM: base_features elapsed={t_base_end-t_base_start:.3f}s samples={len(historical_data)}", flush=True)
        
        # Pre-compute climatological statistics for all metrics
        t_climate_start = time.perf_counter() if prof else 0.0
        climatological_stats = {}
        for metric in metrics:
            climatological_stats[metric] = self.feature_engineering._precompute_climatological_stats(
                historical_data, metric
            )
        
        if prof:
            t_climate_end = time.perf_counter()
            t_shared_total = t_climate_end - t_shared_start
            print(f"[PROFILE] LightGBM: climatological_stats elapsed={t_climate_end-t_climate_start:.3f}s metrics={len(metrics)}", flush=True)
            print(f"[PROFILE] LightGBM: shared_features TOTAL elapsed={t_shared_total:.3f}s", flush=True)
        
        return {
            'base_features': base_features,
            'climatological_stats': climatological_stats,
            'lookback_days': lookback_days,
            'feature_names': self.feature_engineering.get_feature_names('temperature', lookback_days)
        }
    
    def _predict_single_metric_optimized(
        self,
        historical_data: List[WeatherData],
        metric: str,
        model_config: Dict[str, Any],
        shared_features: Dict[str, Any]
    ) -> List[Forecast]:
        """Optimized single metric prediction using shared features."""
        
        # Enable detailed profiling
        prof = os.getenv("AGRR_PROFILE") == "1"
        t_start = time.perf_counter() if prof else 0.0
        
        if len(historical_data) < 90:
            raise PredictionError(
                f"Insufficient data for LightGBM. Need at least 90 data points, got {len(historical_data)}."
            )
        
        # Use shared features
        t_feature_start = time.perf_counter() if prof else 0.0
        lookback_days = shared_features['lookback_days']
        base_features = shared_features['base_features']
        climatological_stats = shared_features['climatological_stats'][metric]
        
        # Get target column for this metric
        target_col = self.feature_engineering._get_target_column(metric)
        
        # Create metric-specific features from base features
        features_df = base_features.copy()
        
        # Update target column if different from temperature
        if metric != 'temperature':
            # Extract metric-specific data
            metric_data = []
            for hist_data in historical_data:
                if metric == 'temperature_max':
                    metric_data.append(hist_data.temperature_2m_max)
                elif metric == 'temperature_min':
                    metric_data.append(hist_data.temperature_2m_min)
                elif metric == 'precipitation':
                    metric_data.append(hist_data.precipitation_sum)
                elif metric == 'sunshine':
                    metric_data.append(hist_data.sunshine_duration)
            
            # Update target column
            features_df[target_col] = metric_data
        
        if prof:
            t_feature_end = time.perf_counter()
            print(f"[PROFILE] LightGBM-{metric}: feature_preparation elapsed={t_feature_end-t_feature_start:.3f}s", flush=True)
        
        # Get feature names for this metric
        t_train_start = time.perf_counter() if prof else 0.0
        feature_names = self.feature_engineering.get_feature_names(metric, lookback_days)
        
        # Filter to only available features
        available_features = [f for f in feature_names if f in features_df.columns]
        
        # Prepare training data
        X = features_df[available_features]
        y = features_df[target_col]
        
        # Split into train/validation (use last 20% for validation)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        if prof:
            t_train_prep = time.perf_counter()
            print(f"[PROFILE] LightGBM-{metric}: train_preparation elapsed={t_train_prep-t_train_start:.3f}s features={len(available_features)} samples={len(X)}", flush=True)
        
        # Train LightGBM model
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        # Update model parameters from config
        params = self.model_params.copy()
        params.update(model_config.get('lgb_params', {}))
        
        # Train model
        t_model_start = time.perf_counter() if prof else 0.0
        model = lgb.train(
            params,
            train_data,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(params.get('early_stopping_rounds', 50))],
        )
        
        if prof:
            t_model_end = time.perf_counter()
            print(f"[PROFILE] LightGBM-{metric}: model_training elapsed={t_model_end-t_model_start:.3f}s iterations={model.best_iteration}", flush=True)
        
        # Make predictions using optimized future features
        prediction_days = model_config.get('prediction_days', 30)
        
        # Create optimized future features using pre-computed statistics
        t_future_start = time.perf_counter() if prof else 0.0
        future_df = self._create_optimized_future_features(
            historical_data, metric, prediction_days, lookback_days, climatological_stats
        )
        
        if prof:
            t_future_end = time.perf_counter()
            print(f"[PROFILE] LightGBM-{metric}: future_features elapsed={t_future_end-t_future_start:.3f}s days={prediction_days}", flush=True)
        
        # Filter to available features
        X_future = future_df[available_features]
        
        # Predict all days at once
        t_predict_start = time.perf_counter() if prof else 0.0
        predictions = model.predict(X_future, num_iteration=model.best_iteration)
        
        if prof:
            t_predict_end = time.perf_counter()
            print(f"[PROFILE] LightGBM-{metric}: prediction elapsed={t_predict_end-t_predict_start:.3f}s", flush=True)
        
        # Calculate confidence intervals
        confidence_lower = None
        confidence_upper = None
        
        if model_config.get('calculate_confidence_intervals', True):
            val_predictions = model.predict(X_val, num_iteration=model.best_iteration)
            residuals = y_val - val_predictions
            
            std_error = np.std(residuals)
            predictions_array = np.array(predictions)
            confidence_lower = predictions_array - 1.96 * std_error
            confidence_upper = predictions_array + 1.96 * std_error
        
        # Create forecast entities
        t_forecast_start = time.perf_counter() if prof else 0.0
        forecasts = []
        start_date = historical_data[-1].time + timedelta(days=1)
        
        for i, prediction in enumerate(predictions):
            forecast_date = start_date + timedelta(days=i)
            
            lower = confidence_lower[i] if confidence_lower is not None else None
            upper = confidence_upper[i] if confidence_upper is not None else None
            
            forecast = Forecast(
                date=forecast_date,
                predicted_value=float(prediction),
                confidence_lower=float(lower) if lower is not None else None,
                confidence_upper=float(upper) if upper is not None else None
            )
            forecasts.append(forecast)
        
        if prof:
            t_forecast_end = time.perf_counter()
            t_total = t_forecast_end - t_start
            print(f"[PROFILE] LightGBM-{metric}: forecast_creation elapsed={t_forecast_end-t_forecast_start:.3f}s", flush=True)
            print(f"[PROFILE] LightGBM-{metric}: TOTAL elapsed={t_total:.3f}s", flush=True)
        
        return forecasts
    
    def _create_optimized_future_features(
        self,
        historical_data: List[WeatherData],
        metric: str,
        prediction_days: int,
        lookback_days: List[int],
        climatological_stats: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        """Create optimized future features using pre-computed statistics."""
        # Generate future dates
        last_date = historical_data[-1].time
        future_dates = [last_date + timedelta(days=i+1) for i in range(prediction_days)]
        
        future_rows = []
        target_col = self.feature_engineering._get_target_column(metric)
        
        for future_date in future_dates:
            row = {}
            row['date'] = future_date
            
            # Temporal features
            row['year'] = future_date.year
            row['month'] = future_date.month
            row['day'] = future_date.day
            row['day_of_year'] = future_date.timetuple().tm_yday
            row['day_of_week'] = future_date.weekday()
            row['week_of_year'] = future_date.isocalendar()[1]
            row['is_weekend'] = 1 if future_date.weekday() >= 5 else 0
            
            # Cyclical encoding
            row['month_sin'] = np.sin(2 * np.pi * row['month'] / 12)
            row['month_cos'] = np.cos(2 * np.pi * row['month'] / 12)
            row['day_of_year_sin'] = np.sin(2 * np.pi * row['day_of_year'] / 365)
            row['day_of_year_cos'] = np.cos(2 * np.pi * row['day_of_year'] / 365)
            
            # Season flags
            row['is_winter'] = 1 if row['month'] in [12, 1, 2] else 0
            row['is_spring'] = 1 if row['month'] in [3, 4, 5] else 0
            row['is_summer'] = 1 if row['month'] in [6, 7, 8] else 0
            row['is_autumn'] = 1 if row['month'] in [9, 10, 11] else 0
            
            future_rows.append(row)
        
        future_df = pd.DataFrame(future_rows)
        
        # Apply pre-computed climatological statistics
        for i, future_date in enumerate(future_dates):
            month_day = f"{future_date.month:02d}-{future_date.day:02d}"
            
            if month_day in climatological_stats:
                stats = climatological_stats[month_day]
                
                # Apply climatological values
                climatological_value = stats['mean']
                for lag in lookback_days:
                    future_df.loc[i, f'{target_col}_lag{lag}'] = climatological_value
                
                # Rolling statistics
                future_df.loc[i, f'{target_col}_ma7'] = climatological_value
                future_df.loc[i, f'{target_col}_ma14'] = climatological_value
                future_df.loc[i, f'{target_col}_ma30'] = climatological_value
                future_df.loc[i, f'{target_col}_std7'] = stats['std']
                future_df.loc[i, f'{target_col}_std14'] = stats['std']
                future_df.loc[i, f'{target_col}_std30'] = stats['std']
                future_df.loc[i, f'{target_col}_min7'] = stats['min']
                future_df.loc[i, f'{target_col}_min14'] = stats['min']
                future_df.loc[i, f'{target_col}_min30'] = stats['min']
                future_df.loc[i, f'{target_col}_max7'] = stats['max']
                future_df.loc[i, f'{target_col}_max14'] = stats['max']
                future_df.loc[i, f'{target_col}_max30'] = stats['max']
                future_df.loc[i, f'{target_col}_diff1'] = 0
                future_df.loc[i, f'{target_col}_diff7'] = 0
                future_df.loc[i, f'{target_col}_ema7'] = climatological_value
                future_df.loc[i, f'{target_col}_ema30'] = climatological_value
                
                # Add cross-metric features for temperature
                if metric == 'temperature' and 'temp_max_mean' in stats:
                    climatological_max = stats['temp_max_mean']
                    for lag in lookback_days:
                        future_df.loc[i, f'temp_max_lag{lag}'] = climatological_max
                    
                    future_df.loc[i, 'temp_max_ma7'] = climatological_max
                    future_df.loc[i, 'temp_max_ma14'] = climatological_max
                    future_df.loc[i, 'temp_max_ma30'] = climatological_max
                    future_df.loc[i, 'temp_max_std7'] = stats['temp_max_std']
                    future_df.loc[i, 'temp_max_std14'] = stats['temp_max_std']
                    future_df.loc[i, 'temp_max_std30'] = stats['temp_max_std']
                    
                    climatological_min = stats['temp_min_mean']
                    for lag in lookback_days:
                        future_df.loc[i, f'temp_min_lag{lag}'] = climatological_min
                    
                    future_df.loc[i, 'temp_min_ma7'] = climatological_min
                    future_df.loc[i, 'temp_min_ma14'] = climatological_min
                    future_df.loc[i, 'temp_min_ma30'] = climatological_min
                    future_df.loc[i, 'temp_min_std7'] = stats['temp_min_std']
                    future_df.loc[i, 'temp_min_std14'] = stats['temp_min_std']
                    future_df.loc[i, 'temp_min_std30'] = stats['temp_min_std']
            else:
                raise ValueError(
                    f"No historical data found for date {future_date.strftime('%Y-%m-%d')} (month-day: {month_day}). "
                    f"Metric: {metric}. Need at least 1 historical sample for climatological prediction."
                )
        
        # Add cross-metric features for temperature
        if metric == 'temperature':
            # Add temp_range feature
            for i, future_date in enumerate(future_dates):
                month_day = f"{future_date.month:02d}-{future_date.day:02d}"
                if month_day in climatological_stats and 'temp_max_mean' in climatological_stats[month_day]:
                    temp_max = climatological_stats[month_day]['temp_max_mean']
                    temp_min = climatological_stats[month_day]['temp_min_mean']
                    future_df.loc[i, 'temp_range'] = temp_max - temp_min
                else:
                    future_df.loc[i, 'temp_range'] = 0  # Default value
            
            # Add precipitation features
            future_df['has_precipitation'] = 0  # Unknown for future
            future_df['precip_rolling7'] = 0  # Unknown for future
        
        # Fill any remaining NaN
        future_df = future_df.ffill().bfill().fillna(0)
        
        return future_df
    
    def _predict_single_metric(
        self, 
        historical_data: List[WeatherData], 
        metric: str,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict single metric using LightGBM."""
        
        if len(historical_data) < 90:
            raise PredictionError(
                f"Insufficient data for LightGBM. Need at least 90 data points, got {len(historical_data)}."
            )
        
        # Extract lookback days from config
        lookback_days = model_config.get('lookback_days', [1, 7, 14, 30])
        
        # Create features from historical data
        features_df = self.feature_engineering.create_features(
            historical_data, metric, lookback_days
        )
        
        # Get target column
        target_col = self.feature_engineering._get_target_column(metric)
        
        # Get feature names (excluding date and target)
        feature_names = self.feature_engineering.get_feature_names(metric, lookback_days)
        
        # Filter to only available features
        available_features = [f for f in feature_names if f in features_df.columns]
        
        # Prepare training data
        X = features_df[available_features]
        y = features_df[target_col]
        
        # Split into train/validation (use last 20% for validation)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Train LightGBM model
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        # Update model parameters from config
        params = self.model_params.copy()
        params.update(model_config.get('lgb_params', {}))
        
        # Train model
        model = lgb.train(
            params,
            train_data,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(params.get('early_stopping_rounds', 50))],
        )
        
        # Save model and feature names for feature importance
        self.model = model
        self.feature_names = available_features
        
        # Make direct predictions (non-autoregressive)
        # Use historical patterns for future lag features
        prediction_days = model_config.get('prediction_days', 30)
        
        # Create features for all future days at once using historical patterns
        future_df = self.feature_engineering.create_future_features(
            historical_data, metric, prediction_days, lookback_days
        )
        
        # Filter to available features
        X_future = future_df[available_features]
        
        # Predict all days at once
        predictions = model.predict(X_future, num_iteration=model.best_iteration)
        
        # Calculate confidence intervals using quantile regression (if enabled)
        confidence_lower = None
        confidence_upper = None
        
        if model_config.get('calculate_confidence_intervals', True):
            # Estimate uncertainty using validation residuals
            val_predictions = model.predict(X_val, num_iteration=model.best_iteration)
            residuals = y_val - val_predictions
            
            # Use 95% confidence interval
            std_error = np.std(residuals)
            predictions_array = np.array(predictions)
            confidence_lower = predictions_array - 1.96 * std_error
            confidence_upper = predictions_array + 1.96 * std_error
        
        # Create forecast entities
        forecasts = []
        start_date = historical_data[-1].time + timedelta(days=1)
        
        for i, prediction in enumerate(predictions):
            forecast_date = start_date + timedelta(days=i)
            
            lower = confidence_lower[i] if confidence_lower is not None else None
            upper = confidence_upper[i] if confidence_upper is not None else None
            
            forecast = Forecast(
                date=forecast_date,
                predicted_value=float(prediction),
                confidence_lower=float(lower) if lower is not None else None,
                confidence_upper=float(upper) if upper is not None else None
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def evaluate_model_accuracy(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate LightGBM model accuracy."""
        # Extract target column
        target_col = self.feature_engineering._get_target_column(metric)
        
        # Extract actual values
        actual_values = []
        for weather_data in test_data:
            value = None
            if metric == 'temperature':
                value = weather_data.temperature_2m_mean
            elif metric == 'temperature_max':
                value = weather_data.temperature_2m_max
            elif metric == 'temperature_min':
                value = weather_data.temperature_2m_min
            elif metric == 'precipitation':
                value = weather_data.precipitation_sum
            elif metric == 'sunshine':
                value = weather_data.sunshine_duration
            
            actual_values.append(value)
        
        # Extract predicted values
        predicted_values = [f.predicted_value for f in predictions]
        
        # Ensure same length
        min_length = min(len(actual_values), len(predicted_values))
        actual_values = actual_values[:min_length]
        predicted_values = predicted_values[:min_length]
        
        # Calculate metrics
        mae = np.mean(np.abs(np.array(actual_values) - np.array(predicted_values)))
        mse = np.mean((np.array(actual_values) - np.array(predicted_values)) ** 2)
        rmse = np.sqrt(mse)
        
        # Calculate MAPE (avoid division by zero)
        mape = np.mean([
            abs((actual - pred) / actual) * 100 
            for actual, pred in zip(actual_values, predicted_values) 
            if actual != 0
        ])
        
        # Calculate R²
        ss_res = np.sum((np.array(actual_values) - np.array(predicted_values)) ** 2)
        ss_tot = np.sum((np.array(actual_values) - np.mean(actual_values)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape,
            'r2': r2
        }
    
    def train_model(
        self,
        training_data: List[WeatherData],
        model_config: Dict[str, Any],
        metric: str
    ) -> Dict[str, Any]:
        """Train LightGBM model."""
        # This is handled in _predict_single_metric
        # Return model info
        return {
            'model_type': 'lightgbm',
            'metric': metric,
            'training_samples': len(training_data),
            'status': 'trained'
        }
    
    def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get LightGBM model information."""
        return {
            'model_type': 'lightgbm',
            'description': 'Light Gradient Boosting Machine',
            'supports_confidence_intervals': True,
            'min_training_samples': 90,
            'recommended_params': {
                'num_leaves': 31,
                'learning_rate': 0.01,
                'n_estimators': 1000,
            },
            'features': [
                'temporal_encoding',
                'lag_features',
                'rolling_statistics',
                'cross_metric_features',
            ]
        }
    
    def predict_with_confidence_intervals(
        self,
        historical_data: List[WeatherData],
        prediction_days: int,
        confidence_level: float,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict with confidence intervals using LightGBM."""
        return self._predict_single_metric(historical_data, 'temperature', {
            **model_config,
            'prediction_days': prediction_days,
            'calculate_confidence_intervals': True,
        })
    
    def batch_predict(
        self,
        historical_data_list: List[List[WeatherData]],
        model_config: Dict[str, Any],
        metrics: List[str]
    ) -> List[Dict[str, List[Forecast]]]:
        """Perform batch prediction using LightGBM."""
        results = []
        
        for historical_data in historical_data_list:
            try:
                result = self.predict_multiple_metrics(historical_data, metrics, model_config)
                results.append(result)
            except Exception as e:
                # Add error result
                results.append({'error': str(e)})
        
        return results
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance from trained model.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.model is None or self.feature_names is None:
            return None
        
        importance = self.model.feature_importance(importance_type='gain')
        return dict(zip(self.feature_names, importance))

