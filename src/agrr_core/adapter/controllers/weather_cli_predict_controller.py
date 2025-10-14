"""CLI controller for weather file-based prediction operations."""

import argparse
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta

from agrr_core.usecase.interactors.weather_predict_interactor import WeatherPredictInteractor
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.prediction_gateway import PredictionGateway


class WeatherCliPredictController:
    """CLI controller for weather file-based prediction operations."""
    
    def __init__(
        self, 
        weather_gateway: WeatherGateway,
        prediction_gateway: PredictionGateway,
        cli_presenter: WeatherCLIPresenter
    ):
        """Initialize CLI weather file prediction controller."""
        # Instantiate interactor directly with injected dependencies
        self.predict_interactor = WeatherPredictInteractor(
            weather_gateway=weather_gateway,
            prediction_gateway=prediction_gateway
        )
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
  {
    "predictions": [
      {
        "date": "2024-11-01",
        "predicted_value": 18.5,
        "confidence_lower": 16.2,
        "confidence_upper": 20.8,
        "metric": "temperature"
      }
    ],
    "model_type": "ARIMA",
    "prediction_days": 30,
    "model_params": {
      "order": [1, 1, 1],
      "seasonal_order": [1, 1, 1, 12]
    }
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
    - Machine learning model with 50+ features
    - Best for: Medium to long-term (90-365 days)
    - Minimum data: 90 days
    - Recommended data: 365+ days (multi-year preferred)
    - Accuracy: MAE ~2.2°C (90-365 days)
    - Uses climatological approach (past same-period data)
    - Higher accuracy for long-term predictions

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
  - LightGBM uses historical climate patterns for long-term prediction
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
        
        return parser
    
    
    async def handle_predict_command(self, args) -> None:
        """Handle predict command execution."""
        try:
            # Get model type from args
            model_type = getattr(args, 'model', 'arima')
            
            # Display model name
            model_names = {
                'arima': 'ARIMA (AutoRegressive Integrated Moving Average)',
                'lightgbm': 'LightGBM (Light Gradient Boosting Machine)',
                'ensemble': 'Ensemble (Multiple Models)'
            }
            model_display = model_names.get(model_type, model_type.upper())
            
            # Execute prediction using use case interactor
            predictions = await self.predict_interactor.execute(
                input_source=args.input,
                output_destination=args.output,
                prediction_days=args.days
            )
            
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
