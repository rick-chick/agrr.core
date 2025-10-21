"""Feature engineering service for time series prediction."""

from typing import List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from agrr_core.entity import WeatherData


class FeatureEngineeringService:
    """Service for creating features from weather time series data."""
    
    @staticmethod
    def create_features(
        historical_data: List[WeatherData],
        metric: str,
        lookback_days: List[int] = None
    ) -> pd.DataFrame:
        """
        Create rich feature set for machine learning models.
        
        Args:
            historical_data: Historical weather data
            metric: Metric to predict ('temperature', 'precipitation', etc.)
            lookback_days: List of lookback periods for lag features (default: [1, 7, 14, 30])
            
        Returns:
            DataFrame with engineered features
        """
        if lookback_days is None:
            lookback_days = [1, 7, 14, 30]
        
        # Extract base data
        df = pd.DataFrame([{
            'date': d.time,
            'temperature': d.temperature_2m_mean,
            'temp_max': d.temperature_2m_max,
            'temp_min': d.temperature_2m_min,
            'precipitation': d.precipitation_sum,
            'sunshine': d.sunshine_duration,
        } for d in historical_data])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # Target variable
        target_col = FeatureEngineeringService._get_target_column(metric)
        
        # Temporal features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_year'] = df['date'].dt.dayofyear
        df['day_of_week'] = df['date'].dt.dayofweek
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Cyclical encoding for month and day_of_year
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_of_year_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365)
        df['day_of_year_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365)
        
        # Season flags
        df['is_winter'] = df['month'].isin([12, 1, 2]).astype(int)
        df['is_spring'] = df['month'].isin([3, 4, 5]).astype(int)
        df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)
        df['is_autumn'] = df['month'].isin([9, 10, 11]).astype(int)
        
        # Lag features
        for lag in lookback_days:
            df[f'{target_col}_lag{lag}'] = df[target_col].shift(lag)
        
        # Rolling statistics
        for window in [7, 14, 30]:
            df[f'{target_col}_ma{window}'] = df[target_col].rolling(window=window, min_periods=1).mean()
            df[f'{target_col}_std{window}'] = df[target_col].rolling(window=window, min_periods=1).std()
            df[f'{target_col}_min{window}'] = df[target_col].rolling(window=window, min_periods=1).min()
            df[f'{target_col}_max{window}'] = df[target_col].rolling(window=window, min_periods=1).max()
        
        # Difference features
        df[f'{target_col}_diff1'] = df[target_col].diff(1)
        df[f'{target_col}_diff7'] = df[target_col].diff(7)
        
        # Exponential moving average
        df[f'{target_col}_ema7'] = df[target_col].ewm(span=7, adjust=False).mean()
        df[f'{target_col}_ema30'] = df[target_col].ewm(span=30, adjust=False).mean()
        
        # Cross-metric features (if available)
        if metric == 'temperature':
            # Temperature range
            df['temp_range'] = df['temp_max'] - df['temp_min']
            
            # Lag features for temp_max and temp_min
            for lag in lookback_days:
                df[f'temp_max_lag{lag}'] = df['temp_max'].shift(lag)
                df[f'temp_min_lag{lag}'] = df['temp_min'].shift(lag)
            
            # Rolling statistics for temp_max
            for window in [7, 14, 30]:
                df[f'temp_max_ma{window}'] = df['temp_max'].rolling(window=window, min_periods=1).mean()
                df[f'temp_max_std{window}'] = df['temp_max'].rolling(window=window, min_periods=1).std()
            
            # Rolling statistics for temp_min
            for window in [7, 14, 30]:
                df[f'temp_min_ma{window}'] = df['temp_min'].rolling(window=window, min_periods=1).mean()
                df[f'temp_min_std{window}'] = df['temp_min'].rolling(window=window, min_periods=1).std()
            
            # Interaction with precipitation (雨の日は気温が安定しやすい)
            if 'precipitation' in df.columns:
                df['has_precipitation'] = (df['precipitation'] > 0).astype(int)
                df['precip_rolling7'] = df['precipitation'].rolling(window=7, min_periods=1).sum()
        
        # Fill NaN values (from lag features) with forward fill then backward fill
        df = df.ffill().bfill()
        
        return df
    
    @staticmethod
    def create_future_features(
        historical_data: List[WeatherData],
        metric: str,
        prediction_days: int,
        lookback_days: List[int] = None
    ) -> pd.DataFrame:
        """
        Create features for future prediction dates using historical patterns.
        
        Uses same-period data from previous years for lag features.
        
        Args:
            historical_data: Historical weather data
            metric: Metric to predict
            prediction_days: Number of days to predict
            lookback_days: List of lookback periods
            
        Returns:
            DataFrame with features for prediction
        """
        if lookback_days is None:
            lookback_days = [1, 7, 14, 30]
        
        # Create features from historical data
        historical_features = FeatureEngineeringService.create_features(
            historical_data, metric, lookback_days
        )
        
        # Get target column
        target_col = FeatureEngineeringService._get_target_column(metric)
        
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
        
        # For lag features, use same period from previous years (climatological approach)
        # This is more reliable than autoregressive for long-term predictions
        for i, future_date in enumerate(future_dates):
            month_day = f"{future_date.month:02d}-{future_date.day:02d}"
            
            # Find same month-day in historical data (from last few years)
            same_period_values = []
            same_period_max_values = []
            same_period_min_values = []
            
            for hist_data in historical_data:
                hist_month_day = f"{hist_data.time.month:02d}-{hist_data.time.day:02d}"
                if hist_month_day == month_day:
                    val = None
                    if metric == 'temperature':
                        val = hist_data.temperature_2m_mean
                        # Also collect temp_max and temp_min for cross-metric features
                        if hist_data.temperature_2m_max is not None:
                            same_period_max_values.append(hist_data.temperature_2m_max)
                        if hist_data.temperature_2m_min is not None:
                            same_period_min_values.append(hist_data.temperature_2m_min)
                    elif metric == 'temperature_max':
                        val = hist_data.temperature_2m_max
                        # Also collect for self-features
                        if hist_data.temperature_2m_max is not None:
                            same_period_max_values.append(hist_data.temperature_2m_max)
                    elif metric == 'temperature_min':
                        val = hist_data.temperature_2m_min
                        # Also collect for self-features
                        if hist_data.temperature_2m_min is not None:
                            same_period_min_values.append(hist_data.temperature_2m_min)
                    elif metric == 'precipitation':
                        val = hist_data.precipitation_sum
                    elif metric == 'sunshine':
                        val = hist_data.sunshine_duration
                    
                    if val is not None:
                        same_period_values.append(val)
            
            # Use mean of same period from historical data
            if same_period_values:
                # Lag features: use historical mean for this day
                climatological_value = np.mean(same_period_values)
                for lag in lookback_days:
                    future_df.loc[i, f'{target_col}_lag{lag}'] = climatological_value
                
                # Rolling statistics: use historical statistics for this period
                future_df.loc[i, f'{target_col}_ma7'] = climatological_value
                future_df.loc[i, f'{target_col}_ma14'] = climatological_value
                future_df.loc[i, f'{target_col}_ma30'] = climatological_value
                future_df.loc[i, f'{target_col}_std7'] = np.std(same_period_values) if len(same_period_values) > 1 else 0
                future_df.loc[i, f'{target_col}_std14'] = np.std(same_period_values) if len(same_period_values) > 1 else 0
                future_df.loc[i, f'{target_col}_std30'] = np.std(same_period_values) if len(same_period_values) > 1 else 0
                future_df.loc[i, f'{target_col}_min7'] = np.min(same_period_values)
                future_df.loc[i, f'{target_col}_min14'] = np.min(same_period_values)
                future_df.loc[i, f'{target_col}_min30'] = np.min(same_period_values)
                future_df.loc[i, f'{target_col}_max7'] = np.max(same_period_values)
                future_df.loc[i, f'{target_col}_max14'] = np.max(same_period_values)
                future_df.loc[i, f'{target_col}_max30'] = np.max(same_period_values)
                future_df.loc[i, f'{target_col}_diff1'] = 0  # Unknown
                future_df.loc[i, f'{target_col}_diff7'] = 0  # Unknown
                future_df.loc[i, f'{target_col}_ema7'] = climatological_value
                future_df.loc[i, f'{target_col}_ema30'] = climatological_value
                
                # Add temp_max and temp_min lag features (for temperature metric)
                if metric == 'temperature':
                    if not same_period_max_values:
                        raise ValueError(f"No temp_max data for date {future_date.strftime('%Y-%m-%d')}")
                    if not same_period_min_values:
                        raise ValueError(f"No temp_min data for date {future_date.strftime('%Y-%m-%d')}")
                    
                    climatological_max = np.mean(same_period_max_values)
                    for lag in lookback_days:
                        future_df.loc[i, f'temp_max_lag{lag}'] = climatological_max
                    
                    # Rolling statistics for temp_max
                    future_df.loc[i, 'temp_max_ma7'] = climatological_max
                    future_df.loc[i, 'temp_max_ma14'] = climatological_max
                    future_df.loc[i, 'temp_max_ma30'] = climatological_max
                    future_df.loc[i, 'temp_max_std7'] = np.std(same_period_max_values) if len(same_period_max_values) > 1 else 0
                    future_df.loc[i, 'temp_max_std14'] = np.std(same_period_max_values) if len(same_period_max_values) > 1 else 0
                    future_df.loc[i, 'temp_max_std30'] = np.std(same_period_max_values) if len(same_period_max_values) > 1 else 0
                    
                    climatological_min = np.mean(same_period_min_values)
                    for lag in lookback_days:
                        future_df.loc[i, f'temp_min_lag{lag}'] = climatological_min
                    
                    # Rolling statistics for temp_min
                    future_df.loc[i, 'temp_min_ma7'] = climatological_min
                    future_df.loc[i, 'temp_min_ma14'] = climatological_min
                    future_df.loc[i, 'temp_min_ma30'] = climatological_min
                    future_df.loc[i, 'temp_min_std7'] = np.std(same_period_min_values) if len(same_period_min_values) > 1 else 0
                    future_df.loc[i, 'temp_min_std14'] = np.std(same_period_min_values) if len(same_period_min_values) > 1 else 0
                    future_df.loc[i, 'temp_min_std30'] = np.std(same_period_min_values) if len(same_period_min_values) > 1 else 0
            else:
                # フォールバック禁止 - データがない場合はエラー
                raise ValueError(
                    f"No historical data found for date {future_date.strftime('%Y-%m-%d')} (month-day: {month_day}). "
                    f"Metric: {metric}, same_period_values: {len(same_period_values)} samples. "
                    f"Need at least 1 historical sample for climatological prediction."
                )
        
        # Cross-metric features
        if metric == 'temperature' and 'temp_range' in historical_features.columns:
            # Use historical mean range for this season
            for i, future_date in enumerate(future_dates):
                month = future_date.month
                historical_month_data = historical_features[historical_features['month'] == month]
                if len(historical_month_data) > 0:
                    future_df.loc[i, 'temp_range'] = historical_month_data['temp_range'].mean()
                else:
                    future_df.loc[i, 'temp_range'] = historical_features['temp_range'].iloc[-1]
            
            if 'has_precipitation' in historical_features.columns:
                future_df['has_precipitation'] = 0  # Unknown
                future_df['precip_rolling7'] = 0  # Unknown
        
        # Fill any remaining NaN
        future_df = future_df.ffill().bfill().fillna(0)
        
        return future_df
    
    @staticmethod
    def _get_target_column(metric: str) -> str:
        """Get target column name for metric."""
        metric_mapping = {
            'temperature': 'temperature',
            'temperature_max': 'temp_max',
            'temperature_min': 'temp_min',
            'precipitation': 'precipitation',
            'sunshine': 'sunshine',
        }
        return metric_mapping.get(metric, metric)
    
    @staticmethod
    def get_feature_names(metric: str, lookback_days: List[int] = None) -> List[str]:
        """
        Get list of feature names for model training.
        
        Args:
            metric: Metric being predicted
            lookback_days: List of lookback periods
            
        Returns:
            List of feature names (excluding target and date)
        """
        if lookback_days is None:
            lookback_days = [1, 7, 14, 30]
        
        target_col = FeatureEngineeringService._get_target_column(metric)
        
        features = [
            # Temporal
            'year', 'month', 'day', 'day_of_year', 'day_of_week', 'week_of_year', 'is_weekend',
            'month_sin', 'month_cos', 'day_of_year_sin', 'day_of_year_cos',
            'is_winter', 'is_spring', 'is_summer', 'is_autumn',
        ]
        
        # Lag features
        for lag in lookback_days:
            features.append(f'{target_col}_lag{lag}')
        
        # Rolling statistics
        for window in [7, 14, 30]:
            features.extend([
                f'{target_col}_ma{window}',
                f'{target_col}_std{window}',
                f'{target_col}_min{window}',
                f'{target_col}_max{window}',
            ])
        
        # Difference features
        features.extend([
            f'{target_col}_diff1',
            f'{target_col}_diff7',
        ])
        
        # EMA features
        features.extend([
            f'{target_col}_ema7',
            f'{target_col}_ema30',
        ])
        
        # Cross-metric features
        if metric == 'temperature':
            features.extend([
                'temp_range',
                'has_precipitation',
                'precip_rolling7',
            ])
            
            # Add temp_max and temp_min lag features
            for lag in lookback_days:
                features.extend([
                    f'temp_max_lag{lag}',
                    f'temp_min_lag{lag}',
                ])
            
            # Add temp_max and temp_min rolling statistics
            for window in [7, 14, 30]:
                features.extend([
                    f'temp_max_ma{window}',
                    f'temp_max_std{window}',
                    f'temp_min_ma{window}',
                    f'temp_min_std{window}',
                ])
        
        return features

