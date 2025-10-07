"""Tests for GrowthPeriodOptimizeCliController."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from agrr_core.adapter.controllers.growth_period_optimize_cli_controller import (
    GrowthPeriodOptimizeCliController,
)
from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
    CandidateResultDTO,
)


class TestGrowthPeriodOptimizeCliController:
    """Test cases for GrowthPeriodOptimizeCliController."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_growth_progress_crop_requirement_gateway,
        mock_growth_progress_weather_gateway,
    ):
        """Set up test fixtures using conftest mocks."""
        # Create mock presenter
        self.mock_presenter = Mock()
        
        # Create controller with mocked dependencies
        self.controller = GrowthPeriodOptimizeCliController(
            crop_requirement_gateway=mock_growth_progress_crop_requirement_gateway,
            weather_gateway=mock_growth_progress_weather_gateway,
            presenter=self.mock_presenter,
        )
        self.mock_crop_requirement_gateway = mock_growth_progress_crop_requirement_gateway
        self.mock_weather_gateway = mock_growth_progress_weather_gateway

    @pytest.mark.asyncio
    async def test_execute_calls_interactor(self):
        """Test that execute method calls interactor correctly."""
        # Setup request
        request = OptimalGrowthPeriodRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            candidate_start_dates=[datetime(2024, 4, 1), datetime(2024, 4, 15)],
            weather_data_file="weather.json",
            daily_fixed_cost=1000.0,
        )
        
        # Setup mock response
        candidates = [
            CandidateResultDTO(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 4, 10),
                growth_days=10,
                total_cost=10000.0,
                is_optimal=True,
            ),
        ]
        mock_response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 4, 10),
            growth_days=10,
            total_cost=10000.0,
            daily_fixed_cost=1000.0,
            candidates=candidates,
        )
        
        # Mock interactor's execute to return response
        self.controller.interactor.execute = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await self.controller.execute(request)
        
        # Assertions
        assert result == mock_response
        self.controller.interactor.execute.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_handle_optimize_command_success(self):
        """Test successful optimize command handling."""
        # Create mock args
        args = Mock()
        args.crop = "rice"
        args.variety = "Koshihikari"
        args.start_dates = "2024-04-01,2024-04-15"
        args.weather_file = "weather.json"
        args.daily_cost = 1000.0
        args.format = "table"
        
        # Setup mock response
        candidates = [
            CandidateResultDTO(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 4, 10),
                growth_days=10,
                total_cost=10000.0,
                is_optimal=True,
            ),
        ]
        mock_response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 4, 10),
            growth_days=10,
            total_cost=10000.0,
            daily_fixed_cost=1000.0,
            candidates=candidates,
        )
        
        # Mock interactor
        self.controller.interactor.execute = AsyncMock(return_value=mock_response)
        
        # Execute
        await self.controller.handle_optimize_command(args)
        
        # Verify presenter was updated and called
        assert self.mock_presenter.output_format == "table"
        self.mock_presenter.present.assert_called_once_with(mock_response)

    @pytest.mark.asyncio
    async def test_handle_optimize_command_invalid_date_format(self, capsys):
        """Test handling of invalid date format."""
        # Create mock args with invalid date
        args = Mock()
        args.crop = "rice"
        args.variety = None
        args.start_dates = "2024-04-01,invalid-date,2024-05-01"
        args.weather_file = "weather.json"
        args.daily_cost = 500.0
        args.format = "table"
        
        # Execute
        await self.controller.handle_optimize_command(args)
        
        # Verify error message was printed
        captured = capsys.readouterr()
        assert "Invalid date format" in captured.out
        assert 'Use YYYY-MM-DD' in captured.out

    @pytest.mark.asyncio
    async def test_parse_start_dates_success(self):
        """Test successful parsing of start dates."""
        dates_str = "2024-04-01,2024-04-15,2024-05-01"
        dates = self.controller._parse_start_dates(dates_str)
        
        assert len(dates) == 3
        assert dates[0] == datetime(2024, 4, 1)
        assert dates[1] == datetime(2024, 4, 15)
        assert dates[2] == datetime(2024, 5, 1)

    @pytest.mark.asyncio
    async def test_parse_start_dates_with_spaces(self):
        """Test parsing dates with spaces."""
        dates_str = "2024-04-01 , 2024-04-15 , 2024-05-01"
        dates = self.controller._parse_start_dates(dates_str)
        
        assert len(dates) == 3
        assert dates[0] == datetime(2024, 4, 1)

    @pytest.mark.asyncio
    async def test_parse_start_dates_invalid(self):
        """Test parsing invalid dates raises ValueError."""
        dates_str = "2024-04-01,not-a-date"
        
        with pytest.raises(ValueError, match="Invalid date format"):
            self.controller._parse_start_dates(dates_str)

    def test_create_argument_parser(self):
        """Test argument parser creation."""
        parser = self.controller.create_argument_parser()
        
        # Test parsing valid arguments
        args = parser.parse_args([
            "optimize",
            "--crop", "rice",
            "--variety", "Koshihikari",
            "--start-dates", "2024-04-01,2024-04-15",
            "--weather-file", "weather.json",
            "--daily-cost", "1000",
            "--format", "table",
        ])
        
        assert args.command == "optimize"
        assert args.crop == "rice"
        assert args.variety == "Koshihikari"
        assert args.start_dates == "2024-04-01,2024-04-15"
        assert args.weather_file == "weather.json"
        assert args.daily_cost == 1000.0
        assert args.format == "table"

    @pytest.mark.asyncio
    async def test_run_with_optimize_command(self):
        """Test run method with optimize command."""
        # Mock handle_optimize_command
        self.controller.handle_optimize_command = AsyncMock()
        
        # Run
        await self.controller.run([
            "optimize",
            "--crop", "rice",
            "--start-dates", "2024-04-01",
            "--weather-file", "weather.json",
            "--daily-cost", "1000",
        ])
        
        # Verify handle_optimize_command was called
        self.controller.handle_optimize_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_without_command(self, capsys):
        """Test run method without command shows help."""
        await self.controller.run([])
        
        captured = capsys.readouterr()
        assert "Optimal Growth Period Calculator" in captured.out or "usage:" in captured.out

