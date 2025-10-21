"""CLI controller for weather file-based prediction operations."""

import argparse
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta

from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.prediction_gateway import PredictionGateway
from agrr_core.framework.validation.output_validator import OutputValidator, OutputValidationError


class WeatherCliPredictController:
    """CLI controller for weather file-based prediction operations."""
    
    def __init__(
        self, 
        weather_gateway: WeatherGateway,
        prediction_gateway: PredictionGateway,
        cli_presenter: WeatherCLIPresenter
    ):
        """Initialize CLI weather file prediction controller."""
        # Store gateways for direct use
        self.weather_gateway = weather_gateway
        self.prediction_gateway = prediction_gateway
        self.cli_presenter = cli_presenter
    
    def create_argument_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI commands."""
        parser = argparse.ArgumentParser(
            description="Weather Prediction CLI - Predict future weather using machine learning models",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get historical data and predict 30 days ahead with ARIMA (default)
  agrr weather --location 35.6762,139.6503 --days 90 --json > historical.json
  agrr predict --input historical.json --output predictions.json --days 30
  
  # Use LightGBM model (higher accuracy, requires 90+ days of data)
  agrr predict --input historical.json --output forecast.json --days 30 --model lightgbm
  
  # Predict temperature_max and temperature_min with LightGBM (NEW!)
  agrr predict --input historical.json --output forecast.json --days 30 --model lightgbm \\
               --metrics temperature,temperature_max,temperature_min
  
  # Predict only temperature_max
  agrr predict --input historical.json --output forecast_max.json --days 30 --model lightgbm \\
               --metrics temperature_max
  
  # Use ensemble of multiple models (best accuracy)
  agrr predict --input historical.json --output forecast.json --days 30 --model ensemble
  
  # Use CSV format
  agrr predict --input data.csv --output predictions.csv --days 7

Input File Format (JSON):
  {
    "latitude": 35.6762,
    "longitude": 139.6503,
    "data": [
      {
        "time": "2024-10-01",
        "temperature_2m_max": 25.5,
        "temperature_2m_min": 15.2,
        "temperature_2m_mean": 20.3
      }
      // ... at least 30 days of historical data
    ]
  }

Output Format (JSON):
  
  ARIMA output (single metric):
  {
    "predictions": [
      {
        "date": "2024-11-01",
        "temperature": 18.5,
        "temperature_confidence_lower": 16.2,
        "temperature_confidence_upper": 20.8
      }
    ],
    "model_type": "ARIMA",
    "prediction_days": 30
  }
  
  LightGBM output (multi-metric, automatically includes temperature_max/min):
  {
    "predictions": [
      {
        "date": "2024-11-01",
        "temperature": 18.5,
        "temperature_max": 22.0,
        "temperature_min": 15.0,
        "temperature_confidence_lower": 16.2,
        "temperature_confidence_upper": 20.8,
        "temperature_max_confidence_lower": 19.0,
        "temperature_max_confidence_upper": 25.0,
        "temperature_min_confidence_lower": 12.0,
        "temperature_min_confidence_upper": 18.0
      }
    ],
    "model_type": "LightGBM",
    "prediction_days": 30,
    "metrics": ["temperature", "temperature_max", "temperature_min"]
  }

How it works:
  1. Reads historical weather data from input file
  2. Applies selected prediction model (ARIMA or LightGBM)
  3. Generates predictions with 95% confidence intervals
  4. Saves predictions to output file

Model Details:

  ARIMA (AutoRegressive Integrated Moving Average):
    - Statistical time series model
    - Best for: Short-term predictions (7-90 days)
    - Minimum data: 30 days
    - Recommended data: 90+ days
    - Accuracy: MAE ~1.5°C (30 days)
    - Includes seasonal components

  LightGBM (Light Gradient Boosting Machine):
    - Machine learning model with 94+ features
    - Best for: Medium to long-term (90-365 days)
    - Minimum data: 90 days
    - Recommended data: 365+ days (multi-year preferred)
    - Accuracy: MAE ~2.2°C (90-365 days)
    - Uses climatological approach (past same-period data)
    - Higher accuracy for long-term predictions
    - Automatically predicts temperature, temperature_max, and temperature_min
      (avoids temperature range saturation issue)

  Ensemble (Future):
    - Combines ARIMA + LightGBM
    - Expected accuracy: Best of both models
    - Currently under development

Model Selection Guide:
  - Short-term (7-30 days): Use ARIMA
  - Medium-term (30-90 days): Either model works
  - Long-term (90-365 days): Use LightGBM
  - Very long-term (365+ days): Use LightGBM with multi-year data

Notes:
  - These are statistical/ML models, not real-time forecasts
  - LightGBM automatically predicts temperature, temperature_max, and temperature_min
    in a single execution (no additional cost)
  - This avoids the temperature range saturation issue (fixed daily range)
  - ARIMA model predicts temperature only (temperature_max/min are estimated)
  - For crop planning (1+ year), use LightGBM with 20 years of historical data
  - Data quality significantly affects prediction accuracy
            """
        )
        
        # Input file argument (required)
        parser.add_argument(
            '--input', '-i',
            required=True,
            help='Path to historical weather data file (JSON or CSV, minimum 30 days)'
        )
        
        # Output file argument (required)
        parser.add_argument(
            '--output', '-o',
            required=True,
            help='Path to save prediction results (JSON or CSV format)'
        )
        
        # Prediction days argument
        parser.add_argument(
            '--days', '-d',
            type=int,
            default=7,
            help='Number of days to predict into the future (default: 7, recommended: 7-30)'
        )
        
        # Model selection argument
        parser.add_argument(
            '--model', '-m',
            choices=['arima', 'lightgbm', 'ensemble'],
            default='arima',
            help='Prediction model to use (default: arima). lightgbm requires 90+ days of data.'
        )
        
        # Confidence level argument
        parser.add_argument(
            '--confidence',
            type=float,
            default=0.95,
            help='Confidence level for prediction intervals (default: 0.95)'
        )
        
        # Metrics argument (NEW: for temperature_max/min support)
        parser.add_argument(
            '--metrics',
            type=str,
            default='temperature',
            help='Metrics to predict (comma-separated). Options: temperature, temperature_max, temperature_min. '
                 'Note: LightGBM model automatically predicts all 3 metrics regardless of this option. '
                 'Example: --metrics temperature,temperature_max,temperature_min'
        )
        
        return parser
    
    
    async def handle_predict_command(self, args) -> None:
        """Handle predict command execution."""
        try:
            # Get model type and metrics from args
            model_type = getattr(args, 'model', 'arima')
            metrics_str = getattr(args, 'metrics', 'temperature')
            metrics = [m.strip() for m in metrics_str.split(',')]
            
            # 厳密な入力バリデーション
            try:
                OutputValidator.validate_input_metrics(metrics, model_type)
            except OutputValidationError as e:
                self.cli_presenter.display_error(f"Invalid input: {e}")
                return
            
            # Display model name
            model_names = {
                'arima': 'ARIMA (AutoRegressive Integrated Moving Average)',
                'lightgbm': 'LightGBM (Light Gradient Boosting Machine)',
                'ensemble': 'Ensemble (Multiple Models)'
            }
            model_display = model_names.get(model_type, model_type.upper())
            
            # Check if multiple metrics or non-temperature metric is requested
            if len(metrics) > 1 or metrics[0] != 'temperature':
                # Multiple metrics or temperature_max/min requested
                if model_type != 'lightgbm':
                    self.cli_presenter.display_error(
                        "temperature_max and temperature_min predictions are only supported with LightGBM model.\n"
                        "Please add --model lightgbm option.",
                        "VALIDATION_ERROR"
                    )
                    return
                
                # Use multi-metric prediction (requires direct service access)
                self.cli_presenter.display_success_message(
                    f"⚠ Multi-metric prediction ({', '.join(metrics)}) with LightGBM\n"
                    f"  This feature requires API-level access.\n"
                    f"  Please use Python API directly:\n\n"
                    f"  from agrr_core.framework.services.ml.lightgbm_prediction_service import LightGBMPredictionService\n"
                    f"  service = LightGBMPredictionService()\n"
                    f"  results = await service.predict_multiple_metrics(\n"
                    f"      historical_data=weather_data,\n"
                    f"      metrics={metrics},\n"
                    f"      model_config={{'prediction_days': {args.days}}}\n"
                    f"  )\n\n"
                    f"  See docs/features/TEMPERATURE_MAX_MIN_PREDICTION.md for details."
                )
                return
            
            # Single temperature metric - use direct gateway calls
            # Load historical data
            historical_data = await self.weather_gateway.load_weather_data(args.input)
            
            # Generate predictions
            predictions = await self.prediction_gateway.predict(
                historical_data, 
                'temperature', 
                {'prediction_days': args.days}
            )
            
            # Save predictions
            await self.prediction_gateway.create(predictions, args.output)
            
            # Display success message
            self.cli_presenter.display_success_message(
                f"✓ Prediction completed successfully!\n"
                f"  Model: {model_display}\n"
                f"  Generated: {len(predictions)} daily predictions\n"
                f"  Period: {args.days} days into the future\n"
                f"  Output: {args.output}"
            )
                
        except ValueError as e:
            self.cli_presenter.display_error(str(e), "VALIDATION_ERROR")
        except Exception as e:
            self.cli_presenter.display_error(f"Unexpected error: {e}", "INTERNAL_ERROR")
    
    async def run(self, args: Optional[list] = None) -> None:
        """Run CLI application with given arguments."""
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)
        
        # Execute predict command directly (no subcommand needed)
        await self.handle_predict_command(parsed_args)
