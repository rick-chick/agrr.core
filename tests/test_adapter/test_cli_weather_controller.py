"""Tests for CLI weather controller."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from agrr_core.adapter.controllers.cli_weather_controller import CLIWeatherController
from agrr_core.adapter.presenters.cli_weather_presenter import CLIWeatherPresenter
from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor


class TestCLIWeatherController:
    """Test cases for CLI weather controller."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_interactor = AsyncMock(spec=FetchWeatherDataInteractor)
        self.mock_presenter = MagicMock(spec=CLIWeatherPresenter)
        self.controller = CLIWeatherController(
            fetch_weather_interactor=self.mock_interactor,
            cli_presenter=self.mock_presenter
        )
    
    def test_parse_location_valid(self):
        """Test parsing valid location string."""
        lat, lon = self.controller.parse_location("35.6762,139.6503")
        
        assert lat == 35.6762
        assert lon == 139.6503
    
    def test_parse_location_invalid_format(self):
        """Test parsing invalid location format."""
        with pytest.raises(ValueError, match="Invalid location format"):
            self.controller.parse_location("35.6762")
        
        with pytest.raises(ValueError, match="Invalid location format"):
            self.controller.parse_location("invalid,format")
    
    def test_parse_location_invalid_coordinates(self):
        """Test parsing location with invalid coordinates."""
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            self.controller.parse_location("91.0,139.6503")
        
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            self.controller.parse_location("35.6762,181.0")
    
    def test_parse_date_valid(self):
        """Test parsing valid date string."""
        result = self.controller.parse_date("2024-01-15")
        assert result == "2024-01-15"
    
    def test_parse_date_invalid(self):
        """Test parsing invalid date string."""
        with pytest.raises(ValueError, match="Invalid date format"):
            self.controller.parse_date("2024/01/15")
        
        with pytest.raises(ValueError, match="Invalid date format"):
            self.controller.parse_date("invalid-date")
    
    def test_calculate_date_range(self):
        """Test calculating date range from days.
        
        Date range should end yesterday (not today) since archive API only supports historical data.
        """
        start_date, end_date = self.controller.calculate_date_range(7)
        
        # Calculate expected dates - ending yesterday, not today
        expected_end = datetime.now().date() - timedelta(days=1)
        expected_start = expected_end - timedelta(days=6)
        
        assert start_date == expected_start.strftime('%Y-%m-%d')
        assert end_date == expected_end.strftime('%Y-%m-%d')
    
    def test_calculate_date_range_single_day(self):
        """Test calculating date range for a single day."""
        start_date, end_date = self.controller.calculate_date_range(1)
        
        # For 1 day, start and end should be the same (yesterday)
        expected_date = datetime.now().date() - timedelta(days=1)
        
        assert start_date == expected_date.strftime('%Y-%m-%d')
        assert end_date == expected_date.strftime('%Y-%m-%d')
    
    def test_calculate_date_range_three_days(self):
        """Test calculating date range for three days."""
        start_date, end_date = self.controller.calculate_date_range(3)
        
        # Calculate expected dates
        expected_end = datetime.now().date() - timedelta(days=1)  # Yesterday
        expected_start = expected_end - timedelta(days=2)  # 3 days ago
        
        assert start_date == expected_start.strftime('%Y-%m-%d')
        assert end_date == expected_end.strftime('%Y-%m-%d')
    
    def test_create_argument_parser(self):
        """Test creating argument parser."""
        parser = self.controller.create_argument_parser()
        
        # Test main help text
        help_text = parser.format_help()
        assert "Weather Forecast CLI" in help_text
        assert "weather" in help_text
        
        # Test weather subcommand help text
        # Parse with 'weather --help' to get subcommand help
        import sys
        from io import StringIO
        
        # Capture the help output for weather subcommand
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            parser.parse_args(['weather', '--help'])
        except SystemExit:
            # argparse exits after printing help
            pass
        
        weather_help = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        assert "--location" in weather_help
        assert "--json" in weather_help
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_success(self):
        """Test handling weather command successfully."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = False
        
        # Mock interactor response with location
        mock_response = {
            "success": True,
            "data": {
                "data": [
                    {
                        "time": "2024-01-15T00:00:00Z",
                        "temperature_2m_max": 15.5,
                        "temperature_2m_min": 8.2,
                        "temperature_2m_mean": 11.8,
                        "precipitation_sum": 5.0,
                        "sunshine_duration": 28800.0,
                        "sunshine_hours": 8.0
                    }
                ],
                "total_count": 1,
                "location": {
                    "latitude": 35.6762,
                    "longitude": 139.6503,
                    "elevation": 37.0,
                    "timezone": "Asia/Tokyo"
                }
            }
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called
        self.mock_interactor.execute.assert_called_once()
        
        # Verify presenter methods were called
        self.mock_presenter.display_success_message.assert_called()
        self.mock_presenter.display_weather_data.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_with_date_range(self):
        """Test handling weather command with specific date range."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = "2024-01-01"
        args.end_date = "2024-01-07"
        args.days = 7
        args.json = False
        
        # Mock interactor response
        mock_response = {
            "success": True,
            "data": {"data": [], "total_count": 0}
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called with correct dates
        call_args = self.mock_interactor.execute.call_args[0][0]
        assert call_args.latitude == 35.6762
        assert call_args.longitude == 139.6503
        assert call_args.start_date == "2024-01-01"
        assert call_args.end_date == "2024-01-07"
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_with_start_date_only(self):
        """Test handling weather command with only start date specified.
        
        When only start_date is specified, end_date should default to yesterday.
        """
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = "2024-01-01"
        args.end_date = None
        args.days = 7
        args.json = False
        
        # Mock interactor response
        mock_response = {
            "success": True,
            "data": {"data": [], "total_count": 0}
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called with correct dates
        call_args = self.mock_interactor.execute.call_args[0][0]
        expected_end_date = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        assert call_args.start_date == "2024-01-01"
        assert call_args.end_date == expected_end_date
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_with_end_date_only(self):
        """Test handling weather command with only end date specified.
        
        When only end_date is specified, start_date is calculated based on days parameter.
        """
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = "2024-01-07"
        args.days = 3
        args.json = False
        
        # Mock interactor response
        mock_response = {
            "success": True,
            "data": {"data": [], "total_count": 0}
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called with correct dates
        call_args = self.mock_interactor.execute.call_args[0][0]
        expected_start_date = "2024-01-05"  # 3 days before 2024-01-07
        
        assert call_args.start_date == expected_start_date
        assert call_args.end_date == "2024-01-07"
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_success_json_output(self):
        """Test handling weather command successfully with JSON output."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = True
        
        # Mock interactor response with location
        mock_response = {
            "success": True,
            "data": {
                "data": [
                    {
                        "time": "2024-01-15T00:00:00Z",
                        "temperature_2m_max": 15.5,
                        "temperature_2m_min": 8.2,
                        "temperature_2m_mean": 11.8,
                        "precipitation_sum": 5.0,
                        "sunshine_duration": 28800.0,
                        "sunshine_hours": 8.0
                    }
                ],
                "total_count": 1,
                "location": {
                    "latitude": 35.6762,
                    "longitude": 139.6503,
                    "elevation": 37.0,
                    "timezone": "Asia/Tokyo"
                }
            }
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called
        self.mock_interactor.execute.assert_called_once()
        
        # Verify JSON display method was called
        self.mock_presenter.display_weather_data_json.assert_called()
        # Success message should not be displayed for JSON output
        self.mock_presenter.display_success_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_empty_data_json_output(self):
        """Test handling weather command with empty data and JSON output."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = True
        
        # Mock interactor response with empty data but including location
        mock_response = {
            "success": True,
            "data": {
                "data": [],
                "total_count": 0,
                "location": {
                    "latitude": 35.6762,
                    "longitude": 139.6503,
                    "elevation": 37.0,
                    "timezone": "Asia/Tokyo"
                }
            }
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called
        self.mock_interactor.execute.assert_called_once()
        
        # Verify JSON display method was called with empty data
        self.mock_presenter.display_weather_data_json.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_includes_location_in_dto(self):
        """Test that location information is included in the DTO passed to presenter."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = True
        
        # Mock interactor response with location
        mock_response = {
            "success": True,
            "data": {
                "data": [
                    {
                        "time": "2024-01-15T00:00:00Z",
                        "temperature_2m_max": 15.5,
                        "temperature_2m_min": 8.2,
                        "temperature_2m_mean": 11.8,
                        "precipitation_sum": 5.0,
                        "sunshine_duration": 28800.0,
                        "sunshine_hours": 8.0
                    }
                ],
                "total_count": 1,
                "location": {
                    "latitude": 35.6762,
                    "longitude": 139.6503,
                    "elevation": 37.0,
                    "timezone": "Asia/Tokyo"
                }
            }
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify presenter was called with DTO that includes location
        self.mock_presenter.display_weather_data_json.assert_called_once()
        called_dto = self.mock_presenter.display_weather_data_json.call_args[0][0]
        
        # Verify location is present in the DTO
        assert called_dto.location is not None
        assert called_dto.location.latitude == 35.6762
        assert called_dto.location.longitude == 139.6503
        assert called_dto.location.elevation == 37.0
        assert called_dto.location.timezone == "Asia/Tokyo"
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_error(self):
        """Test handling weather command with error."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = False
        
        # Mock interactor response with error
        mock_response = {
            "success": False,
            "error": {
                "code": "API_ERROR",
                "message": "API request failed"
            }
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify error was displayed
        self.mock_presenter.display_error.assert_called_with("API request failed", "API_ERROR", json_output=False)
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_error_json_output(self):
        """Test handling weather command with error and JSON output."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = True
        
        # Mock interactor response with error
        mock_response = {
            "success": False,
            "error": {
                "code": "API_ERROR",
                "message": "API request failed"
            }
        }
        self.mock_interactor.execute.return_value = mock_response
        
        await self.controller.handle_weather_command(args)
        
        # Verify error was displayed with JSON format
        self.mock_presenter.display_error.assert_called_with("API request failed", "API_ERROR", json_output=True)
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_validation_error(self):
        """Test handling weather command with validation error."""
        # Mock arguments with invalid location
        args = MagicMock()
        args.location = "invalid,location"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = False
        
        await self.controller.handle_weather_command(args)
        
        # Verify error was displayed
        self.mock_presenter.display_error.assert_called()
        # Interactor should not be called due to validation error
        self.mock_interactor.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_validation_error_json_output(self):
        """Test handling weather command with validation error and JSON output."""
        # Mock arguments with invalid location
        args = MagicMock()
        args.location = "invalid,location"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = True
        
        await self.controller.handle_weather_command(args)
        
        # Verify error was displayed with JSON format
        call_args = self.mock_presenter.display_error.call_args
        assert call_args[1]['json_output'] is True
        # Interactor should not be called due to validation error
        self.mock_interactor.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_run_no_command(self):
        """Test running with no command specified."""
        # Mock parser to return no command
        parser_mock = MagicMock()
        parser_mock.parse_args.return_value.command = None
        parser_mock.print_help.return_value = None
        
        # Patch create_argument_parser
        from unittest.mock import patch
        with patch.object(self.controller, 'create_argument_parser', return_value=parser_mock):
            await self.controller.run([])
            parser_mock.print_help.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_weather_command(self):
        """Test running weather command."""
        # Mock parser to return weather command
        parser_mock = MagicMock()
        args_mock = MagicMock()
        args_mock.command = 'weather'
        args_mock.location = "35.6762,139.6503"
        args_mock.start_date = None
        args_mock.end_date = None
        args_mock.days = 7
        args_mock.json = False
        parser_mock.parse_args.return_value = args_mock
        
        # Mock interactor response
        mock_response = {
            "success": True,
            "data": {"data": [], "total_count": 0}
        }
        self.mock_interactor.execute.return_value = mock_response
        
        # Patch create_argument_parser
        from unittest.mock import patch
        with patch.object(self.controller, 'create_argument_parser', return_value=parser_mock):
            with patch.object(self.controller, 'handle_weather_command') as mock_handle:
                await self.controller.run(['weather', '--location', '35.6762,139.6503'])
                mock_handle.assert_called_once_with(args_mock)
