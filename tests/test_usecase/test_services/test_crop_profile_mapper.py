"""Tests for CropProfileMapper."""

import pytest

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.growth_stage_entity import GrowthStage
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.usecase.services.crop_profile_mapper import CropProfileMapper


@pytest.mark.unit
class TestAggregateToPayload:
    """Tests for aggregate_to_payload method."""
    
    def test_aggregate_to_payload_basic(self):
        """Test basic conversion of aggregate to payload."""
        # Create test entities
        crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            variety="Koshihikari",
            revenue_per_area=10000.0,
            max_revenue=500000.0
        )
        
        stage = GrowthStage(name="Growth", order=1)
        temperature = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=26.0,
            low_stress_threshold=12.0,
            high_stress_threshold=32.0,
            frost_threshold=0.0,
            sterility_risk_threshold=35.0
        )
        sunshine = SunshineProfile(
            minimum_sunshine_hours=3.0,
            target_sunshine_hours=6.0
        )
        thermal = ThermalRequirement(required_gdd=400.0)
        stage_req = StageRequirement(
            stage=stage,
            temperature=temperature,
            sunshine=sunshine,
            thermal=thermal
        )
        
        aggregate = CropProfile(
            crop=crop,
            stage_requirements=[stage_req]
        )
        
        # Convert to payload
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        # Verify crop fields
        assert payload["crop_id"] == "rice"
        assert payload["crop_name"] == "Rice"
        assert payload["variety"] == "Koshihikari"
        assert payload["area_per_unit"] == 0.25
        assert payload["revenue_per_area"] == 10000.0
        assert payload["max_revenue"] == 500000.0
        
        # Verify stages structure
        assert len(payload["stages"]) == 1
        assert payload["stages"][0]["name"] == "Growth"
        assert payload["stages"][0]["order"] == 1
    
    def test_aggregate_to_payload_multiple_stages(self):
        """Test conversion with multiple stages."""
        crop = Crop("wheat", "Wheat", 0.3, revenue_per_area=8000.0)
        
        stages = []
        for i in range(3):
            stage = GrowthStage(name=f"Stage{i+1}", order=i+1)
            temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
            sunshine = SunshineProfile(3.0, 6.0)
            thermal = ThermalRequirement(400.0)
            stage_req = StageRequirement(stage, temperature, sunshine, thermal)
            stages.append(stage_req)
        
        aggregate = CropProfile(crop, stages)
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        assert len(payload["stages"]) == 3
        assert payload["stages"][0]["name"] == "Stage1"
        assert payload["stages"][1]["name"] == "Stage2"
        assert payload["stages"][2]["name"] == "Stage3"
    
    def test_aggregate_to_payload_no_variety(self):
        """Test conversion when variety is None."""
        crop = Crop("corn", "Corn", 0.5, variety=None)
        stage = GrowthStage("Growth", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        aggregate = CropProfile(crop, [stage_req])
        
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        assert payload["variety"] is None
    
    def test_aggregate_to_payload_no_revenue(self):
        """Test conversion when revenue_per_area is None."""
        crop = Crop("barley", "Barley", 0.4, revenue_per_area=None)
        stage = GrowthStage("Growth", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        aggregate = CropProfile(crop, [stage_req])
        
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        assert payload["revenue_per_area"] is None

    def test_aggregate_to_payload_no_max_revenue(self):
        """Test conversion when max_revenue is None."""
        crop = Crop("soybean", "Soybean", 0.3, max_revenue=None)
        stage = GrowthStage("Growth", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        aggregate = CropProfile(crop, [stage_req])
        
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        assert payload["max_revenue"] is None

    def test_aggregate_to_payload_with_max_revenue(self):
        """Test conversion when max_revenue is specified."""
        crop = Crop(
            crop_id="cucumber",
            name="Cucumber",
            area_per_unit=0.4,
            max_revenue=800000.0
        )
        stage = GrowthStage("Growth", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        aggregate = CropProfile(crop, [stage_req])
        
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        assert payload["max_revenue"] == 800000.0


@pytest.mark.unit
class TestStageRequirementToDict:
    """Tests for stage_requirement_to_dict method."""
    
    def test_stage_requirement_to_dict_complete(self):
        """Test conversion of complete stage requirement."""
        stage = GrowthStage(name="Vegetative", order=1)
        temperature = TemperatureProfile(
            base_temperature=10.0,
            optimal_min=20.0,
            optimal_max=26.0,
            low_stress_threshold=12.0,
            high_stress_threshold=32.0,
            frost_threshold=0.0,
            sterility_risk_threshold=35.0
        )
        sunshine = SunshineProfile(
            minimum_sunshine_hours=3.0,
            target_sunshine_hours=6.0
        )
        thermal = ThermalRequirement(required_gdd=400.0)
        
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        result = CropProfileMapper.stage_requirement_to_dict(stage_req)
        
        # Verify stage info
        assert result["name"] == "Vegetative"
        assert result["order"] == 1
        
        # Verify temperature data
        assert result["temperature"]["base_temperature"] == 10.0
        assert result["temperature"]["optimal_min"] == 20.0
        assert result["temperature"]["optimal_max"] == 26.0
        assert result["temperature"]["low_stress_threshold"] == 12.0
        assert result["temperature"]["high_stress_threshold"] == 32.0
        assert result["temperature"]["frost_threshold"] == 0.0
        assert result["temperature"]["sterility_risk_threshold"] == 35.0
        
        # Verify sunshine data
        assert result["sunshine"]["minimum_sunshine_hours"] == 3.0
        assert result["sunshine"]["target_sunshine_hours"] == 6.0
        
        # Verify thermal data
        assert result["thermal"]["required_gdd"] == 400.0
    
    def test_stage_requirement_to_dict_all_keys_present(self):
        """Test that all expected keys are present in the result."""
        stage = GrowthStage("Test", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        
        result = CropProfileMapper.stage_requirement_to_dict(stage_req)
        
        # Check top-level keys
        assert "name" in result
        assert "order" in result
        assert "temperature" in result
        assert "sunshine" in result
        assert "thermal" in result
        
        # Check nested keys
        temp_keys = [
            "base_temperature", "optimal_min", "optimal_max",
            "low_stress_threshold", "high_stress_threshold",
            "frost_threshold", "sterility_risk_threshold"
        ]
        for key in temp_keys:
            assert key in result["temperature"]
        
        assert "minimum_sunshine_hours" in result["sunshine"]
        assert "target_sunshine_hours" in result["sunshine"]
        assert "required_gdd" in result["thermal"]


@pytest.mark.unit
class TestPrivateMethods:
    """Tests for private helper methods."""
    
    def test_temperature_to_dict(self):
        """Test _temperature_to_dict method."""
        temperature = TemperatureProfile(
            base_temperature=15.0,
            optimal_min=22.0,
            optimal_max=28.0,
            low_stress_threshold=14.0,
            high_stress_threshold=34.0,
            frost_threshold=-2.0,
            sterility_risk_threshold=38.0
        )
        
        result = CropProfileMapper._temperature_to_dict(temperature)
        
        assert result["base_temperature"] == 15.0
        assert result["optimal_min"] == 22.0
        assert result["optimal_max"] == 28.0
        assert result["low_stress_threshold"] == 14.0
        assert result["high_stress_threshold"] == 34.0
        assert result["frost_threshold"] == -2.0
        assert result["sterility_risk_threshold"] == 38.0
    
    def test_sunshine_to_dict(self):
        """Test _sunshine_to_dict method."""
        sunshine = SunshineProfile(
            minimum_sunshine_hours=4.0,
            target_sunshine_hours=8.0
        )
        
        result = CropProfileMapper._sunshine_to_dict(sunshine)
        
        assert result["minimum_sunshine_hours"] == 4.0
        assert result["target_sunshine_hours"] == 8.0
    
    def test_thermal_to_dict(self):
        """Test _thermal_to_dict method."""
        thermal = ThermalRequirement(required_gdd=500.0)
        
        result = CropProfileMapper._thermal_to_dict(thermal)
        
        assert result["required_gdd"] == 500.0


@pytest.mark.unit
class TestGroupsFieldHandling:
    """Tests for groups field handling in mapper."""
    
    def test_aggregate_to_payload_with_groups(self):
        """Test conversion when groups field is present."""
        crop = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.5,
            variety="Cherry",
            groups=["Solanaceae", "fruiting_vegetables"]
        )
        
        stage = GrowthStage("Growth", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        aggregate = CropProfile(crop, [stage_req])
        
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        # Verify groups field is present and correct
        assert "groups" in payload
        assert payload["groups"] == ["Solanaceae", "fruiting_vegetables"]
        assert isinstance(payload["groups"], list)
        assert len(payload["groups"]) == 2
    
    def test_aggregate_to_payload_with_single_group(self):
        """Test conversion when groups field has single element (family only)."""
        crop = Crop(
            crop_id="cucumber",
            name="Cucumber",
            area_per_unit=0.4,
            groups=["Cucurbitaceae"]  # Only family
        )
        
        stage = GrowthStage("Growth", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        aggregate = CropProfile(crop, [stage_req])
        
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        # Verify groups field with single element
        assert "groups" in payload
        assert payload["groups"] == ["Cucurbitaceae"]
        assert len(payload["groups"]) == 1
    
    def test_aggregate_to_payload_without_groups(self):
        """Test conversion when groups field is None."""
        crop = Crop(
            crop_id="lettuce",
            name="Lettuce",
            area_per_unit=0.3,
            groups=None
        )
        
        stage = GrowthStage("Growth", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        aggregate = CropProfile(crop, [stage_req])
        
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        # Verify groups field is None
        assert "groups" in payload
        assert payload["groups"] is None
    
    def test_aggregate_to_payload_with_empty_groups(self):
        """Test conversion when groups field is empty list."""
        crop = Crop(
            crop_id="spinach",
            name="Spinach",
            area_per_unit=0.2,
            groups=[]
        )
        
        stage = GrowthStage("Growth", 1)
        temperature = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
        sunshine = SunshineProfile(3.0, 6.0)
        thermal = ThermalRequirement(400.0)
        stage_req = StageRequirement(stage, temperature, sunshine, thermal)
        aggregate = CropProfile(crop, [stage_req])
        
        payload = CropProfileMapper.aggregate_to_payload(aggregate)
        
        # Verify groups field is empty list
        assert "groups" in payload
        assert payload["groups"] == []

