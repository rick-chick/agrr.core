"""Tests for GrowthProgressCliController."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from agrr_core.adapter.controllers.growth_progress_cli_controller import (
    GrowthProgressCliController,
)
from agrr_core.usecase.dto.growth_progress_calculate_request_dto import (
    GrowthProgressCalculateRequestDTO,
)
from agrr_core.usecase.dto.growth_progress_calculate_response_dto import (
    GrowthProgressCalculateResponseDTO,
    GrowthProgressRecordDTO,
)


class TestGrowthProgressCliController:
    """Test cases for GrowthProgressCliController."""

    @pytest.fixture(autouse=True)
    def setup(
        self,
        mock_growth_progress_crop_requirement_gateway,
        mock_growth_progress_weather_gateway,
        mock_growth_progress_presenter,
    ):
        """Set up test fixtures using conftest mocks."""
        # Create controller with mocked dependencies from conftest
        self.controller = GrowthProgressCliController(
            crop_requirement_gateway=mock_growth_progress_crop_requirement_gateway,
            weather_gateway=mock_growth_progress_weather_gateway,
            presenter=mock_growth_progress_presenter,
        )
        self.mock_crop_requirement_gateway = mock_growth_progress_crop_requirement_gateway
        self.mock_weather_gateway = mock_growth_progress_weather_gateway
        self.mock_presenter = mock_growth_progress_presenter

    @pytest.mark.asyncio
    async def test_execute_calls_interactor(self):
        """Test that execute method calls interactor correctly."""
        # Setup request
        request = GrowthProgressCalculateRequestDTO(
            crop_id="rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
            weather_data_file="weather.json",
        )
        
        # Setup mock response
        mock_response = GrowthProgressCalculateResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
            progress_records=[],
        )
        
        # Mock interactor's execute to return response
        self.controller.interactor.execute = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await self.controller.execute(request)
        
        # Assertions
        assert result == mock_response
        self.controller.interactor.execute.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_handle_progress_command_success(self):
        """Test successful progress command handling."""
        # Create mock args
        args = Mock()
        args.crop = "rice"
        args.variety = "Koshihikari"
        args.start_date = "2024-05-01"
        args.weather_file = "weather.json"
        args.format = "table"
        
        # Setup mock response
        mock_record = GrowthProgressRecordDTO(
            date=datetime(2024, 5, 1),
            cumulative_gdd=15.0,
            total_required_gdd=1000.0,
            growth_percentage=1.5,
            stage_name="Vegetative",
            is_complete=False,
        )
        
        mock_response = GrowthProgressCalculateResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            start_date=datetime(2024, 5, 1),
            progress_records=[mock_record],
        )
        
        # Mock interactor's execute
        self.controller.interactor.execute = AsyncMock(return_value=mock_response)
        
        # Execute
        await self.controller.handle_progress_command(args)
        
        # Assertions
        self.controller.interactor.execute.assert_called_once()
        self.mock_presenter.present.assert_called_once_with(mock_response)

    @pytest.mark.asyncio
    async def test_handle_progress_command_invalid_date(self, capsys):
        """Test error handling for invalid date format."""
        # Create mock args with invalid date
        args = Mock()
        args.crop = "rice"
        args.variety = "Koshihikari"
        args.start_date = "invalid-date"
        args.weather_file = "weather.json"
        args.format = "table"
        
        # Execute
        await self.controller.handle_progress_command(args)
        
        # Assertions - should print error message
        captured = capsys.readouterr()
        assert "Invalid date format" in captured.out
        
        # Interactor should not be called
        self.controller.interactor.execute = AsyncMock()
        assert not self.controller.interactor.execute.called

    def test_controller_implements_input_port(self):
        """Test that controller implements Input Port interface."""
        from agrr_core.usecase.ports.input.growth_progress_calculate_input_port import (
            GrowthProgressCalculateInputPort,
        )
        
        # Controller should be an instance of Input Port
        assert isinstance(self.controller, GrowthProgressCalculateInputPort)

    def test_controller_has_required_dependencies(self):
        """Test that controller has all required dependencies injected."""
        assert self.controller.crop_requirement_gateway is not None
        assert self.controller.weather_gateway is not None
        assert self.controller.presenter is not None
        assert self.controller.interactor is not None

