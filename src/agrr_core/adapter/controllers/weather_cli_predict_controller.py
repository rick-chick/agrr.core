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
            description="Weather Prediction CLI - Predict future weather using ARIMA time series model",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get historical data and predict 30 days ahead
  agrr weather --location 35.6762,139.6503 --days 90 --json > historical.json
  agrr predict --input historical.json --output predictions.json --days 30
  
  # Predict 14 days ahead from existing data
  agrr predict --input weather_data.json --output forecast.json --days 14
  
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
  1. Reads historical weather data from input file (minimum 30 days)
  2. Applies ARIMA time series model with automatic stationarity checking
  3. Generates predictions with 95% confidence intervals
  4. Saves predictions to output file

Model Details:
  - Algorithm: ARIMA (AutoRegressive Integrated Moving Average)
  - Includes seasonal components for annual patterns
  - Automatic fallback to simpler model if needed
  - Best for: 7-30 day predictions
  - Minimum data: 30 days (90+ days recommended for better accuracy)

Notes:
  - This is a statistical model, not real-time forecast
  - Accuracy decreases for longer prediction periods
  - Data quality significantly affects prediction accuracy
  - Currently predicts temperature (extensible to other metrics)
            """
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Predict command (renamed from predict-file)
        predict_parser = subparsers.add_parser(
            'predict', 
            help='Predict future weather using ARIMA model from historical data',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get historical data and predict 30 days ahead
  agrr weather --location 35.6762,139.6503 --days 90 --json > historical.json
  agrr predict --input historical.json --output predictions.json --days 30
  
  # Predict 14 days ahead from existing data
  agrr predict --input weather_data.json --output forecast.json --days 14

Input File Format (JSON):
  {
    "data": [
      {"time": "2024-10-01", "temperature_2m_max": 25.5, "temperature_2m_min": 15.2},
      // ... minimum 30 days (90+ days recommended)
    ]
  }

Output Format (JSON):
  {
    "predictions": [
      {
        "date": "2024-11-01",
        "predicted_value": 18.5,
        "confidence_lower": 16.2,
        "confidence_upper": 20.8
      }
    ],
    "model_type": "ARIMA"
  }

Model Details:
  - Algorithm: ARIMA (AutoRegressive Integrated Moving Average)
  - Seasonal patterns: Automatic detection and modeling
  - Confidence intervals: 95% prediction intervals
  - Best for: 7-30 day predictions
  - Minimum data: 30 days (90+ recommended)

Note: Statistical model based on historical patterns. Accuracy decreases for longer periods.
            """
        )
        
        # Input file argument (required)
        predict_parser.add_argument(
            '--input', '-i',
            required=True,
            help='Path to historical weather data file (JSON or CSV, minimum 30 days)'
        )
        
        # Output file argument (required)
        predict_parser.add_argument(
            '--output', '-o',
            required=True,
            help='Path to save prediction results (JSON or CSV format)'
        )
        
        # Prediction days argument
        predict_parser.add_argument(
            '--days', '-d',
            type=int,
            default=7,
            help='Number of days to predict into the future (default: 7, recommended: 7-30)'
        )
        
        
        return parser
    
    
    async def handle_predict_command(self, args) -> None:
        """Handle predict command execution."""
        try:
            # Execute prediction using use case interactor
            predictions = await self.predict_interactor.execute(
                input_source=args.input,
                output_destination=args.output,
                prediction_days=args.days
            )
            
            # Display success message
            self.cli_presenter.display_success_message(
                f"✓ Prediction completed successfully!\n"
                f"  Model: ARIMA time series\n"
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
        
        if not parsed_args.command:
            parser.print_help()
            return
        
        if parsed_args.command == 'predict':
            await self.handle_predict_command(parsed_args)
        else:
            parser.print_help()
