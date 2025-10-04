"""CLI weather controller for framework layer."""

import argparse
import asyncio
from typing import Optional, Tuple
from datetime import datetime, timedelta

from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.framework.presenters.cli_weather_presenter import CLIWeatherPresenter


class CLIWeatherController:
    """CLI controller for weather data operations."""
    
    def __init__(
        self, 
        fetch_weather_interactor: FetchWeatherDataInteractor,
        cli_presenter: CLIWeatherPresenter
    ):
        """Initialize CLI weather controller."""
        self.fetch_weather_interactor = fetch_weather_interactor
        self.cli_presenter = cli_presenter
    
    def create_argument_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI commands."""
        parser = argparse.ArgumentParser(
            description="Weather Forecast CLI - Get weather data from Open-Meteo",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get weather for Tokyo for the last 7 days
  python -m agrr_core.cli weather --location 35.6762,139.6503 --days 7
  
  # Get weather for specific date range
  python -m agrr_core.cli weather --location 35.6762,139.6503 --start-date 2024-01-01 --end-date 2024-01-07
  
  # Get weather for New York
  python -m agrr_core.cli weather --location 40.7128,-74.0060 --days 5
            """
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Weather command
        weather_parser = subparsers.add_parser('weather', help='Get weather forecast data')
        
        # Location argument (required)
        weather_parser.add_argument(
            '--location', '-l',
            required=True,
            help='Location coordinates as "latitude,longitude" (e.g., "35.6762,139.6503" for Tokyo)'
        )
        
        # Date range arguments (mutually exclusive with days)
        date_group = weather_parser.add_mutually_exclusive_group()
        
        date_group.add_argument(
            '--start-date', '-s',
            help='Start date in YYYY-MM-DD format'
        )
        
        date_group.add_argument(
            '--end-date', '-e',
            help='End date in YYYY-MM-DD format'
        )
        
        date_group.add_argument(
            '--days', '-d',
            type=int,
            default=7,
            help='Number of days from today (default: 7)'
        )
        
        # Output format
        weather_parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        
        return parser
    
    def parse_location(self, location_str: str) -> Tuple[float, float]:
        """Parse location string to latitude and longitude."""
        try:
            lat_str, lon_str = location_str.split(',')
            latitude = float(lat_str.strip())
            longitude = float(lon_str.strip())
            
            # Validate coordinate ranges
            if not (-90 <= latitude <= 90):
                raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")
            if not (-180 <= longitude <= 180):
                raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")
            
            return latitude, longitude
            
        except ValueError as e:
            if "not enough values to unpack" in str(e):
                raise ValueError(f"Invalid location format: '{location_str}'. Expected format: 'latitude,longitude'")
            elif "could not convert" in str(e):
                raise ValueError(f"Invalid location format: '{location_str}'. Expected format: 'latitude,longitude'")
            else:
                raise e
    
    def parse_date(self, date_str: str) -> str:
        """Parse date string to YYYY-MM-DD format."""
        try:
            # Try to parse the date to validate format
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Expected format: YYYY-MM-DD")
    
    def calculate_date_range(self, days: int) -> Tuple[str, str]:
        """Calculate start and end date based on number of days."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    async def handle_weather_command(self, args) -> None:
        """Handle weather command execution."""
        try:
            # Parse location
            latitude, longitude = self.parse_location(args.location)
            
            # Determine date range
            if args.start_date and args.end_date:
                start_date = self.parse_date(args.start_date)
                end_date = self.parse_date(args.end_date)
            elif args.start_date:
                start_date = self.parse_date(args.start_date)
                end_date = datetime.now().date().strftime('%Y-%m-%d')
            elif args.end_date:
                end_date = self.parse_date(args.end_date)
                start_date = (datetime.now().date() - timedelta(days=args.days-1)).strftime('%Y-%m-%d')
            else:
                start_date, end_date = self.calculate_date_range(args.days)
            
            # Create request DTO
            request = WeatherDataRequestDTO(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date
            )
            
            # Execute use case
            json_output = getattr(args, 'json', False)
            
            if not json_output:
                self.cli_presenter.display_success_message(
                    f"Fetching weather data for location ({latitude}, {longitude}) "
                    f"from {start_date} to {end_date}..."
                )
            
            result = await self.fetch_weather_interactor.execute(request)
            
            # Display results
            if result.get('success', False):
                data = result.get('data', {})
                weather_data_list = data.get('data', [])
                total_count = data.get('total_count', 0)
                
                if total_count > 0:
                    # Create WeatherDataListResponseDTO for display
                    from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                    from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
                    
                    # Convert dict data to DTOs
                    dto_list = []
                    for item in weather_data_list:
                        if isinstance(item, dict):
                            dto = WeatherDataResponseDTO(
                                time=item.get('time', ''),
                                temperature_2m_max=item.get('temperature_2m_max'),
                                temperature_2m_min=item.get('temperature_2m_min'),
                                temperature_2m_mean=item.get('temperature_2m_mean'),
                                precipitation_sum=item.get('precipitation_sum'),
                                sunshine_duration=item.get('sunshine_duration'),
                                sunshine_hours=item.get('sunshine_hours')
                            )
                            dto_list.append(dto)
                        else:
                            dto_list.append(item)
                    
                    weather_list_dto = WeatherDataListResponseDTO(
                        data=dto_list,
                        total_count=total_count
                    )
                    
                    # Display in appropriate format
                    if json_output:
                        self.cli_presenter.display_weather_data_json(weather_list_dto)
                    else:
                        self.cli_presenter.display_weather_data(weather_list_dto)
                else:
                    if json_output:
                        # Empty result as JSON
                        from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                        empty_dto = WeatherDataListResponseDTO(data=[], total_count=0)
                        self.cli_presenter.display_weather_data_json(empty_dto)
                    else:
                        self.cli_presenter.display_success_message("No weather data available for the specified criteria.")
            else:
                error_info = result.get('error', {})
                error_message = error_info.get('message', 'Unknown error occurred')
                error_code = error_info.get('code', 'UNKNOWN_ERROR')
                self.cli_presenter.display_error(error_message, error_code, json_output=json_output)
                
        except ValueError as e:
            json_output = getattr(args, 'json', False)
            self.cli_presenter.display_error(str(e), "VALIDATION_ERROR", json_output=json_output)
        except Exception as e:
            json_output = getattr(args, 'json', False)
            self.cli_presenter.display_error(f"Unexpected error: {e}", "INTERNAL_ERROR", json_output=json_output)
    
    async def run(self, args: Optional[list] = None) -> None:
        """Run CLI application with given arguments."""
        parser = self.create_argument_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return
        
        if parsed_args.command == 'weather':
            await self.handle_weather_command(parsed_args)
        else:
            parser.print_help()
