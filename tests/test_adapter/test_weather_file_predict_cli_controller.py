"""Tests for WeatherFilePredictCLIController."""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from agrr_core.adapter.controllers.weather_file_predict_cli_controller import WeatherFilePredictCLIController
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast
from agrr_core.entity.exceptions.file_error import FileError


class TestWeatherFilePredictCLIController:
    """Test cases for WeatherFilePredictCLIController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_predict_interactor = Mock()
        self.mock_cli_presenter = Mock()
        
        # Setup async mock
        self.mock_predict_interactor.execute = AsyncMock()
        
        self.controller = WeatherFilePredictCLIController(
            predict_interactor=self.mock_predict_interactor,
            cli_presenter=self.mock_cli_presenter
        )
    
    # ===== Argument Parser Tests =====
    
    def test_create_argument_parser(self):
        """Test creating argument parser."""
        parser = self.controller.create_argument_parser()
        
        # Check parser attributes
        assert parser.description == "Weather File-based Prediction CLI - Predict weather from file data"
        
        # Check that subcommands exist
        actions = [action.dest for action in parser._actions]
        assert 'command' in actions
    
    # ===== Input Validation Tests =====
    
    
    # ===== Command Handling Tests =====
    
    @pytest.mark.asyncio
    async def test_handle_predict_file_command_success(self):
        """Test successful predict file command execution."""
        predictions = [
            Forecast(date=datetime(2024, 2, 1), predicted_value=17.0)
        ]
        self.mock_predict_interactor.execute = AsyncMock(return_value=predictions)
        
        # Mock arguments
        args = Mock()
        args.input = "input.json"
        args.output = "output.json"
        args.days = 7
        
        # Execute
        await self.controller.handle_predict_file_command(args)
        
        # Verify calls
        self.mock_predict_interactor.execute.assert_called_once_with(
            input_source="input.json",
            output_destination="output.json",
            prediction_days=7
        )
        self.mock_cli_presenter.display_success_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_predict_file_command_validation_error(self):
        """Test predict file command with validation error."""
        self.mock_predict_interactor.execute = AsyncMock(
            side_effect=ValueError("Invalid input file format")
        )
        
        args = Mock()
        args.input = "input.xyz"
        args.output = "output.json"
        args.days = 7
        
        await self.controller.handle_predict_file_command(args)
        
        self.mock_cli_presenter.display_error.assert_called_once_with(
            "Invalid input file format", "VALIDATION_ERROR"
        )
    
    @pytest.mark.asyncio
    async def test_handle_predict_file_command_internal_error(self):
        """Test predict file command with internal error."""
        self.mock_predict_interactor.execute = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        args = Mock()
        args.input = "input.json"
        args.output = "output.json"
        args.days = 7
        
        await self.controller.handle_predict_file_command(args)
        
        self.mock_cli_presenter.display_error.assert_called_once_with(
            "Unexpected error: Database connection failed", "INTERNAL_ERROR"
        )
    
    # ===== Run Method Tests =====
    
    @pytest.mark.asyncio
    async def test_run_no_command(self):
        """Test run method with no command provided."""
        with patch('sys.stdout'):
            await self.controller.run([])
    
    @pytest.mark.asyncio
    async def test_run_predict_file_command(self):
        """Test run method with predict-file command."""
        predictions = [Forecast(date=datetime(2024, 2, 1), predicted_value=17.0)]
        self.mock_predict_interactor.execute = AsyncMock(return_value=predictions)
        
        args = ['predict-file', '--input', 'input.json', '--output', 'output.json', '--days', '7']
        
        await self.controller.run(args)
        
        self.mock_predict_interactor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_unknown_command(self):
        """Test run method with unknown command."""
        with pytest.raises(SystemExit):
            await self.controller.run(['unknown-command'])