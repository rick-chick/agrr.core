"""Tests for MultiFieldCropAllocationCliController."""

import pytest
import json
import tempfile
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from io import StringIO
from pathlib import Path

from agrr_core.adapter.controllers.multi_field_crop_allocation_cli_controller import (
    MultiFieldCropAllocationCliController,
)
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_profile_entity import (
    CropProfile,
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
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from argparse import Namespace

class TestMultiFieldCropAllocationCliController:
    """Test cases for CLI controller for multi-field crop allocation."""

    def test_optimize_command_basic(self, optimization_config_legacy):
        """Test that basic optimization command works correctly."""
        # Setup mocks
        mock_field_gateway = Mock()
        mock_crop_gateway = Mock()
        mock_weather_gateway = Mock()
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
        
        def field_get_side_effect(field_id):
            return {
                "field_01": field1,
                "field_02": field2,
            }.get(field_id)
        
        mock_field_gateway.get.side_effect = field_get_side_effect
        mock_field_gateway.get_all.return_value = [field1, field2]

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
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()
        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )

        crop_req1 = CropProfile(
            crop=crop1, stage_requirements=[stage_req]
        )
        crop_req2 = CropProfile(
            crop=crop2, stage_requirements=[stage_req]
        )

        # Setup crop gateway to return all crops
        mock_crop_gateway.get_all.return_value = [crop_req1, crop_req2]
        
        # Setup internal state for save/get operations (used by growth_period_optimizer)
        saved_profile = None
        def save_profile(profile):
            nonlocal saved_profile
            saved_profile = profile
        def get_profile():
            return saved_profile if saved_profile else crop_req1
        
        mock_crop_gateway.save.side_effect = save_profile
        mock_crop_gateway.get.side_effect = get_profile

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
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            config=optimization_config_legacy,
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
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
            ]

            with patch("sys.stdout", new=StringIO()):
                controller.run(args)

        # Verify that presenter was called
        mock_presenter.present.assert_called_once()

    def test_optimize_command_with_target_area(self, optimization_config_legacy):
        """Test optimization with target area specification."""
        # Setup mocks
        mock_field_gateway = Mock()
        mock_crop_gateway = Mock()
        mock_weather_gateway = Mock()
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
        mock_field_gateway.get_all.return_value = [field1]

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
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()
        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )
        crop_req1 = CropProfile(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_gateway.get_all.return_value = [crop_req1]
        
        # Setup internal state for save/get operations (used by growth_period_optimizer)
        saved_profile = None
        def save_profile(profile):
            nonlocal saved_profile
            saved_profile = profile
        def get_profile():
            return saved_profile if saved_profile else crop_req1
        
        mock_crop_gateway.save.side_effect = save_profile
        mock_crop_gateway.get.side_effect = get_profile

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
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            config=optimization_config_legacy,
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
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
            ]

            with patch("sys.stdout", new=StringIO()):
                controller.run(args)

        # Verify presenter was called
        mock_presenter.present.assert_called_once()

    def test_optimize_command_with_json_output(self, optimization_config_legacy):
        """Test optimization with JSON output format."""
        # Setup mocks
        mock_field_gateway = Mock()
        mock_crop_gateway = Mock()
        mock_weather_gateway = Mock()
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
        mock_field_gateway.get_all.return_value = [field1]

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
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()
        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )
        crop_req1 = CropProfile(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_gateway.get_all.return_value = [crop_req1]
        
        # Setup internal state for save/get operations (used by growth_period_optimizer)
        saved_profile = None
        def save_profile(profile):
            nonlocal saved_profile
            saved_profile = profile
        def get_profile():
            return saved_profile if saved_profile else crop_req1
        
        mock_crop_gateway.save.side_effect = save_profile
        mock_crop_gateway.get.side_effect = get_profile

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
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            config=optimization_config_legacy,
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
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
                "--format", "json",
            ]

            with patch("sys.stdout", new=StringIO()):
                controller.run(args)

        # Verify presenter format was updated to json
        assert mock_presenter.output_format == "json"
        mock_presenter.present.assert_called_once()

    def test_optimize_command_with_interaction_rules(self, optimization_config_legacy):
        """Test optimization with interaction rules."""
        # Setup mocks
        mock_field_gateway = Mock()
        mock_crop_gateway = Mock()
        mock_weather_gateway = Mock()
        mock_interaction_rule_gateway = Mock()
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
        mock_field_gateway.get_all.return_value = [field1]

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
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()
        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )
        crop_req1 = CropProfile(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_gateway.get_all.return_value = [crop_req1]
        
        # Setup internal state for save/get operations (used by growth_period_optimizer)
        saved_profile = None
        def save_profile(profile):
            nonlocal saved_profile
            saved_profile = profile
        def get_profile():
            return saved_profile if saved_profile else crop_req1
        
        mock_crop_gateway.save.side_effect = save_profile
        mock_crop_gateway.get.side_effect = get_profile

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

        # Mock interaction rules gateway to return empty list
        mock_interaction_rule_gateway.get_rules.return_value = []

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            interaction_rule_gateway=mock_interaction_rule_gateway,
            config=optimization_config_legacy,
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

            # Simulate CLI arguments
            args = [
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
            ]

            with patch("sys.stdout", new=StringIO()):
                controller.run(args)

        # Verify interaction rules gateway was used
        mock_interaction_rule_gateway.get_rules.assert_called_once()
        mock_presenter.present.assert_called_once()

    def test_optimize_command_with_parallel_enabled(self, optimization_config_legacy):
        """Test optimization with parallel candidate generation enabled."""
        # Setup mocks
        mock_field_gateway = Mock()
        mock_crop_gateway = Mock()
        mock_weather_gateway = Mock()
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
        mock_field_gateway.get_all.return_value = [field1]

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
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()
        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )
        crop_req1 = CropProfile(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_gateway.get_all.return_value = [crop_req1]
        
        # Setup internal state for save/get operations (used by growth_period_optimizer)
        saved_profile = None
        def save_profile(profile):
            nonlocal saved_profile
            saved_profile = profile
        def get_profile():
            return saved_profile if saved_profile else crop_req1
        
        mock_crop_gateway.save.side_effect = save_profile
        mock_crop_gateway.get.side_effect = get_profile

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
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            config=optimization_config_legacy,
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
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
                "--enable-parallel",
            ]

            with patch("sys.stdout", new=StringIO()):
                controller.run(args)

        # Verify presenter was called
        mock_presenter.present.assert_called_once()

    def test_optimize_command_with_local_search_disabled(self, optimization_config_legacy):
        """Test optimization with local search disabled."""
        # Setup mocks
        mock_field_gateway = Mock()
        mock_crop_gateway = Mock()
        mock_weather_gateway = Mock()
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
        mock_field_gateway.get_all.return_value = [field1]

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
            max_temperature=42.0,
        )
        sunshine_profile = SunshineProfile()
        stage_req = StageRequirement(
            stage=stage,
            temperature=temp_profile,
            sunshine=sunshine_profile,
            thermal=ThermalRequirement(required_gdd=100.0),
        )
        crop_req1 = CropProfile(
            crop=crop1, stage_requirements=[stage_req]
        )
        mock_crop_gateway.get_all.return_value = [crop_req1]
        
        # Setup internal state for save/get operations (used by growth_period_optimizer)
        saved_profile = None
        def save_profile(profile):
            nonlocal saved_profile
            saved_profile = profile
        def get_profile():
            return saved_profile if saved_profile else crop_req1
        
        mock_crop_gateway.save.side_effect = save_profile
        mock_crop_gateway.get.side_effect = get_profile

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
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            config=optimization_config_legacy,
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
                "--fields-file", str(fields_file),
                "--crops-file", str(crops_file),
                "--planning-start", "2024-04-01",
                "--planning-end", "2024-10-31",
                "--weather-file", "test_weather.json",
                "--disable-local-search",
            ]

            with patch("sys.stdout", new=StringIO()):
                controller.run(args)

        # Verify presenter was called
        mock_presenter.present.assert_called_once()

    def test_flag_transfer_with_default_filtering_enabled(self, optimization_config_legacy):
        """Test that filter_redundant_candidates=True is passed by default."""
        # Setup mocks
        mock_field_gateway = Mock()
        mock_crop_gateway = Mock()
        mock_weather_gateway = Mock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        field1 = Field(
            field_id="field_01",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        mock_field_gateway.get_all.return_value = [field1]

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            config=optimization_config_legacy,
        )

        # Create mock args without --no-filter-redundant flag
        args = Namespace(
            planning_start="2024-04-01",
            planning_end="2024-10-31",
            objective="maximize_profit",
            format="table",
            no_filter_redundant=False,  # Default: filtering enabled
        )

        # Mock the interactor's execute method to capture the request
        captured_request = None

        def capture_execute(request, **kwargs):
            nonlocal captured_request
            captured_request = request
            # Return mock response
            return MultiFieldCropAllocationResponseDTO(
                optimization_result=MagicMock(),
                field_schedules=[],
            )

        controller.interactor.execute = Mock(side_effect=capture_execute)

        # Execute the command
        controller.handle_optimize_command(args)

        # Verify that the request was created with filter_redundant_candidates=True
        assert captured_request is not None, "Request was not passed to interactor"
        assert captured_request.filter_redundant_candidates is True, \
            "Expected filter_redundant_candidates=True by default"

    def test_flag_transfer_with_filtering_disabled(self, optimization_config_legacy):
        """Test that filter_redundant_candidates=False is passed when --no-filter-redundant is specified."""
        # Setup mocks
        mock_field_gateway = Mock()
        mock_crop_gateway = Mock()
        mock_weather_gateway = Mock()
        mock_presenter = MagicMock()
        mock_presenter.output_format = "table"

        field1 = Field(
            field_id="field_01",
            name="Field 1",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        mock_field_gateway.get_all.return_value = [field1]

        # Create controller
        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            config=optimization_config_legacy,
        )

        # Create mock args with --no-filter-redundant flag
        args = Namespace(
            planning_start="2024-04-01",
            planning_end="2024-10-31",
            objective="maximize_profit",
            format="table",
            no_filter_redundant=True,  # Filtering disabled
        )

        # Mock the interactor's execute method to capture the request
        captured_request = None

        def capture_execute(request, **kwargs):
            nonlocal captured_request
            captured_request = request
            # Return mock response
            return MultiFieldCropAllocationResponseDTO(
                optimization_result=MagicMock(),
                field_schedules=[],
            )

        controller.interactor.execute = Mock(side_effect=capture_execute)

        # Execute the command
        controller.handle_optimize_command(args)

        # Verify that the request was created with filter_redundant_candidates=False
        assert captured_request is not None, "Request was not passed to interactor"
        assert captured_request.filter_redundant_candidates is False, \
            "Expected filter_redundant_candidates=False when --no-filter-redundant is specified"

    def test_argument_parser_includes_no_filter_flag(self):
        """Test that argument parser includes --no-filter-redundant option."""
        # Setup mocks
        mock_field_gateway = MagicMock()
        mock_crop_gateway = MagicMock()
        mock_weather_gateway = MagicMock()
        mock_presenter = MagicMock()
        
        # Create config with legacy strategy
        config = OptimizationConfig(
            candidate_generation_strategy="candidate_pool"
        )

        controller = MultiFieldCropAllocationCliController(
            field_gateway=mock_field_gateway,
            crop_gateway=mock_crop_gateway,
            weather_gateway=mock_weather_gateway,
            presenter=mock_presenter,
            crop_profile_gateway_internal=mock_crop_gateway,
            config=config,
        )

        parser = controller.create_argument_parser()

        # Parse with default (no flag)
        args_default = parser.parse_args([
            "--fields-file", "fields.json",
            "--crops-file", "crops.json",
            "--planning-start", "2024-04-01",
            "--planning-end", "2024-10-31",
            "--weather-file", "weather.json",
        ])
        assert args_default.no_filter_redundant is False

        # Parse with --no-filter-redundant flag
        args_no_filter = parser.parse_args([
            "--fields-file", "fields.json",
            "--crops-file", "crops.json",
            "--planning-start", "2024-04-01",
            "--planning-end", "2024-10-31",
            "--weather-file", "weather.json",
            "--no-filter-redundant",
        ])
        assert args_no_filter.no_filter_redundant is True
