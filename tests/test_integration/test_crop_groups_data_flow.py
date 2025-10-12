"""Integration tests for Crop groups field data flow through CLI layers.

This test suite verifies that the groups field is correctly propagated
through all architectural layers: Entity → Mapper → Gateway → CLI output.
"""

import json
import tempfile
from pathlib import Path

import pytest

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_requirement_aggregate_entity import CropRequirementAggregate
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.adapter.mappers.crop_requirement_mapper import CropRequirementMapper
from agrr_core.adapter.gateways.crop_requirement_gateway_impl import CropRequirementGatewayImpl
from agrr_core.framework.repositories.file_repository import FileRepository


class TestCropGroupsDataFlowThroughMapper:
    """Test groups field data flow through Mapper layer."""
    
    def test_crop_with_groups_to_payload(self):
        """Test that Crop with groups is correctly converted to payload by Mapper."""
        # Entity layer: Create Crop with groups
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            variety="Aiko",
            revenue_per_area=50000.0,
            groups=["Solanaceae", "fruiting_vegetables", "warm_season"]
        )
        
        # Create minimal stage requirement
        stage = GrowthStage(name="growth", order=1)
        temp = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=26.0,
            low_stress_threshold=12.0,
            high_stress_threshold=32.0,
            frost_threshold=0.0,
            sterility_risk_threshold=35.0
        )
        sun = SunshineProfile(minimum_sunshine_hours=4.0, target_sunshine_hours=8.0)
        thermal = ThermalRequirement(required_gdd=2000.0)
        stage_req = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
        
        aggregate = CropRequirementAggregate(crop=crop, stage_requirements=[stage_req])
        
        # Adapter layer: Convert to payload using Mapper
        payload = CropRequirementMapper.aggregate_to_payload(aggregate)
        
        # Verify groups field is present and correct in payload
        assert "groups" in payload
        assert payload["groups"] == ["Solanaceae", "fruiting_vegetables", "warm_season"]
        assert payload["crop_id"] == "tomato"
        assert payload["crop_name"] == "Tomato"
        assert payload["area_per_unit"] == 0.5
        assert payload["variety"] == "Aiko"
        assert payload["revenue_per_area"] == 50000.0
    
    def test_crop_without_groups_to_payload(self):
        """Test that Crop without groups (None) is handled correctly by Mapper."""
        crop = Crop(
            crop_id="unknown_crop",
            name="Unknown Crop",
            area_per_unit=0.25
        )
        
        stage = GrowthStage(name="growth", order=1)
        temp = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sun = SunshineProfile(4.0, 8.0)
        thermal = ThermalRequirement(2000.0)
        stage_req = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
        
        aggregate = CropRequirementAggregate(crop=crop, stage_requirements=[stage_req])
        payload = CropRequirementMapper.aggregate_to_payload(aggregate)
        
        # groups should be None (not missing)
        assert "groups" in payload
        assert payload["groups"] is None
    
    def test_crop_with_empty_groups_to_payload(self):
        """Test that Crop with empty groups list is handled correctly."""
        crop = Crop(
            crop_id="test_crop",
            name="Test Crop",
            area_per_unit=0.25,
            groups=[]
        )
        
        stage = GrowthStage(name="growth", order=1)
        temp = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sun = SunshineProfile(4.0, 8.0)
        thermal = ThermalRequirement(2000.0)
        stage_req = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
        
        aggregate = CropRequirementAggregate(crop=crop, stage_requirements=[stage_req])
        payload = CropRequirementMapper.aggregate_to_payload(aggregate)
        
        assert "groups" in payload
        assert payload["groups"] == []


