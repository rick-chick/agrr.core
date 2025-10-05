"""CLI controller for weather file-based prediction operations."""

import argparse
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta

from agrr_core.usecase.interactors.weather_predict_interactor import WeatherPredictInteractor
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter


class WeatherFilePredictCLIController:
    """CLI controller for weather file-based prediction operations."""
    
    def __init__(
        self, 
        predict_interactor: WeatherPredictInteractor,
        cli_presenter: WeatherCLIPresenter
    ):
        """Initialize CLI weather file prediction controller."""
        self.predict_interactor = predict_interactor
        self.cli_presenter = cli_presenter
    
    def create_argument_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI commands."""
        parser = argparse.ArgumentParser(
            description="Weather File-based Prediction CLI - Predict weather from file data",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Predict weather from JSON file for 30 days
  python -m agrr_core.cli predict-file --input weather_data.json --days 30 --output predictions.json
  
  
  
            """
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Predict-file command
        predict_parser = subparsers.add_parser('predict-file', help='Predict weather from file data')
        
        # Input file argument (required)
        predict_parser.add_argument(
            '--input', '-i',
            required=True,
            help='Input weather data file path (JSON or CSV format)'
        )
        
        # Output file argument (required)
        predict_parser.add_argument(
            '--output', '-o',
            required=True,
            help='Output prediction file path (JSON or CSV format)'
        )
        
        # Prediction days argument
        predict_parser.add_argument(
            '--days', '-d',
            type=int,
            default=7,
            help='Number of days to predict (default: 7)'
        )
        
        
        return parser
    
    
    async def handle_predict_file_command(self, args) -> None:
        """Handle predict-file command execution."""
        try:
            # Execute prediction using use case interactor
            predictions = await self.predict_interactor.execute(
                input_source=args.input,
                output_destination=args.output,
                prediction_days=args.days
            )
            
            # Display success message
            self.cli_presenter.display_success_message(
                f"Prediction completed successfully! Generated {len(predictions)} predictions for {args.days} days. Output saved to: {args.output}"
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
        
        if parsed_args.command == 'predict-file':
            await self.handle_predict_file_command(parsed_args)
        else:
            parser.print_help()
