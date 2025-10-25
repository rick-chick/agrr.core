"""CLI weather controller for adapter layer."""

import argparse
import asyncio
from typing import Optional, Tuple
from datetime import datetime, timedelta

from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.usecase.interactors.weather_fetch_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.interactors.weather_get_forecast_interactor import WeatherGetForecastInteractor
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.usecase.dto.weather_forecast_request_dto import WeatherForecastRequestDTO


class WeatherCliFetchController:
    """CLI controller for weather data fetch operations."""
    
    def __init__(
        self, 
        weather_gateway: WeatherGateway,
        cli_presenter: WeatherCLIPresenter
    ):
        """Initialize CLI weather controller."""
        self.weather_gateway = weather_gateway
        self.cli_presenter = cli_presenter
        # Interactorをインスタンス化
        self.weather_interactor = FetchWeatherDataInteractor(
            weather_gateway=self.weather_gateway,
            weather_presenter_output_port=self.cli_presenter
        )
        self.forecast_interactor = WeatherGetForecastInteractor(
            weather_gateway=self.weather_gateway,
            weather_presenter_output_port=self.cli_presenter
        )
    
    def create_argument_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI commands."""
        parser = argparse.ArgumentParser(
            description="Weather Forecast CLI - Get weather data from Open-Meteo or JMA",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get historical weather for Tokyo for the last 7 days (ending yesterday)
  agrr weather --location 35.6762,139.6503 --days 7
  
  # Get weather from JMA (Japan Meteorological Agency) for Tokyo
  agrr weather --location 35.6762,139.6503 --days 7 --data-source jma
  
  # Get India weather from NOAA ISD (49 agricultural region stations, 2000+)
  agrr weather --location 28.5844,77.2031 --start-date 2023-01-01 --end-date 2023-12-31 --data-source noaa --json
  
  # Get long-term historical data from NOAA FTP (US 2000+)
  agrr weather --location 40.7128,-74.0060 --start-date 2000-01-01 --end-date 2023-12-31 --data-source noaa-ftp
  
  # Get weather for specific historical date range
  agrr weather --location 35.6762,139.6503 --start-date 2024-01-01 --end-date 2024-01-07
  
  # Get historical weather for New York with JSON output (save to file)
  agrr weather --location 40.7128,-74.0060 --days 5 --json > weather.json
  
  # Get 16-day forecast from tomorrow
  agrr forecast --location 35.6762,139.6503

Major Cities Coordinates:
  Tokyo:       35.6762,139.6503
  Osaka:       34.6937,135.5023
  New York:    40.7128,-74.0060
  London:      51.5074,-0.1278
  
  # India (NOAA ISD - 49 agricultural stations)
  Delhi:       28.5844,77.2031    (NCR)
  Mumbai:      19.0896,72.8681    (Maharashtra)
  Bangalore:   12.9500,77.6681    (Karnataka)
  Chennai:     12.9900,80.1692    (Tamil Nadu)
  Kolkata:     22.6544,88.4467    (West Bengal)
  Ludhiana:    30.9000,75.8500    (Punjab - wheat belt)
  Lucknow:     26.7600,80.8800    (Uttar Pradesh)
  Pune:        18.5800,73.9200    (Maharashtra)

JSON Output Format:
  {
    "data": [
      {
        "time": "2024-05-01",
        "temperature_2m_max": 25.5,
        "temperature_2m_min": 15.2,
        "temperature_2m_mean": 20.3,
        "precipitation_sum": 0.0,
        "sunshine_duration": 28800.0,
        "sunshine_hours": 8.0
      }
    ],
    "total_count": 7,
    "location": {
      "latitude": 35.6762,
      "longitude": 139.6503,
      "elevation": 40.0,
      "timezone": "Asia/Tokyo"
    }
  }
            """
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Weather command
        weather_parser = subparsers.add_parser(
            'weather', 
            help='Get historical weather data',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get historical weather for Tokyo for the last 7 days
  agrr weather --location 35.6762,139.6503 --days 7
  
  # Get India weather from NOAA ISD (49 agricultural stations)
  agrr weather --location 28.5844,77.2031 --start-date 2023-01-01 --end-date 2023-12-31 --data-source noaa --json
  
  # Get weather for specific date range
  agrr weather --location 35.6762,139.6503 --start-date 2024-01-01 --end-date 2024-01-07
  
  # Save weather data to file (JSON format)
  agrr weather --location 40.7128,-74.0060 --days 5 --json > weather.json

Major Cities:
  Tokyo:       35.6762,139.6503
  Osaka:       34.6937,135.5023
  New York:    40.7128,-74.0060
  
  # India (NOAA ISD - 49 agricultural stations)
  Delhi:       28.5844,77.2031
  Mumbai:      19.0896,72.8681
  Bangalore:   12.9500,77.6681
  Ludhiana:    30.9000,75.8500  (Punjab wheat belt)

Output (JSON):
  {
    "data": [
      {
        "time": "2024-05-01",
        "temperature_2m_max": 25.5,
        "temperature_2m_min": 15.2,
        "temperature_2m_mean": 20.3,
        "precipitation_sum": 0.0,
        "sunshine_duration": 28800.0
      }
    ],
    "location": {
      "latitude": 35.6762,
      "longitude": 139.6503
    }
  }
            """
        )
        
        # Location argument (required)
        weather_parser.add_argument(
            '--location', '-l',
            required=True,
            help='Location coordinates as "latitude,longitude" (e.g., "35.6762,139.6503" for Tokyo)'
        )
        
        # Data source selection
        weather_parser.add_argument(
            '--data-source',
            choices=['openmeteo', 'jma', 'noaa', 'noaa-ftp', 'nasa-power'],
            default='openmeteo',
            help='Weather data source: openmeteo (global, default), jma (Japan only), noaa (US + India 66 stations, 2000+), noaa-ftp (US long-term FTP 2000+), or nasa-power (global grid-based)'
        )
        
        # Date range arguments
        weather_parser.add_argument(
            '--start-date', '-s',
            help='Start date in YYYY-MM-DD format'
        )
        
        weather_parser.add_argument(
            '--end-date', '-e',
            help='End date in YYYY-MM-DD format'
        )
        
        weather_parser.add_argument(
            '--days', '-d',
            type=int,
            default=7,
            help='Number of days of historical data ending yesterday (default: 7, ignored if start-date or end-date is specified)'
        )
        
        # Output format
        weather_parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        
        weather_parser.add_argument(
            '--output', '-o',
            help='Output file path (optional)'
        )
        
        # Forecast command (16-day forecast from tomorrow)
        forecast_parser = subparsers.add_parser(
            'forecast', 
            help='Get 16-day weather forecast starting from tomorrow',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Get 16-day forecast for Tokyo
  agrr forecast --location 35.6762,139.6503
  
  # Get forecast with JSON output (save to file)
  agrr forecast --location 35.6762,139.6503 --json > forecast.json
  
  # Get forecast for New York
  agrr forecast --location 40.7128,-74.0060

Major Cities:
  Tokyo:     35.6762,139.6503
  Osaka:     34.6937,135.5023
  New York:  40.7128,-74.0060
  London:    51.5074,-0.1278

Note: Forecast data starts from tomorrow and extends 16 days into the future.
      This is useful for planning future cultivation activities.
            """
        )
        
        # Location argument (required)
        forecast_parser.add_argument(
            '--location', '-l',
            required=True,
            help='Location coordinates as "latitude,longitude" (e.g., "35.6762,139.6503" for Tokyo)'
        )
        
        # Output format
        forecast_parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        
        forecast_parser.add_argument(
            '--output', '-o',
            help='Output file path (optional)'
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
        """Calculate start and end date based on number of days of historical data.
        
        Returns date range ending yesterday (not including today), since the archive API
        only supports historical data.
        """
        end_date = datetime.now().date() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days-1)
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    async def handle_weather_command(self, args) -> None:
        """Handle weather command execution."""
        try:
            # Parse location
            latitude, longitude = self.parse_location(args.location)
            
            # Validate days parameter if using --days
            if not args.start_date and not args.end_date:
                if args.days < 2:
                    raise ValueError("Minimum 2 days required for weather data. Use --days 2 or more, or specify --start-date and --end-date")
            
            # Determine date range
            if args.start_date and args.end_date:
                start_date = self.parse_date(args.start_date)
                end_date = self.parse_date(args.end_date)
            elif args.start_date:
                start_date = self.parse_date(args.start_date)
                end_date = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')  # Yesterday
            elif args.end_date:
                end_date = self.parse_date(args.end_date)
                start_date = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(days=args.days-1)).strftime('%Y-%m-%d')
            else:
                start_date, end_date = self.calculate_date_range(args.days)
            
            # Check if we should split by year (for long-term data)
            data_source = getattr(args, 'data_source', 'openmeteo')
            json_output = getattr(args, 'json', False)
            output_file = getattr(args, 'output', None)
            
            if self._should_split_by_year(start_date, end_date, data_source):
                # Fetch data year by year (more reliable for long-term data)
                await self._fetch_by_year_chunks(
                    latitude, longitude, start_date, end_date, 
                    data_source, json_output, output_file
                )
                return
            
            # Normal single-request fetch
            # Create request DTO
            request = WeatherDataRequestDTO(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date
            )
            
            # Execute interactor
            json_output = getattr(args, 'json', False)
            output_file = getattr(args, 'output', None)
            
            # Remove debug message - it should not be displayed in CLI output
            # if not json_output:
            #     self.cli_presenter.display_success_message(
            #         f"Fetching weather data for location ({latitude}, {longitude}) "
            #         f"from {start_date} to {end_date}..."
            #     )
            
            # Execute interactor
            result = await self.weather_interactor.execute(request)
            
            # Display results based on interactor response
            if result.get('success', False):
                data = result.get('data', {})
                weather_data_list = data.get('data', [])
                total_count = data.get('total_count', 0)
                location_data = data.get('location')
                
                if total_count > 0:
                    # Create WeatherDataListResponseDTO for display
                    from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                    from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
                    from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
                    
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
                                sunshine_hours=item.get('sunshine_hours'),
                                wind_speed_10m=item.get('wind_speed_10m'),
                                weather_code=item.get('weather_code')
                            )
                            dto_list.append(dto)
                        else:
                            dto_list.append(item)
                    
                    # Convert location data to DTO if available
                    location_dto = None
                    if location_data:
                        location_dto = LocationResponseDTO(
                            latitude=location_data.get('latitude'),
                            longitude=location_data.get('longitude'),
                            elevation=location_data.get('elevation'),
                            timezone=location_data.get('timezone')
                        )
                    
                    weather_list_dto = WeatherDataListResponseDTO(
                        data=dto_list,
                        total_count=total_count,
                        location=location_dto
                    )
                    
                    # Display in appropriate format
                    if output_file:
                        if json_output:
                            self.cli_presenter.display_weather_data_to_file(weather_list_dto, output_file)
                        else:
                            self.cli_presenter.display_weather_data_table_to_file(weather_list_dto, output_file)
                    else:
                        if json_output:
                            self.cli_presenter.display_weather_data_json(weather_list_dto)
                        else:
                            self.cli_presenter.display_weather_data(weather_list_dto)
                else:
                    if json_output:
                        # Empty result as JSON
                        from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                        from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
                        
                        # Include location even for empty results
                        location_dto = None
                        if location_data:
                            location_dto = LocationResponseDTO(
                                latitude=location_data.get('latitude'),
                                longitude=location_data.get('longitude'),
                                elevation=location_data.get('elevation'),
                                timezone=location_data.get('timezone')
                            )
                        
                        empty_dto = WeatherDataListResponseDTO(
                            data=[], 
                            total_count=0,
                            location=location_dto
                        )
                        if output_file:
                            self.cli_presenter.display_weather_data_to_file(empty_dto, output_file)
                        else:
                            self.cli_presenter.display_weather_data_json(empty_dto)
                    else:
                        if output_file:
                            # Empty result to file
                            from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                            from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
                            
                            location_dto = None
                            if location_data:
                                location_dto = LocationResponseDTO(
                                    latitude=location_data.get('latitude'),
                                    longitude=location_data.get('longitude'),
                                    elevation=location_data.get('elevation'),
                                    timezone=location_data.get('timezone')
                                )
                            
                            empty_dto = WeatherDataListResponseDTO(
                                data=[], 
                                total_count=0,
                                location=location_dto
                            )
                            self.cli_presenter.display_weather_data_table_to_file(empty_dto, output_file)
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
    
    def _should_split_by_year(self, start_date: str, end_date: str, data_source: str) -> bool:
        """Determine if we should split the request by year.
        
        For NOAA FTP data source and date ranges spanning multiple years,
        it's more reliable to fetch year by year.
        """
        # Only split for NOAA FTP source
        if data_source != 'noaa-ftp':
            return False
        
        # Check if date range spans multiple years
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Split if more than 1 year
        days_diff = (end - start).days
        return days_diff > 365
    
    async def _fetch_by_year_chunks(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        data_source: str,
        json_output: bool,
        output_file: str = None
    ) -> None:
        """Fetch weather data year by year and merge.
        
        This is more reliable for long-term historical data.
        """
        import sys
        import json
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        all_weather_data = []
        failed_years = []
        
        # Display progress header (to stderr if JSON output)
        output_stream = sys.stderr if json_output else sys.stdout
        print(f"\n{'='*60}", file=output_stream)
        print(f"Fetching Long-Term Weather Data", file=output_stream)
        print(f"{'='*60}", file=output_stream)
        print(f"Location: {latitude}, {longitude}", file=output_stream)
        print(f"Period: {start_date} to {end_date}", file=output_stream)
        print(f"Data Source: {data_source}", file=output_stream)
        print(f"Mode: Year-by-year fetch (more reliable)", file=output_stream)
        print(f"{'='*60}\n", file=output_stream)
        
        # Fetch year by year
        current_year = start.year
        end_year = end.year
        
        while current_year <= end_year:
            # Determine date range for this year
            year_start = start.strftime('%Y-%m-%d') if current_year == start.year else f"{current_year}-01-01"
            year_end = end.strftime('%Y-%m-%d') if current_year == end.year else f"{current_year}-12-31"
            
            print(f"[{current_year}] Fetching data from {year_start} to {year_end}...", file=output_stream, flush=True)
            
            try:
                # Create request for this year
                request = WeatherDataRequestDTO(
                    latitude=latitude,
                    longitude=longitude,
                    start_date=year_start,
                    end_date=year_end
                )
                
                # Execute interactor
                result = await self.weather_interactor.execute(request)
                
                if result.get('success', False):
                    data = result.get('data', {})
                    weather_data_list = data.get('data', [])
                    
                    if weather_data_list:
                        all_weather_data.extend(weather_data_list)
                        print(f"[{current_year}] ✅ Success! Fetched {len(weather_data_list)} records", file=output_stream)
                    else:
                        failed_years.append(current_year)
                        print(f"[{current_year}] ⚠️  No data available", file=output_stream)
                else:
                    failed_years.append(current_year)
                    error_msg = result.get('error', 'Unknown error')
                    print(f"[{current_year}] ❌ Failed: {error_msg}", file=output_stream)
                    
            except Exception as e:
                failed_years.append(current_year)
                print(f"[{current_year}] ❌ Error: {str(e)}", file=output_stream)
            
            current_year += 1
        
        # Display summary
        print(f"\n{'='*60}", file=output_stream)
        print(f"Summary", file=output_stream)
        print(f"{'='*60}", file=output_stream)
        print(f"Total records: {len(all_weather_data)}", file=output_stream)
        print(f"Successful years: {end_year - start.year + 1 - len(failed_years)}", file=output_stream)
        if failed_years:
            print(f"Failed years: {failed_years}", file=output_stream)
        print(f"{'='*60}\n", file=output_stream)
        
        # Check if we got any data
        if not all_weather_data:
            self.cli_presenter.display_error(
                f"No weather data found for location ({latitude}, {longitude}) "
                f"from {start_date} to {end_date}"
            )
            sys.exit(1)
        
        # Sort by time
        all_weather_data.sort(key=lambda x: x['time'] if isinstance(x, dict) else x.time)
        
        # Display results
        if output_file:
            # File output
            from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
            from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
            from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
            
            # Convert dict data to DTOs
            dto_list = []
            for item in all_weather_data:
                if isinstance(item, dict):
                    dto = WeatherDataResponseDTO(
                        time=item.get('time', ''),
                        temperature_2m_max=item.get('temperature_2m_max'),
                        temperature_2m_min=item.get('temperature_2m_min'),
                        temperature_2m_mean=item.get('temperature_2m_mean'),
                        precipitation_sum=item.get('precipitation_sum'),
                        sunshine_duration=item.get('sunshine_duration'),
                        sunshine_hours=item.get('sunshine_hours'),
                        wind_speed_10m=item.get('wind_speed_10m'),
                        weather_code=item.get('weather_code')
                    )
                    dto_list.append(dto)
            
            location_dto = LocationResponseDTO(
                latitude=latitude,
                longitude=longitude,
                elevation=None,
                timezone=None
            )
            
            response_dto = WeatherDataListResponseDTO(
                data=dto_list,
                total_count=len(dto_list),
                location=location_dto
            )
            
            if json_output:
                self.cli_presenter.display_weather_data_to_file(response_dto, output_file)
            else:
                self.cli_presenter.display_weather_data_table_to_file(response_dto, output_file)
        else:
            if json_output:
                # JSON output
                output = {
                    'data': all_weather_data,
                    'total_count': len(all_weather_data),
                    'location': {
                        'latitude': latitude,
                        'longitude': longitude
                    }
                }
                print(json.dumps(output, indent=2))
            else:
                # Table output
                from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
                from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
                
                # Convert dict data to DTOs
                dto_list = []
                for item in all_weather_data:
                    if isinstance(item, dict):
                        dto = WeatherDataResponseDTO(
                            time=item.get('time', ''),
                            temperature_2m_max=item.get('temperature_2m_max'),
                            temperature_2m_min=item.get('temperature_2m_min'),
                            temperature_2m_mean=item.get('temperature_2m_mean'),
                            precipitation_sum=item.get('precipitation_sum'),
                            sunshine_duration=item.get('sunshine_duration'),
                            sunshine_hours=item.get('sunshine_hours'),
                            wind_speed_10m=item.get('wind_speed_10m'),
                            weather_code=item.get('weather_code')
                        )
                        dto_list.append(dto)
                
                location_dto = LocationResponseDTO(
                    latitude=latitude,
                    longitude=longitude,
                    elevation=None,
                    timezone=None
                )
                
                response_dto = WeatherDataListResponseDTO(
                    data=dto_list,
                    total_count=len(dto_list),
                    location=location_dto
                )
                
                self.cli_presenter.display_weather_data(response_dto)
    
    async def handle_forecast_command(self, args) -> None:
        """Handle forecast command execution."""
        try:
            # Parse location
            latitude, longitude = self.parse_location(args.location)
            
            # Create request DTO
            request = WeatherForecastRequestDTO(
                latitude=latitude,
                longitude=longitude
            )
            
            # Execute interactor
            json_output = getattr(args, 'json', False)
            output_file = getattr(args, 'output', None)
            
            # Execute interactor
            result = await self.forecast_interactor.execute(request)
            
            # Display results based on interactor response
            if result.get('success', False):
                data = result.get('data', {})
                weather_data_list = data.get('data', [])
                total_count = data.get('total_count', 0)
                location_data = data.get('location')
                
                if total_count > 0:
                    # Create WeatherDataListResponseDTO for display
                    from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                    from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
                    from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
                    
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
                                sunshine_hours=item.get('sunshine_hours'),
                                wind_speed_10m=item.get('wind_speed_10m'),
                                weather_code=item.get('weather_code')
                            )
                            dto_list.append(dto)
                        else:
                            dto_list.append(item)
                    
                    # Convert location data to DTO if available
                    location_dto = None
                    if location_data:
                        location_dto = LocationResponseDTO(
                            latitude=location_data.get('latitude'),
                            longitude=location_data.get('longitude'),
                            elevation=location_data.get('elevation'),
                            timezone=location_data.get('timezone')
                        )
                    
                    weather_list_dto = WeatherDataListResponseDTO(
                        data=dto_list,
                        total_count=total_count,
                        location=location_dto
                    )
                    
                    # Display in appropriate format
                    if output_file:
                        if json_output:
                            self.cli_presenter.display_weather_data_to_file(weather_list_dto, output_file)
                        else:
                            self.cli_presenter.display_weather_data_table_to_file(weather_list_dto, output_file)
                    else:
                        if json_output:
                            self.cli_presenter.display_weather_data_json(weather_list_dto)
                        else:
                            self.cli_presenter.display_weather_data(weather_list_dto)
                else:
                    if json_output:
                        # Empty result as JSON
                        from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                        from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
                        
                        # Include location even for empty results
                        location_dto = None
                        if location_data:
                            location_dto = LocationResponseDTO(
                                latitude=location_data.get('latitude'),
                                longitude=location_data.get('longitude'),
                                elevation=location_data.get('elevation'),
                                timezone=location_data.get('timezone')
                            )
                        
                        empty_dto = WeatherDataListResponseDTO(
                            data=[], 
                            total_count=0,
                            location=location_dto
                        )
                        if output_file:
                            self.cli_presenter.display_weather_data_to_file(empty_dto, output_file)
                        else:
                            self.cli_presenter.display_weather_data_json(empty_dto)
                    else:
                        if output_file:
                            # Empty result to file
                            from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
                            from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO
                            
                            location_dto = None
                            if location_data:
                                location_dto = LocationResponseDTO(
                                    latitude=location_data.get('latitude'),
                                    longitude=location_data.get('longitude'),
                                    elevation=location_data.get('elevation'),
                                    timezone=location_data.get('timezone')
                                )
                            
                            empty_dto = WeatherDataListResponseDTO(
                                data=[], 
                                total_count=0,
                                location=location_dto
                            )
                            self.cli_presenter.display_weather_data_table_to_file(empty_dto, output_file)
                        else:
                            self.cli_presenter.display_success_message("No forecast data available for the specified location.")
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
        elif parsed_args.command == 'forecast':
            await self.handle_forecast_command(parsed_args)
        else:
            parser.print_help()
