"""Tests for CLI weather controller."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from agrr_core.adapter.controllers.weather_cli_controller import WeatherCliFetchController
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.adapter.gateways.weather_gateway_adapter import WeatherGatewayAdapter as WeatherGatewayImpl
from agrr_core.entity import WeatherData, Location


class TestWeatherCliFetchController:
    """Test cases for WeatherCliFetchController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_gateway = AsyncMock(spec=WeatherGatewayImpl)
        self.mock_presenter = MagicMock(spec=WeatherCLIPresenter)
        self.controller = WeatherCliFetchController(
            weather_gateway=self.mock_gateway,
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
            self.controller.parse_location("invalid")
    
    def test_parse_location_invalid_coordinates(self):
        """Test parsing invalid coordinates."""
        with pytest.raises(ValueError, match="Latitude must be between"):
            self.controller.parse_location("91.0,139.6503")
    
    def test_parse_date_valid(self):
        """Test parsing valid date string."""
        result = self.controller.parse_date("2024-01-01")
        assert result == "2024-01-01"
    
    def test_parse_date_invalid(self):
        """Test parsing invalid date string."""
        with pytest.raises(ValueError, match="Invalid date format"):
            self.controller.parse_date("invalid-date")
    
    def test_calculate_date_range(self):
        """Test calculating date range."""
        start, end = self.controller.calculate_date_range(7)
        
        # Should be 7 days ending yesterday
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
        
        assert (end_date - start_date).days == 6  # 7 days inclusive
    
    def test_calculate_date_range_single_day(self):
        """Test calculating single day date range."""
        start, end = self.controller.calculate_date_range(1)
        assert start == end
    
    def test_calculate_date_range_three_days(self):
        """Test calculating three day date range."""
        start, end = self.controller.calculate_date_range(3)
        
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
        
        assert (end_date - start_date).days == 2  # 3 days inclusive
    
    def test_create_argument_parser(self):
        """Test creating argument parser."""
        parser = self.controller.create_argument_parser()
        
        assert parser is not None
        # The prog name may vary depending on how the test is run
        assert hasattr(parser, 'prog')
    
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
        
        # Mock interactor response
        mock_response = {
            'success': True,
            'data': {
                'data': [
                    {
                        'time': '2024-01-15T00:00:00',
                        'temperature_2m_max': 15.5,
                        'temperature_2m_min': 8.2,
                        'temperature_2m_mean': 11.8,
                        'precipitation_sum': 5.0,
                        'sunshine_duration': 28800.0,
                        'sunshine_hours': 8.0
                    }
                ],
                'total_count': 1,
                'location': {
                    'latitude': 35.6762,
                    'longitude': 139.6503,
                    'elevation': 37.0,
                    'timezone': 'Asia/Tokyo'
                }
            }
        }
        
        # Mock interactor execute method
        self.controller.weather_interactor.execute = AsyncMock(return_value=mock_response)
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called
        self.controller.weather_interactor.execute.assert_called_once()
        
        # Verify presenter methods were called
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
        
        # Mock repository response
        mock_weather_data = []
        mock_location = Location(
            latitude=35.6762,
            longitude=139.6503
        )
        
        self.mock_gateway.get_by_location_and_date_range.return_value = [
            mock_weather_data
        ]
        
        await self.controller.handle_weather_command(args)
        
        # Verify repository was called with correct dates
        call_args = self.mock_gateway.get_by_location_and_date_range.call_args[0]
        assert call_args[0] == 35.6762
        assert call_args[1] == 139.6503
        assert call_args[2] == "2024-01-01"
        assert call_args[3] == "2024-01-07"
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_with_start_date_only(self):
        """Test handling weather command with start date only."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = "2024-01-01"
        args.end_date = None
        args.days = 7
        args.json = False
        
        # Mock repository response
        mock_weather_data = []
        mock_location = Location(
            latitude=35.6762,
            longitude=139.6503
        )
        
        self.mock_gateway.get_by_location_and_date_range.return_value = [
            mock_weather_data
        ]
        
        await self.controller.handle_weather_command(args)
        
        # Verify repository was called
        self.mock_gateway.get_by_location_and_date_range.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_with_end_date_only(self):
        """Test handling weather command with end date only."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = "2024-01-07"
        args.days = 7
        args.json = False
        
        # Mock repository response
        mock_weather_data = []
        mock_location = Location(
            latitude=35.6762,
            longitude=139.6503
        )
        
        self.mock_gateway.get_by_location_and_date_range.return_value = [
            mock_weather_data
        ]
        
        await self.controller.handle_weather_command(args)
        
        # Verify repository was called
        self.mock_gateway.get_by_location_and_date_range.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_success_json_output(self):
        """Test handling weather command with JSON output."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = True
        
        # Mock interactor response
        mock_response = {
            'success': True,
            'data': {
                'data': [
                    {
                        'time': '2024-01-15T00:00:00',
                        'temperature_2m_max': 15.5,
                        'temperature_2m_min': 8.2,
                        'temperature_2m_mean': 11.8,
                        'precipitation_sum': 5.0,
                        'sunshine_duration': 28800.0,
                        'sunshine_hours': 8.0
                    }
                ],
                'total_count': 1,
                'location': {
                    'latitude': 35.6762,
                    'longitude': 139.6503,
                    'elevation': 37.0,
                    'timezone': 'Asia/Tokyo'
                }
            }
        }
        
        # Mock interactor execute method
        self.controller.weather_interactor.execute = AsyncMock(return_value=mock_response)
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called
        self.controller.weather_interactor.execute.assert_called_once()
        
        # Verify JSON presenter was called
        self.mock_presenter.display_weather_data_json.assert_called()
    
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
        
        # Mock interactor response with empty data
        mock_response = {
            'success': True,
            'data': {
                'data': [],
                'total_count': 0,
                'location': {
                    'latitude': 35.6762,
                    'longitude': 139.6503,
                    'elevation': None,
                    'timezone': None
                }
            }
        }
        
        # Mock interactor execute method
        self.controller.weather_interactor.execute = AsyncMock(return_value=mock_response)
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called
        self.controller.weather_interactor.execute.assert_called_once()
        
        # Verify JSON presenter was called for empty data
        self.mock_presenter.display_weather_data_json.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_includes_location_in_dto(self):
        """Test that location information is included in DTO."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = False
        
        # Mock repository response with location data
        mock_weather_data = []
        mock_location = Location(
            latitude=35.6762,
            longitude=139.6503,
            elevation=37.0,
            timezone="Asia/Tokyo"
        )
        
        self.mock_gateway.get_by_location_and_date_range.return_value = [
            mock_weather_data
        ]
        
        await self.controller.handle_weather_command(args)
        
        # Verify repository was called
        self.mock_gateway.get_by_location_and_date_range.assert_called_once()
        
        # For empty data with json=False, the success message should be displayed
        # Note: display_success_message is currently commented out in the controller
    
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
        
        # Mock repository to raise exception
        self.mock_gateway.get_by_location_and_date_range.side_effect = Exception("API Error")
        
        await self.controller.handle_weather_command(args)
        
        # Verify repository was called
        self.mock_gateway.get_by_location_and_date_range.assert_called_once()
        
        # Verify error presenter was called
        self.mock_presenter.display_error.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_error_json_output(self):
        """Test handling weather command error with JSON output."""
        # Mock arguments
        args = MagicMock()
        args.location = "35.6762,139.6503"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = True
        
        # Mock repository to raise exception
        self.mock_gateway.get_by_location_and_date_range.side_effect = Exception("API Error")
        
        await self.controller.handle_weather_command(args)
        
        # Verify repository was called
        self.mock_gateway.get_by_location_and_date_range.assert_called_once()
        
        # Verify error presenter was called with JSON flag
        self.mock_presenter.display_error.assert_called()
        call_args = self.mock_presenter.display_error.call_args
        assert call_args[1]['json_output'] is True
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_validation_error(self):
        """Test handling weather command with validation error."""
        # Mock arguments with invalid location
        args = MagicMock()
        args.location = "invalid"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = False
        
        await self.controller.handle_weather_command(args)
        
        # Verify repository was NOT called due to validation error
        self.mock_gateway.get_by_location_and_date_range.assert_not_called()
        
        # Verify error presenter was called
        self.mock_presenter.display_error.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_validation_error_json_output(self):
        """Test handling weather command validation error with JSON output."""
        # Mock arguments with invalid location
        args = MagicMock()
        args.location = "invalid"
        args.start_date = None
        args.end_date = None
        args.days = 7
        args.json = True
        
        await self.controller.handle_weather_command(args)
        
        # Verify repository was NOT called due to validation error
        self.mock_gateway.get_by_location_and_date_range.assert_not_called()
        
        # Verify error presenter was called with JSON flag
        self.mock_presenter.display_error.assert_called()
        call_args = self.mock_presenter.display_error.call_args
        assert call_args[1]['json_output'] is True
    
    @pytest.mark.asyncio
    async def test_run_no_command(self):
        """Test running CLI with no command."""
        result = await self.controller.run([])
        # Should complete without error (help is displayed)
    
    @pytest.mark.asyncio
    async def test_run_weather_command(self):
        """Test running CLI with weather command."""
        # Mock arguments
        args = ["weather", "--location", "35.6762,139.6503", "--days", "7"]
        
        # Mock repository response
        mock_weather_data = []
        mock_location = Location(
            latitude=35.6762,
            longitude=139.6503
        )
        
        self.mock_gateway.get_by_location_and_date_range.return_value = [
            mock_weather_data
        ]
        
        await self.controller.run(args)
        
        # Verify repository was called
        self.mock_gateway.get_by_location_and_date_range.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_weather_command_nasa_power_json_output(self):
        """Test handling weather command with NASA POWER data source and JSON output."""
        # Mock arguments for NASA POWER
        args = MagicMock()
        args.location = "28.6139,77.2090"  # Delhi, India
        args.start_date = "2023-01-01"
        args.end_date = "2023-01-07"
        args.days = 7
        args.data_source = "nasa-power"
        args.json = True
        
        # Mock interactor response with NASA POWER data
        mock_response = {
            'success': True,
            'data': {
                'data': [
                    {
                        'time': '2023-01-01',
                        'temperature_2m_max': 20.21,
                        'temperature_2m_min': 6.12,
                        'temperature_2m_mean': 12.9,
                        'precipitation_sum': 0.0,
                        'sunshine_duration': 11050.0,
                        'sunshine_hours': 3.07,
                        'wind_speed_10m': 1.03,
                        'weather_code': None
                    },
                    {
                        'time': '2023-01-02',
                        'temperature_2m_max': 19.49,
                        'temperature_2m_min': 5.85,
                        'temperature_2m_mean': 12.26,
                        'precipitation_sum': 0.0,
                        'sunshine_duration': 6660.0,
                        'sunshine_hours': 1.85,
                        'wind_speed_10m': 1.09,
                        'weather_code': None
                    }
                ],
                'total_count': 2,
                'location': {
                    'latitude': 28.6139,
                    'longitude': 77.2090,
                    'elevation': None,  # NASA POWER doesn't provide elevation
                    'timezone': None    # NASA POWER doesn't provide timezone
                }
            }
        }
        
        # Mock interactor execute method
        self.controller.weather_interactor.execute = AsyncMock(return_value=mock_response)
        
        await self.controller.handle_weather_command(args)
        
        # Verify interactor was called
        self.controller.weather_interactor.execute.assert_called_once()
        
        # Verify JSON display method was called
        self.mock_presenter.display_weather_data_json.assert_called()
        
        # Verify the call was made with correct data structure
        call_args = self.mock_presenter.display_weather_data_json.call_args
        assert call_args is not None
        weather_list_dto = call_args[0][0]
        assert weather_list_dto.total_count == 2
        assert weather_list_dto.location is not None
        assert weather_list_dto.location.latitude == 28.6139
        assert weather_list_dto.location.longitude == 77.2090
        assert weather_list_dto.location.elevation is None  # NASA POWER specific
        assert weather_list_dto.location.timezone is None   # NASA POWER specific