class TestCropGroupsDataFlowThroughGateway:
    """Test groups field data flow through Gateway layer (file I/O)."""
    
    @pytest.mark.asyncio
    async def test_save_and_load_crop_with_groups(self):
        """Test that Crop with groups can be saved to and loaded from JSON file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            
            # Create JSON data with groups (Gateway format)
            crop_data = {
                "crop": {
                    "crop_id": "tomato",
                    "name": "Tomato",
                    "variety": "Aiko",
                    "area_per_unit": 0.5,
                    "revenue_per_area": 50000.0,
                    "max_revenue": 1000000.0,
                    "groups": ["Solanaceae", "fruiting_vegetables", "warm_season"]
                },
                "stage_requirements": [
                    {
                        "stage": {
                            "name": "germination",
                            "order": 1
                        },
                        "temperature": {
                            "base_temperature": 10.0,
                            "optimal_min": 20.0,
                            "optimal_max": 30.0,
                            "low_stress_threshold": 15.0,
                            "high_stress_threshold": 35.0,
                            "frost_threshold": 0.0,
                            "sterility_risk_threshold": 40.0
                        },
                        "sunshine": {
                            "minimum_sunshine_hours": 4.0,
                            "target_sunshine_hours": 8.0
                        },
                        "thermal": {
                            "required_gdd": 200.0
                        }
                    }
                ]
            }
            
            # Write JSON
            json.dump(crop_data, f, ensure_ascii=False, indent=2)
        
        try:
            # Load using Gateway
            file_repository = FileRepository()
            gateway = CropRequirementGatewayImpl(
                llm_client=None,
                file_repository=file_repository
            )
            
            aggregate = await gateway.get(str(temp_file))
            
            # Verify groups field was loaded correctly
            assert aggregate.crop.groups is not None
            assert aggregate.crop.groups == ["Solanaceae", "fruiting_vegetables", "warm_season"]
            assert aggregate.crop.crop_id == "tomato"
            assert aggregate.crop.name == "Tomato"
            assert aggregate.crop.variety == "Aiko"
            assert aggregate.crop.area_per_unit == 0.5
            assert aggregate.crop.revenue_per_area == 50000.0
            assert aggregate.crop.max_revenue == 1000000.0
            
        finally:
            # Cleanup
            temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_load_crop_without_groups_field(self):
        """Test loading JSON that doesn't have groups field (backward compatibility)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            
            # Old format without groups (Gateway format)
            crop_data = {
                "crop": {
                    "crop_id": "rice",
                    "name": "Rice",
                    "variety": "Koshihikari",
                    "area_per_unit": 0.25,
                    "revenue_per_area": 30000.0
                },
                "stage_requirements": [
                    {
                        "stage": {
                            "name": "growth",
                            "order": 1
                        },
                        "temperature": {
                            "base_temperature": 10.0,
                            "optimal_min": 20.0,
                            "optimal_max": 30.0,
                            "low_stress_threshold": 15.0,
                            "high_stress_threshold": 35.0,
                            "frost_threshold": 0.0,
                            "sterility_risk_threshold": 40.0
                        },
                        "sunshine": {
                            "minimum_sunshine_hours": 5.0,
                            "target_sunshine_hours": 10.0
                        },
                        "thermal": {
                            "required_gdd": 2400.0
                        }
                    }
                ]
            }
            
            json.dump(crop_data, f, ensure_ascii=False, indent=2)
        
        try:
            file_repository = FileRepository()
            gateway = CropRequirementGatewayImpl(
                llm_client=None,
                file_repository=file_repository
            )
            
            aggregate = await gateway.get(str(temp_file))
            
            # groups should be None for backward compatibility
            assert aggregate.crop.groups is None
            assert aggregate.crop.crop_id == "rice"
            
        finally:
            temp_file.unlink()
    
    @pytest.mark.asyncio
    async def test_roundtrip_crop_with_groups(self):
        """Test complete roundtrip: Entity → Gateway format JSON → Gateway → Entity."""
        # 1. Create original Crop entity with groups
        original_crop = Crop(
            crop_id="eggplant",
            name="Eggplant",
            area_per_unit=0.4,
            variety="Senryo",
            revenue_per_area=40000.0,
            max_revenue=800000.0,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        # 2. Create Gateway-compatible JSON format
        gateway_format = {
            "crop": {
                "crop_id": original_crop.crop_id,
                "name": original_crop.name,
                "area_per_unit": original_crop.area_per_unit,
                "variety": original_crop.variety,
                "revenue_per_area": original_crop.revenue_per_area,
                "max_revenue": original_crop.max_revenue,
                "groups": original_crop.groups
            },
            "stage_requirements": [
                {
                    "stage": {
                        "name": "vegetative",
                        "order": 1
                    },
                    "temperature": {
                        "base_temperature": 12.0,
                        "optimal_min": 22.0,
                        "optimal_max": 28.0,
                        "low_stress_threshold": 15.0,
                        "high_stress_threshold": 32.0,
                        "frost_threshold": 5.0,
                        "sterility_risk_threshold": 35.0
                    },
                    "sunshine": {
                        "minimum_sunshine_hours": 5.0,
                        "target_sunshine_hours": 8.0
                    },
                    "thermal": {
                        "required_gdd": 1800.0
                    }
                }
            ]
        }
        
        # 3. Save to JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
            json.dump(gateway_format, f, ensure_ascii=False, indent=2)
        
        try:
            # 4. Load back using Gateway
            file_repository = FileRepository()
            gateway = CropRequirementGatewayImpl(
                llm_client=None,
                file_repository=file_repository
            )
            
            loaded_aggregate = await gateway.get(str(temp_file))
            
            # 5. Verify all fields including groups
            assert loaded_aggregate.crop.crop_id == original_crop.crop_id
            assert loaded_aggregate.crop.name == original_crop.name
            assert loaded_aggregate.crop.area_per_unit == original_crop.area_per_unit
            assert loaded_aggregate.crop.variety == original_crop.variety
            assert loaded_aggregate.crop.revenue_per_area == original_crop.revenue_per_area
            assert loaded_aggregate.crop.max_revenue == original_crop.max_revenue
            assert loaded_aggregate.crop.groups == original_crop.groups
            
            # Verify groups specifically
            assert loaded_aggregate.crop.groups == ["Solanaceae", "fruiting_vegetables"]
            
        finally:
            temp_file.unlink()


class TestCropGroupsJSONSerializationFormat:
    """Test JSON serialization format of groups field."""
    
    def test_groups_json_format_with_values(self):
        """Test that groups are serialized as JSON array."""
        crop = Crop(
            crop_id="cabbage",
            name="Cabbage",
            area_per_unit=0.3,
            groups=["Brassicaceae", "leafy_vegetables", "cool_season"]
        )
        
        stage = GrowthStage(name="growth", order=1)
        temp = TemperatureProfile(5.0, 15.0, 20.0, 10.0, 25.0, -2.0, 30.0)
        sun = SunshineProfile(4.0, 6.0)
        thermal = ThermalRequirement(1500.0)
        stage_req = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
        
        aggregate = CropRequirementAggregate(crop=crop, stage_requirements=[stage_req])
        payload = CropRequirementMapper.aggregate_to_payload(aggregate)
        
        # Serialize to JSON string
        json_str = json.dumps(payload, ensure_ascii=False)
        
        # Parse back
        parsed = json.loads(json_str)
        
        # Verify groups is a list
        assert isinstance(parsed["groups"], list)
        assert parsed["groups"] == ["Brassicaceae", "leafy_vegetables", "cool_season"]
    
    def test_groups_json_format_with_none(self):
        """Test that None groups are serialized as null."""
        crop = Crop(
            crop_id="test_crop",
            name="Test Crop",
            area_per_unit=0.25,
            groups=None
        )
        
        stage = GrowthStage(name="growth", order=1)
        temp = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sun = SunshineProfile(4.0, 8.0)
        thermal = ThermalRequirement(2000.0)
        stage_req = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
        
        aggregate = CropRequirementAggregate(crop=crop, stage_requirements=[stage_req])
        payload = CropRequirementMapper.aggregate_to_payload(aggregate)
        
        json_str = json.dumps(payload, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        # null in JSON becomes None in Python
        assert parsed["groups"] is None
    
    def test_groups_json_format_with_empty_list(self):
        """Test that empty groups list is serialized as empty array."""
        crop = Crop(
            crop_id="test_crop",
            name="Test Crop",
            area_per_unit=0.25,
            groups=[]
        )
        
        stage = GrowthStage(name="growth", order=1)
        temp = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sun = SunshineProfile(4.0, 8.0)
        thermal = ThermalRequirement(2000.0)
        stage_req = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
        
        aggregate = CropRequirementAggregate(crop=crop, stage_requirements=[stage_req])
        payload = CropRequirementMapper.aggregate_to_payload(aggregate)
        
        json_str = json.dumps(payload, ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert isinstance(parsed["groups"], list)
        assert len(parsed["groups"]) == 0


class TestRealWorldCropGroupsScenarios:
    """Test real-world scenarios with crop groups."""
    
    @pytest.mark.asyncio
    async def test_multiple_crops_with_different_groups(self):
        """Test handling multiple crops with different group configurations."""
        crops_data = [
            {
                "crop_id": "tomato",
                "name": "Tomato",
                "groups": ["Solanaceae", "fruiting_vegetables"],
            },
            {
                "crop_id": "rice",
                "name": "Rice",
                "groups": ["Poaceae", "grains", "high_water_need"],
            },
            {
                "crop_id": "soybean",
                "name": "Soybean",
                "groups": ["Fabaceae", "legumes", "nitrogen_fixing"],
            },
            {
                "crop_id": "unknown",
                "name": "Unknown Crop",
                "groups": None,  # No groups assigned
            }
        ]
        
        for crop_data in crops_data:
            # Create entity
            crop = Crop(
                crop_id=crop_data["crop_id"],
                name=crop_data["name"],
                area_per_unit=0.25,
                groups=crop_data.get("groups")
            )
            
            # Verify groups
            if crop_data.get("groups") is not None:
                assert crop.groups == crop_data["groups"]
            else:
                assert crop.groups is None
            
            # Test mapper conversion
            stage = GrowthStage(name="growth", order=1)
            temp = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
            sun = SunshineProfile(4.0, 8.0)
            thermal = ThermalRequirement(2000.0)
            stage_req = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
            
            aggregate = CropRequirementAggregate(crop=crop, stage_requirements=[stage_req])
            payload = CropRequirementMapper.aggregate_to_payload(aggregate)
            
            assert payload["groups"] == crop_data.get("groups")
    
    def test_crop_groups_for_interaction_rule_matching(self):
        """Test that crop groups can be used for interaction rule matching."""
        # Create crops with specific groups for continuous cultivation detection
        tomato = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        eggplant = Crop(
            crop_id="eggplant",
            name="Eggplant",
            area_per_unit=0.4,
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        rice = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            groups=["Poaceae", "grains"]
        )
        
        # Check for continuous cultivation potential
        # (same family = potential continuous cultivation issue)
        tomato_groups_set = set(tomato.groups)
        eggplant_groups_set = set(eggplant.groups)
        rice_groups_set = set(rice.groups)
        
        # Tomato and Eggplant share "Solanaceae" group
        assert bool(tomato_groups_set & eggplant_groups_set)
        
        # Tomato and Rice don't share any groups
        assert not bool(tomato_groups_set & rice_groups_set)
        
        # Specific check for family-level group
        assert "Solanaceae" in tomato.groups
        assert "Solanaceae" in eggplant.groups
        assert "Solanaceae" not in rice.groups

