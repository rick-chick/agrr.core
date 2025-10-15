"""Integration test for harvest_start_gdd data flow through optimization commands.

This test verifies that harvest_start_gdd is correctly transmitted through:
1. JSON file → CropProfileFileGateway → Entity
2. Entity → CropProfileMapper → JSON output
3. Full round-trip for optimize-period and allocate commands
"""

import pytest
import json
import tempfile
import os
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway as CropProfileFileGateway
from agrr_core.framework.repositories.file_repository import FileRepository
from agrr_core.usecase.services.crop_profile_mapper import CropProfileMapper


@pytest.mark.integration
class TestHarvestStartGddDataFlow:
    """Test harvest_start_gdd data flow through optimization commands."""
    
    @pytest.mark.asyncio
    async def test_json_to_entity_with_harvest_start_gdd(self):
        """Test loading crop profile with harvest_start_gdd from JSON file."""
        # Create temporary JSON file
        profile_data = {
            "crop": {
                "crop_id": "eggplant",
                "name": "Eggplant",
                "variety": "Japanese",
                "area_per_unit": 0.5,
                "revenue_per_area": 800,
                "max_revenue": None,
                "groups": ["Solanaceae"]
            },
            "stage_requirements": [
                {
                    "stage": {"name": "Seedling", "order": 1},
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 30.0,
                        "low_stress_threshold": 15.0,
                        "high_stress_threshold": 32.0,
                        "frost_threshold": 0.0,
                        "sterility_risk_threshold": None,
                        "max_temperature": 35.0
                    },
                    "thermal": {
                        "required_gdd": 300.0
                    },
                    "sunshine": {
                        "minimum_sunshine_hours": 6.0,
                        "target_sunshine_hours": 8.0
                    }
                },
                {
                    "stage": {"name": "Harvest", "order": 2},
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 30.0,
                        "low_stress_threshold": 12.0,
                        "high_stress_threshold": 32.0,
                        "frost_threshold": 0.0,
                        "sterility_risk_threshold": 30.0,
                        "max_temperature": 35.0
                    },
                    "thermal": {
                        "required_gdd": 2200.0,
                        "harvest_start_gdd": 200.0
                    },
                    "sunshine": {
                        "minimum_sunshine_hours": 6.0,
                        "target_sunshine_hours": 8.0
                    }
                }
            ]
        }
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(profile_data, f)
            temp_file = f.name
        
        try:
            # Load profile from file
            file_repo = FileRepository()
            crop_profile_repo = CropProfileFileGateway(file_repo, temp_file)
            profile = await crop_profile_repo.get()
            
            # Verify crop
            assert profile.crop.crop_id == "eggplant"
            assert profile.crop.name == "Eggplant"
            
            # Verify seedling stage (no harvest_start_gdd)
            seedling_stage = profile.stage_requirements[0]
            assert seedling_stage.stage.name == "Seedling"
            assert seedling_stage.thermal.required_gdd == 300.0
            assert seedling_stage.thermal.harvest_start_gdd is None
            
            # Verify harvest stage (with harvest_start_gdd)
            harvest_stage = profile.stage_requirements[1]
            assert harvest_stage.stage.name == "Harvest"
            assert harvest_stage.thermal.required_gdd == 2200.0
            assert harvest_stage.thermal.harvest_start_gdd == 200.0
            
            # Verify is_harvest_started() method
            assert not harvest_stage.thermal.is_harvest_started(100.0)
            assert harvest_stage.thermal.is_harvest_started(200.0)
            assert harvest_stage.thermal.is_harvest_started(1000.0)
            assert not harvest_stage.thermal.is_met(200.0)
            assert harvest_stage.thermal.is_met(2200.0)
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_entity_to_json_with_harvest_start_gdd(self):
        """Test converting crop profile entity to JSON with harvest_start_gdd."""
        # Create crop
        crop = Crop(
            "eggplant", "Eggplant", 0.5,
            variety="Japanese",
            revenue_per_area=800,
            groups=["Solanaceae"]
        )
        
        # Create stage requirements
        stage1 = GrowthStage("Seedling", 1)
        temp1 = TemperatureProfile(10.0, 20.0, 30.0, 15.0, 32.0, 0.0, 35.0, None)
        sun1 = SunshineProfile(6.0, 8.0)
        thermal1 = ThermalRequirement(300.0)  # No harvest_start_gdd
        sr1 = StageRequirement(stage1, temp1, sun1, thermal1)
        
        stage2 = GrowthStage("Harvest", 2)
        temp2 = TemperatureProfile(10.0, 20.0, 30.0, 12.0, 32.0, 0.0, 35.0, 30.0)
        sun2 = SunshineProfile(6.0, 8.0)
        thermal2 = ThermalRequirement(2200.0, harvest_start_gdd=200.0)
        sr2 = StageRequirement(stage2, temp2, sun2, thermal2)
        
        # Create profile
        profile = CropProfile(crop, [sr1, sr2])
        
        # Convert to JSON format
        result = CropProfileMapper.to_crop_profile_format(profile)
        
        # Verify crop
        assert result['crop']['crop_id'] == "eggplant"
        assert result['crop']['name'] == "Eggplant"
        
        # Verify seedling stage (no harvest_start_gdd)
        seedling = result['stage_requirements'][0]
        assert seedling['stage']['name'] == "Seedling"
        assert seedling['thermal']['required_gdd'] == 300.0
        assert 'harvest_start_gdd' not in seedling['thermal']
        
        # Verify harvest stage (with harvest_start_gdd)
        harvest = result['stage_requirements'][1]
        assert harvest['stage']['name'] == "Harvest"
        assert harvest['thermal']['required_gdd'] == 2200.0
        assert 'harvest_start_gdd' in harvest['thermal']
        assert harvest['thermal']['harvest_start_gdd'] == 200.0
    
    @pytest.mark.asyncio
    async def test_round_trip_json_entity_json(self):
        """Test full round-trip: JSON → Entity → JSON."""
        # Original JSON data
        original_data = {
            "crop": {
                "crop_id": "eggplant",
                "name": "Eggplant",
                "variety": "Japanese",
                "area_per_unit": 0.5,
                "revenue_per_area": 800,
                "max_revenue": None,
                "groups": ["Solanaceae"]
            },
            "stage_requirements": [
                {
                    "stage": {"name": "Harvest", "order": 1},
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 30.0,
                        "low_stress_threshold": 12.0,
                        "high_stress_threshold": 32.0,
                        "frost_threshold": 0.0,
                        "sterility_risk_threshold": 30.0,
                        "max_temperature": 35.0
                    },
                    "thermal": {
                        "required_gdd": 2200.0,
                        "harvest_start_gdd": 200.0
                    },
                    "sunshine": {
                        "minimum_sunshine_hours": 6.0,
                        "target_sunshine_hours": 8.0
                    }
                }
            ]
        }
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(original_data, f)
            temp_file = f.name
        
        try:
            # Load profile from file (JSON → Entity)
            file_repo = FileRepository()
            crop_profile_repo = CropProfileFileGateway(file_repo, temp_file)
            profile = await crop_profile_repo.get()
            
            # Convert back to JSON (Entity → JSON)
            result = CropProfileMapper.to_crop_profile_format(profile)
            
            # Verify harvest_start_gdd is preserved
            harvest = result['stage_requirements'][0]
            assert harvest['thermal']['required_gdd'] == 2200.0
            assert harvest['thermal']['harvest_start_gdd'] == 200.0
            
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_backward_compatibility_without_harvest_start_gdd(self):
        """Test backward compatibility for profiles without harvest_start_gdd."""
        # Create crop with old format (no harvest_start_gdd)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000)
        
        stage = GrowthStage("Maturity", 1)
        temp = TemperatureProfile(10.0, 20.0, 30.0, 12.0, 32.0, 0.0, 35.0, None)
        sun = SunshineProfile(4.0, 8.0)
        thermal = ThermalRequirement(800.0)  # No harvest_start_gdd
        sr = StageRequirement(stage, temp, sun, thermal)
        
        profile = CropProfile(crop, [sr])
        
        # Convert to JSON format
        result = CropProfileMapper.to_crop_profile_format(profile)
        
        # Verify harvest_start_gdd is not in output
        maturity = result['stage_requirements'][0]
        assert maturity['thermal']['required_gdd'] == 800.0
        assert 'harvest_start_gdd' not in maturity['thermal']
        
        # Verify is_harvest_started() behaves like is_met()
        assert not thermal.is_harvest_started(700.0)
        assert thermal.is_harvest_started(800.0)
        assert not thermal.is_met(700.0)
        assert thermal.is_met(800.0)

