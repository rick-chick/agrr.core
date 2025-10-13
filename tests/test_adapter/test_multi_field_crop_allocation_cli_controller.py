"""Tests for MultiFieldCropAllocationCliController."""

import pytest
import json
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from io import StringIO
from pathlib import Path

from agrr_core.adapter.controllers.multi_field_crop_allocation_cli_controller import (
    MultiFieldCropAllocationCliController,
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
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_schedule_entity import FieldSchedule
from agrr_core.entity.entities.multi_field_optimization_result_entity import (
    MultiFieldOptimizationResult,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_response_dto import (
    MultiFieldCropAllocationResponseDTO,
)


@pytest.mark.asyncio
class TestMultiFieldCropAllocationCliController:
    """Test cases for CLI controller for multi-field crop allocation."""

    async def test_optimize_command_basic(self):
        """Test that basic optimization command works correctly."""
        # Setup mocks
        mock_field_gateway = AsyncMock()
        mock_crop_requirement_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup fields
        field1 = Field(
            field_id="field_01",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
            location="Location 1"
        )
        field2 = Field(
            field_id="field_02",
            name="Field 2",
            area=800.0,
            daily_fixed_cost=4000.0,
            location="Location 2"
        )
        
        async def field_get_side_effect(field_id):
            return {
                "field_01": field1,
                "field_02": field2,
            }.get(field_id)
        
        mock_field_gateway.get.side_effect = field_get_side_effect

        # Setup crop requirements
        crop1 = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
        crop2 = Crop(crop_id="tomato", name="Tomato", area_per_unit=0.5, variety="Momotaro")
        
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

        crop_req1 = CropRequirementAggregate(
            crop=crop1, stage_requirements=[stage_req]
        )
        crop_req2 = CropRequirementAggregate(
            crop=crop2, stage_requirements=[stage_req]
        )

        # Set up side_effect to handle both string and DTO inputs
        async def crop_requirement_side_effect(crop_query=None):
            if crop_query is None:
                # get() called without arguments - return first requirement
                return crop_req1
            if hasattr(crop_query, 'crop_query'):
                # It's a DTO
                query = crop_query.crop_query
            else:
                # It's a string
                query = crop_query
            
            mapping = {
                "rice Koshihikari": crop_req1,
                "tomato Momotaro": crop_req2,
            }
            return mapping.get(query)
        
        mock_crop_requirement_gateway.craft.side_effect = crop_requirement_side_effect
        # gateway.get() called without arguments - return crop requirement
        mock_crop_requirement_gateway.get.side_effect = crop_requirement_side_effect

        # Weather data - generate for full planning period (Apr-Oct)
        weather_data = [
            WeatherData(
                time=datetime(2024, month, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for month, days_in_month in [(4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31)]
            for day in range(1, days_in_month + 1)
        ]
        mock_weather_gateway.get.return_value = weather_data

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_requirement_gateway=mock_crop_requirement_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
        )

        # Create temporary files for fields and crops
        with tempfile.TemporaryDirectory() as tmpdir:
            fields_file = Path(tmpdir) / "fields.json"
            crops_file = Path(tmpdir) / "crops.json"
            
            # Write fields file
            fields_data = {
                "fields": [
                    {"field_id": "field_01"},
                    {"field_id": "field_02"}
                ]
            }
            with open(fields_file, 'w') as f:
                json.dump(fields_data, f)
            
            # Write crops file
            crops_data = {
                "crops": [
                    {"crop_id": "rice", "variety": "Koshihikari"},
                    {"crop_id": "tomato", "variety": "Momotaro"}
                ]
            }
            with open(crops_file, 'w') as f:
                json.dump(crops_data, f)

            # Simulate CLI arguments
            args = [
                "optimize",
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
            ]

            with patch("sys.stdout", new=StringIO()):
                await controller.run(args)

        # Verify that presenter was called
        mock_presenter.present.assert_called_once()

    async def test_optimize_command_with_target_area(self):
        """Test optimization with target area specification."""
        # Setup mocks
        mock_field_gateway = AsyncMock()
        mock_crop_requirement_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup field
        field1 = Field(
            field_id="field_01",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        mock_field_gateway.get.return_value = field1

        # Setup crop
        crop1 = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
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
        crop_req1 = CropRequirementAggregate(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_requirement_gateway.craft.return_value = crop_req1
        mock_crop_requirement_gateway.get.return_value = crop_req1

        # Weather data - generate for full planning period (Apr-Oct)
        weather_data = [
            WeatherData(
                time=datetime(2024, month, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for month, days_in_month in [(4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31)]
            for day in range(1, days_in_month + 1)
        ]
        mock_weather_gateway.get.return_value = weather_data

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_requirement_gateway=mock_crop_requirement_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
        )

        # Create temporary files for fields and crops
        with tempfile.TemporaryDirectory() as tmpdir:
            fields_file = Path(tmpdir) / "fields.json"
            crops_file = Path(tmpdir) / "crops.json"
            
            # Write fields file
            fields_data = {
                "fields": [{"field_id": "field_01"}]
            }
            with open(fields_file, 'w') as f:
                json.dump(fields_data, f)
            
            # Write crops file with target area
            crops_data = {
                "crops": [
                    {"crop_id": "rice", "variety": "Koshihikari", "target_area": 500.0}
                ]
            }
            with open(crops_file, 'w') as f:
                json.dump(crops_data, f)

            # Simulate CLI arguments with target area
            args = [
                "optimize",
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
            ]

            with patch("sys.stdout", new=StringIO()):
                await controller.run(args)

        # Verify presenter was called
        mock_presenter.present.assert_called_once()

    async def test_optimize_command_with_json_output(self):
        """Test optimization with JSON output format."""
        # Setup mocks
        mock_field_gateway = AsyncMock()
        mock_crop_requirement_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup field
        field1 = Field(
            field_id="field_01",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        mock_field_gateway.get.return_value = field1

        # Setup crop
        crop1 = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
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
        crop_req1 = CropRequirementAggregate(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_requirement_gateway.craft.return_value = crop_req1

        mock_crop_requirement_gateway.get.return_value = crop_req1


        # Weather data - generate for full planning period (Apr-Oct)
        weather_data = [
            WeatherData(
                time=datetime(2024, month, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for month, days_in_month in [(4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31)]
            for day in range(1, days_in_month + 1)
        ]
        mock_weather_gateway.get.return_value = weather_data

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_requirement_gateway=mock_crop_requirement_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
        )

        # Create temporary files for fields and crops
        with tempfile.TemporaryDirectory() as tmpdir:
            fields_file = Path(tmpdir) / "fields.json"
            crops_file = Path(tmpdir) / "crops.json"
            
            # Write fields file
            fields_data = {
                "fields": [{"field_id": "field_01"}]
            }
            with open(fields_file, 'w') as f:
                json.dump(fields_data, f)
            
            # Write crops file
            crops_data = {
                "crops": [{"crop_id": "rice"}]
            }
            with open(crops_file, 'w') as f:
                json.dump(crops_data, f)

            # Simulate CLI arguments with JSON format
            args = [
                "optimize",
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
                "--format", "json",
            ]

            with patch("sys.stdout", new=StringIO()):
                await controller.run(args)

        # Verify presenter format was updated to json
        assert mock_presenter.output_format == "json"
        mock_presenter.present.assert_called_once()

    async def test_optimize_command_with_interaction_rules(self):
        """Test optimization with interaction rules."""
        # Setup mocks
        mock_field_gateway = AsyncMock()
        mock_crop_requirement_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_interaction_rule_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup field
        field1 = Field(
            field_id="field_01",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        mock_field_gateway.get.return_value = field1

        # Setup crop
        crop1 = Crop(crop_id="tomato", name="Tomato", area_per_unit=0.5)
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
        crop_req1 = CropRequirementAggregate(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_requirement_gateway.craft.return_value = crop_req1

        mock_crop_requirement_gateway.get.return_value = crop_req1


        # Weather data - generate for full planning period (Apr-Oct)
        weather_data = [
            WeatherData(
                time=datetime(2024, month, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for month, days_in_month in [(4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31)]
            for day in range(1, days_in_month + 1)
        ]
        mock_weather_gateway.get.return_value = weather_data

        # Mock interaction rules
        mock_interaction_rule_gateway.load_from_file.return_value = []

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_requirement_gateway=mock_crop_requirement_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            interaction_rule_gateway=mock_interaction_rule_gateway,
        )

        # Create temporary files for fields and crops
        with tempfile.TemporaryDirectory() as tmpdir:
            fields_file = Path(tmpdir) / "fields.json"
            crops_file = Path(tmpdir) / "crops.json"
            
            # Write fields file
            fields_data = {
                "fields": [{"field_id": "field_01"}]
            }
            with open(fields_file, 'w') as f:
                json.dump(fields_data, f)
            
            # Write crops file
            crops_data = {
                "crops": [{"crop_id": "tomato"}]
            }
            with open(crops_file, 'w') as f:
                json.dump(crops_data, f)

            # Simulate CLI arguments with interaction rules
            args = [
                "optimize",
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
                "--interaction-rules-file", "test_interaction_rules.json",
            ]

            with patch("sys.stdout", new=StringIO()):
                await controller.run(args)

        # Verify interaction rules were loaded
        mock_interaction_rule_gateway.load_from_file.assert_called_once_with(
            "test_interaction_rules.json"
        )
        mock_presenter.present.assert_called_once()

    async def test_load_crops_from_file(self):
        """Test crop loading from JSON file."""
        # Setup minimal mocks
        mock_field_gateway = AsyncMock()
        mock_crop_requirement_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_presenter = MagicMock()

        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_requirement_gateway=mock_crop_requirement_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            crops_file = Path(tmpdir) / "crops.json"
            
            # Test basic crop specification
            crops_data = {
                "crops": [
                    {"crop_id": "rice"},
                    {"crop_id": "rice", "variety": "Koshihikari"},
                    {"crop_id": "rice", "variety": "Koshihikari", "target_area": 1000.0},
                    {"crop_id": "tomato", "target_area": 500.0, "crop_requirement_file": "tomato.json"}
                ]
            }
            with open(crops_file, 'w') as f:
                json.dump(crops_data, f)
            
            specs = controller._load_crops_from_file(str(crops_file))
            
            assert len(specs) == 4
            assert specs[0].crop_id == "rice"
            assert specs[0].variety is None
            assert specs[0].target_area is None
            
            assert specs[1].crop_id == "rice"
            assert specs[1].variety == "Koshihikari"
            assert specs[1].target_area is None
            
            assert specs[2].crop_id == "rice"
            assert specs[2].variety == "Koshihikari"
            assert specs[2].target_area == 1000.0
            
            assert specs[3].crop_id == "tomato"
            assert specs[3].target_area == 500.0
            assert specs[3].crop_requirement_file == "tomato.json"

    async def test_optimize_command_with_parallel_enabled(self):
        """Test optimization with parallel candidate generation enabled."""
        # Setup mocks
        mock_field_gateway = AsyncMock()
        mock_crop_requirement_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup field
        field1 = Field(
            field_id="field_01",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        mock_field_gateway.get.return_value = field1

        # Setup crop
        crop1 = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
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
        crop_req1 = CropRequirementAggregate(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_requirement_gateway.craft.return_value = crop_req1

        mock_crop_requirement_gateway.get.return_value = crop_req1


        # Weather data - generate for full planning period (Apr-Oct)
        weather_data = [
            WeatherData(
                time=datetime(2024, month, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for month, days_in_month in [(4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31)]
            for day in range(1, days_in_month + 1)
        ]
        mock_weather_gateway.get.return_value = weather_data

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_requirement_gateway=mock_crop_requirement_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
        )

        # Create temporary files for fields and crops
        with tempfile.TemporaryDirectory() as tmpdir:
            fields_file = Path(tmpdir) / "fields.json"
            crops_file = Path(tmpdir) / "crops.json"
            
            # Write fields file
            fields_data = {
                "fields": [{"field_id": "field_01"}]
            }
            with open(fields_file, 'w') as f:
                json.dump(fields_data, f)
            
            # Write crops file
            crops_data = {
                "crops": [{"crop_id": "rice"}]
            }
            with open(crops_file, 'w') as f:
                json.dump(crops_data, f)

            # Simulate CLI arguments with parallel enabled
            args = [
                "optimize",
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
                "--enable-parallel",
            ]

            with patch("sys.stdout", new=StringIO()):
                await controller.run(args)

        # Verify presenter was called
        mock_presenter.present.assert_called_once()

    async def test_optimize_command_with_local_search_disabled(self):
        """Test optimization with local search disabled."""
        # Setup mocks
        mock_field_gateway = AsyncMock()
        mock_crop_requirement_gateway = AsyncMock()
        mock_weather_gateway = AsyncMock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        # Setup field
        field1 = Field(
            field_id="field_01",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        mock_field_gateway.get.return_value = field1

        # Setup crop
        crop1 = Crop(crop_id="rice", name="Rice", area_per_unit=0.25)
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
        crop_req1 = CropRequirementAggregate(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_requirement_gateway.craft.return_value = crop_req1

        mock_crop_requirement_gateway.get.return_value = crop_req1


        # Weather data - generate for full planning period (Apr-Oct)
        weather_data = [
            WeatherData(
                time=datetime(2024, month, day),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            )
            for month, days_in_month in [(4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30), (10, 31)]
            for day in range(1, days_in_month + 1)
        ]
        mock_weather_gateway.get.return_value = weather_data

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_requirement_gateway=mock_crop_requirement_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
        )

        # Create temporary files for fields and crops
        with tempfile.TemporaryDirectory() as tmpdir:
            fields_file = Path(tmpdir) / "fields.json"
            crops_file = Path(tmpdir) / "crops.json"
            
            # Write fields file
            fields_data = {
                "fields": [{"field_id": "field_01"}]
            }
            with open(fields_file, 'w') as f:
                json.dump(fields_data, f)
            
            # Write crops file
            crops_data = {
                "crops": [{"crop_id": "rice"}]
            }
            with open(crops_file, 'w') as f:
                json.dump(crops_data, f)

            # Simulate CLI arguments with local search disabled
            args = [
                "optimize",
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
                "--disable-local-search",
            ]

            with patch("sys.stdout", new=StringIO()):
                await controller.run(args)

        # Verify presenter was called
        mock_presenter.present.assert_called_once()

