"""Unit tests for GrowthPeriodOptimizeCliController.

Tests the data transfer from CLI controller to Interactor,
specifically focusing on the filter_redundant_candidates flag.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from argparse import Namespace

from agrr_core.adapter.controllers.growth_period_optimize_cli_controller import (
    GrowthPeriodOptimizeCliController,
)
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.usecase.dto.growth_period_optimize_request_dto import (
    OptimalGrowthPeriodRequestDTO,
)
from agrr_core.usecase.dto.growth_period_optimize_response_dto import (
    OptimalGrowthPeriodResponseDTO,
    CandidateResultDTO,
)


class TestGrowthPeriodOptimizeCliController:
    """Test data transfer through controller layer."""

    @pytest.fixture
    def mock_crop_profile_gateway(self):
        """Create mock crop profile gateway."""
        gateway = AsyncMock()
        
        # Create test crop profile
        crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            variety="Koshihikari",
        )
        
        stage = GrowthStage(name="Growth", order=1)
        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
            max_temperature=42.0,
        )
        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=SunshineProfile(),
            thermal=ThermalRequirement(required_gdd=100.0),
        )
        
        crop_profile = CropProfile(crop=crop, stage_requirements=[stage_req])
        gateway.get.return_value = crop_profile
        
        return gateway

    @pytest.fixture
    def mock_weather_gateway(self):
        """Create mock weather gateway."""
        gateway = AsyncMock()
        return gateway

    @pytest.fixture
    def mock_presenter(self):
        """Create mock presenter."""
        presenter = MagicMock()
        presenter.output_format = "table"
        return presenter

    @pytest.fixture
    def test_field(self):
        """Create test field."""
        return Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=1000.0,
        )

    @pytest.fixture
    def controller(self, mock_crop_profile_gateway, mock_weather_gateway, mock_presenter, test_field):
        """Create controller with mocked dependencies."""
        return GrowthPeriodOptimizeCliController(
            crop_profile_gateway=mock_crop_profile_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            field=test_field,
        )

    @pytest.mark.asyncio
    async def test_flag_transfer_with_default_filtering_enabled(
        self, controller, mock_crop_profile_gateway
    ):
        """Test that filter_redundant_candidates=True is passed by default."""
        # Create mock args without --no-filter-redundant flag
        args = Namespace(
            evaluation_start="2024-04-01",
            evaluation_end="2024-06-30",
            format="table",
            no_filter_redundant=False,  # Default: filtering enabled
        )
        
        # Create mock response
        mock_response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 15),
            growth_days=76,
            total_cost=76000.0,
            revenue=None,
            profit=-76000.0,
            daily_fixed_cost=1000.0,
            field=controller.field,
            candidates=[],
        )
        
        # Mock the interactor's execute method to capture the request
        captured_request = None
        
        async def capture_execute(request):
            nonlocal captured_request
            captured_request = request
            return mock_response
        
        controller.interactor.execute = AsyncMock(side_effect=capture_execute)
        
        # Execute the command
        await controller.handle_period_command(args)
        
        # Verify that the request was created with filter_redundant_candidates=True
        assert captured_request is not None, "Request was not passed to interactor"
        assert captured_request.filter_redundant_candidates is True, \
            "Expected filter_redundant_candidates=True by default"

    @pytest.mark.asyncio
    async def test_flag_transfer_with_filtering_disabled(
        self, controller, mock_crop_profile_gateway
    ):
        """Test that filter_redundant_candidates=False is passed when --no-filter-redundant is specified."""
        # Create mock args with --no-filter-redundant flag
        args = Namespace(
            evaluation_start="2024-04-01",
            evaluation_end="2024-06-30",
            format="table",
            no_filter_redundant=True,  # Filtering disabled
        )
        
        # Create mock response
        mock_response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 15),
            growth_days=76,
            total_cost=76000.0,
            revenue=None,
            profit=-76000.0,
            daily_fixed_cost=1000.0,
            field=controller.field,
            candidates=[],
        )
        
        # Mock the interactor's execute method to capture the request
        captured_request = None
        
        async def capture_execute(request):
            nonlocal captured_request
            captured_request = request
            return mock_response
        
        controller.interactor.execute = AsyncMock(side_effect=capture_execute)
        
        # Execute the command
        await controller.handle_period_command(args)
        
        # Verify that the request was created with filter_redundant_candidates=False
        assert captured_request is not None, "Request was not passed to interactor"
        assert captured_request.filter_redundant_candidates is False, \
            "Expected filter_redundant_candidates=False when --no-filter-redundant is specified"

    @pytest.mark.asyncio
    async def test_request_dto_structure(self, controller, mock_crop_profile_gateway):
        """Test that RequestDTO is created with all required fields including the flag."""
        args = Namespace(
            evaluation_start="2024-04-01",
            evaluation_end="2024-06-30",
            format="json",
            no_filter_redundant=False,
        )
        
        # Create mock response
        mock_response = OptimalGrowthPeriodResponseDTO(
            crop_name="Rice",
            variety="Koshihikari",
            optimal_start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 15),
            growth_days=76,
            total_cost=76000.0,
            revenue=None,
            profit=-76000.0,
            daily_fixed_cost=1000.0,
            field=controller.field,
            candidates=[],
        )
        
        # Mock the interactor's execute method to capture the request
        captured_request = None
        
        async def capture_execute(request):
            nonlocal captured_request
            captured_request = request
            return mock_response
        
        controller.interactor.execute = AsyncMock(side_effect=capture_execute)
        
        # Execute the command
        await controller.handle_period_command(args)
        
        # Verify all DTO fields
        assert captured_request is not None
        assert captured_request.crop_id == "rice"
        assert captured_request.variety == "Koshihikari"
        assert captured_request.evaluation_period_start == datetime(2024, 4, 1)
        assert captured_request.evaluation_period_end == datetime(2024, 6, 30)
        assert captured_request.field is not None
        assert captured_request.filter_redundant_candidates is True

    def test_argument_parser_includes_no_filter_flag(self, controller):
        """Test that argument parser includes --no-filter-redundant option."""
        parser = controller.create_argument_parser()
        
        # Parse with default (no flag)
        args_default = parser.parse_args([
            "--crop-file", "test.json",
            "--evaluation-start", "2024-04-01",
            "--evaluation-end", "2024-06-30",
            "--weather-file", "weather.json",
            "--field-file", "field.json",
        ])
        assert args_default.no_filter_redundant is False
        
        # Parse with --no-filter-redundant flag
        args_no_filter = parser.parse_args([
            "--crop-file", "test.json",
            "--evaluation-start", "2024-04-01",
            "--evaluation-end", "2024-06-30",
            "--weather-file", "weather.json",
            "--field-file", "field.json",
            "--no-filter-redundant",
        ])
        assert args_no_filter.no_filter_redundant is True

