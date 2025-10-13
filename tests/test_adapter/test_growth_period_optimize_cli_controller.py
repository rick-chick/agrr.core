"""Tests for GrowthPeriodOptimizeCliController with optimization result storage."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from io import StringIO

from agrr_core.adapter.controllers.growth_period_optimize_cli_controller import (
    GrowthPeriodOptimizeCliController,
)
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)


@pytest.mark.asyncio
class TestGrowthPeriodOptimizeCliControllerWithStorage:
    """Test cases for CLI controller with optimization result storage."""

    async def test_optimize_command_saves_results_when_flag_set(self):
        """Test that optimization results are saved when --save-results flag is used."""
        # Setup mocks
        gateway_crop_requirement = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_optimization_result_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup crop requirements
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: 10 GDD per day
        weather_data = [
            WeatherData(
                time=datetime(2024, 4, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for day in range(1, 21)
        ]

        gateway_crop_requirement.get.return_value = crop_requirement
        mock_weather_gateway.get.return_value = weather_data

        # Create field entity
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location="Test Location"
        )

        # Create controller with optimization result gateway and field
        controller = GrowthPeriodOptimizeCliController(
            crop_requirement_gateway=gateway_crop_requirement,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            field=test_field,
            optimization_result_gateway=mock_optimization_result_gateway,
        )

        # Simulate CLI arguments with --save-results flag
        args = [
            "optimize",
            "--crop", "rice",
            "--variety", "Koshihikari",
            "--evaluation-start", "2024-04-01",
            "--evaluation-end", "2024-04-15",
            "--weather-file", "test_weather.json",
            "--field-config", "test_field.json",
            "--save-results",
        ]

        with patch("sys.stdout", new=StringIO()):
            await controller.run(args)

        # Verify that save was called
        mock_optimization_result_gateway.save.assert_called_once()

    async def test_optimize_command_without_gateway(self):
        """Test that optimization works without gateway (no storage)."""
        # Setup mocks
        gateway_crop_requirement = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup crop requirements
        crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: 10 GDD per day
        weather_data = [
            WeatherData(
                time=datetime(2024, 4, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for day in range(1, 21)
        ]

        gateway_crop_requirement.get.return_value = crop_requirement
        mock_weather_gateway.get.return_value = weather_data

        # Create field entity
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location="Test Location"
        )

        # Create controller WITHOUT optimization result gateway
        controller = GrowthPeriodOptimizeCliController(
            crop_requirement_gateway=gateway_crop_requirement,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            field=test_field,
            optimization_result_gateway=None,  # No gateway
        )

        # Simulate CLI arguments
        args = [
            "optimize",
            "--crop", "rice",
            "--variety", "Koshihikari",
            "--evaluation-start", "2024-04-01",
            "--evaluation-end", "2024-04-15",
            "--weather-file", "test_weather.json",
            "--field-config", "test_field.json",
        ]

        # Should not raise any errors even without gateway
        with patch("sys.stdout", new=StringIO()):
            await controller.run(args)
        
        # Verify that presenter was called (optimization completed)
        mock_presenter.present.assert_called_once()

    async def test_list_results_command(self):
        """Test list-results command displays saved results."""
        # Setup mocks
        gateway_crop_requirement = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_optimization_result_gateway = AsyncMock()
        mock_presenter = MagicMock()

        # Setup mock optimization results
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 7, 15),
            growth_days=106,
            accumulated_gdd=1500.0,
            field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=5000.0),
            is_optimal=True,
            base_temperature=10.0,
        )
        
        mock_optimization_result_gateway.get_all.return_value = [
            ("rice_Koshihikari_2024-04-01_2024-06-30", [result1])
        ]

        # Create controller
        controller = GrowthPeriodOptimizeCliController(
            crop_requirement_gateway=gateway_crop_requirement,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            optimization_result_gateway=mock_optimization_result_gateway,
        )

        # Simulate CLI arguments for list-results
        args = ["list-results"]

        with patch("sys.stdout", new=StringIO()) as fake_out:
            await controller.run(args)
            output = fake_out.getvalue()

        # Verify get_all was called
        mock_optimization_result_gateway.get_all.assert_called_once()
        
        # Verify output contains expected information
        assert "rice_Koshihikari_2024-04-01_2024-06-30" in output
        assert "1" in output  # Number of candidates

    async def test_show_result_command(self):
        """Test show-result command displays specific optimization result."""
        # Setup mocks
        gateway_crop_requirement = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_optimization_result_gateway = AsyncMock()
        mock_presenter = MagicMock()

        # Setup mock optimization result
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 7, 15),
            growth_days=106,
            accumulated_gdd=1500.0,
            field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=5000.0),
            is_optimal=True,
            base_temperature=10.0,
        )
        
        mock_optimization_result_gateway.get.return_value = [result1]

        # Create controller
        controller = GrowthPeriodOptimizeCliController(
            crop_requirement_gateway=gateway_crop_requirement,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            optimization_result_gateway=mock_optimization_result_gateway,
        )

        # Simulate CLI arguments for show-result
        optimization_id = "rice_Koshihikari_2024-04-01_2024-06-30"
        args = ["show-result", optimization_id]

        with patch("sys.stdout", new=StringIO()) as fake_out:
            await controller.run(args)
            output = fake_out.getvalue()

        # Verify get was called with correct ID
        mock_optimization_result_gateway.get.assert_called_once_with(optimization_id)
        
        # Verify output contains expected information
        assert optimization_id in output
        assert "2024-04-01" in output
        assert "2024-07-15" in output
        assert "1500.0" in output  # GDD

    async def test_optimize_command_with_interaction_rules(self):
        """Test that --interaction-rules option is correctly parsed and passed to DTO."""
        # Setup mocks
        gateway_crop_requirement = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_optimization_result_gateway = AsyncMock()
        mock_interaction_rule_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup crop requirements
        crop = Crop(crop_id="tomato", name="Tomato", area_per_unit=0.25, variety="Aiko")
        stage = GrowthStage(name="Growth", order=1)

        temp_profile = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=30.0,
            low_stress_threshold=15.0,
            high_stress_threshold=35.0,
            frost_threshold=0.0,
        )
        sunshine_profile = SunshineProfile()

        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_requirement = CropRequirementAggregate(
            crop=crop, stage_requirements=[stage_req]
        )

        # Weather data: 10 GDD per day
        weather_data = [
            WeatherData(
                time=datetime(2024, 4, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for day in range(1, 21)
        ]

        gateway_crop_requirement.get.return_value = crop_requirement
        mock_weather_gateway.get.return_value = weather_data

        # Create field entity
        test_field = Field(
            field_id="test_field",
            name="Test Field",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location="Test Location"
        )

        # Create controller with interaction rule gateway
        controller = GrowthPeriodOptimizeCliController(
            crop_requirement_gateway=gateway_crop_requirement,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            field=test_field,
            optimization_result_gateway=mock_optimization_result_gateway,
            interaction_rule_gateway=mock_interaction_rule_gateway,
        )

        # Simulate CLI arguments with --interaction-rules option
        args = [
            "optimize",
            "--crop", "tomato",
            "--variety", "Aiko",
            "--evaluation-start", "2024-04-01",
            "--evaluation-end", "2024-06-30",
            "--weather-file", "test_weather.json",
            "--field-config", "test_field.json",
            "--interaction-rules", "test_interaction_rules.json",
        ]

        # Mock interaction rules (empty list for this test)
        mock_interaction_rule_gateway.get_rules.return_value = []

        with patch("sys.stdout", new=StringIO()):
            await controller.run(args)

        # Verify that interaction_rule_gateway.get_rules was called (no args - path configured at init)
        mock_interaction_rule_gateway.get_rules.assert_called_once()
