"""Weather prediction visualization service."""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    import pandas as pd
    import numpy as np
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

from agrr_core.entity import WeatherData, Forecast
from agrr_core.usecase.dto.advanced_prediction_response_dto import VisualizationDataDTO
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.forecast_response_dto import ForecastResponseDTO


class VisualizationService:
    """Service for creating weather prediction visualizations."""
    
    def __init__(self):
        self.default_style = 'seaborn-v0_8' if PLOTTING_AVAILABLE else None
    
    async def create_prediction_chart(
        self,
        historical_data: List[WeatherDataResponseDTO],
        forecasts: Dict[str, List[ForecastResponseDTO]],
        title: str = "Weather Prediction",
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a comprehensive prediction chart."""
        
        if not PLOTTING_AVAILABLE:
            return {
                'status': 'error',
                'message': 'Matplotlib not available. Please install matplotlib and seaborn.'
            }
        
        try:
            # Set up the plot style
            plt.style.use(self.default_style)
            fig, axes = plt.subplots(len(forecasts), 1, figsize=(12, 4 * len(forecasts)))
            
            if len(forecasts) == 1:
                axes = [axes]
            
            for idx, (metric, forecast_list) in enumerate(forecasts.items()):
                ax = axes[idx]
                
                # Prepare historical data
                hist_dates = [datetime.fromisoformat(d.time) for d in historical_data]
                hist_values = self._extract_metric_from_historical(historical_data, metric)
                
                # Prepare forecast data
                forecast_dates = [datetime.fromisoformat(f.date) for f in forecast_list]
                forecast_values = [f.predicted_value for f in forecast_list]
                
                # Plot historical data
                ax.plot(hist_dates, hist_values, 'b-', label='Historical Data', linewidth=2)
                
                # Plot forecasts
                ax.plot(forecast_dates, forecast_values, 'r--', label='Prediction', linewidth=2)
                
                # Plot confidence intervals if available
                confidence_lower = [f.confidence_lower for f in forecast_list if f.confidence_lower is not None]
                confidence_upper = [f.confidence_upper for f in forecast_list if f.confidence_upper is not None]
                
                if confidence_lower and confidence_upper:
                    ax.fill_between(
                        forecast_dates,
                        confidence_lower,
                        confidence_upper,
                        alpha=0.3,
                        color='red',
                        label='Confidence Interval'
                    )
                
                # Formatting
                ax.set_title(f'{metric.title()} Prediction')
                ax.set_xlabel('Date')
                ax.set_ylabel(self._get_metric_unit(metric))
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Format x-axis dates
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.suptitle(title, fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # Convert to base64 for web display
            import io
            import base64
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            plt.close()
            
            return {
                'status': 'success',
                'image_base64': image_base64,
                'save_path': save_path
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to create chart: {e}'
            }
    
    async def create_trend_analysis_chart(
        self,
        historical_data: List[WeatherDataResponseDTO],
        metric: str = 'temperature',
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create trend analysis chart."""
        
        if not PLOTTING_AVAILABLE:
            return {
                'status': 'error',
                'message': 'Matplotlib not available.'
            }
        
        try:
            # Prepare data
            dates = [datetime.fromisoformat(d.time) for d in historical_data]
            values = self._extract_metric_from_historical(historical_data, metric)
            
            # Create DataFrame for analysis
            df = pd.DataFrame({
                'date': dates,
                'value': values
            })
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Calculate moving averages
            df['ma_7'] = df['value'].rolling(window=7).mean()
            df['ma_30'] = df['value'].rolling(window=30).mean()
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot original data
            ax.plot(df.index, df['value'], alpha=0.7, label='Daily Values', color='lightblue')
            
            # Plot moving averages
            ax.plot(df.index, df['ma_7'], label='7-day Moving Average', color='blue', linewidth=2)
            ax.plot(df.index, df['ma_30'], label='30-day Moving Average', color='red', linewidth=2)
            
            # Formatting
            ax.set_title(f'{metric.title()} Trend Analysis')
            ax.set_xlabel('Date')
            ax.set_ylabel(self._get_metric_unit(metric))
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # Convert to base64
            import io
            import base64
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            plt.close()
            
            return {
                'status': 'success',
                'image_base64': image_base64,
                'save_path': save_path,
                'trend_data': {
                    'daily_avg': float(df['value'].mean()),
                    'trend_7d': float(df['ma_7'].iloc[-1]) if not pd.isna(df['ma_7'].iloc[-1]) else None,
                    'trend_30d': float(df['ma_30'].iloc[-1]) if not pd.isna(df['ma_30'].iloc[-1]) else None
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to create trend analysis: {e}'
            }
    
    async def create_model_comparison_chart(
        self,
        comparison_results: Dict[str, Any],
        metric: str = 'temperature',
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create model comparison chart."""
        
        if not PLOTTING_AVAILABLE:
            return {
                'status': 'error',
                'message': 'Matplotlib not available.'
            }
        
        try:
            # Extract accuracy metrics
            models = []
            mae_values = []
            rmse_values = []
            mape_values = []
            
            for model_name, result in comparison_results.items():
                if 'error' not in result and 'accuracy' in result:
                    if metric in result['accuracy']:
                        accuracy = result['accuracy'][metric]
                        models.append(model_name)
                        mae_values.append(accuracy.get('mae', 0))
                        rmse_values.append(accuracy.get('rmse', 0))
                        mape_values.append(accuracy.get('mape', 0))
            
            if not models:
                return {
                    'status': 'error',
                    'message': 'No valid comparison data found'
                }
            
            # Create comparison chart
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            metrics_data = [
                (mae_values, 'MAE', 'Mean Absolute Error'),
                (rmse_values, 'RMSE', 'Root Mean Squared Error'),
                (mape_values, 'MAPE', 'Mean Absolute Percentage Error (%)')
            ]
            
            for idx, (values, metric_name, title) in enumerate(metrics_data):
                ax = axes[idx]
                bars = ax.bar(models, values, color=plt.cm.Set3(np.linspace(0, 1, len(models))))
                ax.set_title(title)
                ax.set_ylabel(metric_name)
                
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:.2f}', ha='center', va='bottom')
                
                # Rotate x-axis labels if needed
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            plt.suptitle(f'Model Comparison - {metric.title()}', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            # Convert to base64
            import io
            import base64
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            plt.close()
            
            return {
                'status': 'success',
                'image_base64': image_base64,
                'save_path': save_path,
                'comparison_summary': {
                    'best_mae_model': models[np.argmin(mae_values)],
                    'best_rmse_model': models[np.argmin(rmse_values)],
                    'best_mape_model': models[np.argmin(mape_values)]
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to create comparison chart: {e}'
            }
    
    def _extract_metric_from_historical(
        self, 
        historical_data: List[WeatherDataResponseDTO], 
        metric: str
    ) -> List[float]:
        """Extract metric values from historical data."""
        values = []
        
        for data in historical_data:
            if metric == 'temperature':
                if data.temperature_2m_mean is not None:
                    values.append(data.temperature_2m_mean)
            elif metric == 'precipitation':
                if data.precipitation_sum is not None:
                    values.append(data.precipitation_sum)
            elif metric == 'sunshine':
                if data.sunshine_duration is not None:
                    values.append(data.sunshine_duration)
        
        return values
    
    def _get_metric_unit(self, metric: str) -> str:
        """Get unit for metric."""
        units = {
            'temperature': 'Temperature (°C)',
            'precipitation': 'Precipitation (mm)',
            'sunshine': 'Sunshine Duration (hours)',
            'humidity': 'Humidity (%)',
            'pressure': 'Pressure (hPa)',
            'wind_speed': 'Wind Speed (m/s)'
        }
        return units.get(metric, metric.title())
    
    async def create_visualization_data(
        self,
        historical_data: List[WeatherDataResponseDTO],
        forecasts: Dict[str, List[ForecastResponseDTO]]
    ) -> VisualizationDataDTO:
        """Create comprehensive visualization data."""
        
        # Calculate confidence intervals
        confidence_intervals = {}
        for metric, forecast_list in forecasts.items():
            confidence_data = []
            for forecast in forecast_list:
                if forecast.confidence_lower is not None and forecast.confidence_upper is not None:
                    confidence_data.append({
                        'date': forecast.date,
                        'lower': forecast.confidence_lower,
                        'upper': forecast.confidence_upper
                    })
            confidence_intervals[metric] = confidence_data
        
        # Perform trend analysis
        trend_analysis = {}
        for metric in forecasts.keys():
            trend_result = await self.create_trend_analysis_chart(
                historical_data, metric
            )
            if trend_result['status'] == 'success':
                trend_analysis[metric] = trend_result.get('trend_data', {})
        
        return VisualizationDataDTO(
            historical_data=historical_data,
            forecasts=forecasts,
            confidence_intervals=confidence_intervals,
            trend_analysis=trend_analysis,
            seasonality_analysis=None  # Could be implemented later
        )
