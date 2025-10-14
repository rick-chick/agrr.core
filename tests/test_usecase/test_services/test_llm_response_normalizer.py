"""Tests for LLMResponseNormalizer."""

import pytest

from agrr_core.usecase.services.llm_response_normalizer import LLMResponseNormalizer


@pytest.mark.unit
class TestNormalizeStageNameclass:
    """Tests for normalize_stage_name method."""
    
    def test_normalize_stage_name_english(self):
        """Test normalization of English stage name."""
        data = {"stage_name": "Vegetative"}
        assert LLMResponseNormalizer.normalize_stage_name(data) == "Vegetative"
    
    def test_normalize_stage_name_japanese(self):
        """Test normalization of Japanese stage name."""
        data = {"ステージ名": "栄養成長期"}
        assert LLMResponseNormalizer.normalize_stage_name(data) == "栄養成長期"
    
    def test_normalize_stage_name_period_name(self):
        """Test normalization using period_name field."""
        data = {"period_name": "Growth Period"}
        assert LLMResponseNormalizer.normalize_stage_name(data) == "Growth Period"
    
    def test_normalize_stage_name_short_form(self):
        """Test normalization using short form 'stage'."""
        data = {"stage": "Flowering"}
        assert LLMResponseNormalizer.normalize_stage_name(data) == "Flowering"
    
    def test_normalize_stage_name_generic_name(self):
        """Test normalization using generic 'name' field."""
        data = {"name": "Maturity"}
        assert LLMResponseNormalizer.normalize_stage_name(data) == "Maturity"
    
    def test_normalize_stage_name_fallback(self):
        """Test fallback to default value when no field is found."""
        data = {}
        assert LLMResponseNormalizer.normalize_stage_name(data) == "Unknown Stage"
    
    def test_normalize_stage_name_priority(self):
        """Test that fields are checked in priority order."""
        data = {
            "name": "Generic Name",
            "stage": "Stage Name",
            "stage_name": "Priority Name"
        }
        # stage_name should have highest priority
        assert LLMResponseNormalizer.normalize_stage_name(data) == "Priority Name"


@pytest.mark.unit
class TestNormalizeStageDescription:
    """Tests for normalize_stage_description method."""
    
    def test_normalize_description_english(self):
        """Test normalization of English description."""
        data = {"description": "Growth phase description"}
        assert LLMResponseNormalizer.normalize_stage_description(data) == "Growth phase description"
    
    def test_normalize_description_japanese(self):
        """Test normalization of Japanese description."""
        data = {"管理の重点": "温度管理が重要"}
        assert LLMResponseNormalizer.normalize_stage_description(data) == "温度管理が重要"
    
    def test_normalize_description_period_description(self):
        """Test normalization using period_description."""
        data = {"period_description": "Period desc"}
        assert LLMResponseNormalizer.normalize_stage_description(data) == "Period desc"
    
    def test_normalize_description_fallback(self):
        """Test fallback to empty string when no field is found."""
        data = {}
        assert LLMResponseNormalizer.normalize_stage_description(data) == ""


@pytest.mark.unit
class TestNormalizeGrowthStagesField:
    """Tests for normalize_growth_stages_field method."""
    
    def test_normalize_growth_periods(self):
        """Test normalization of growth_periods field."""
        data = {"growth_periods": [{"name": "Stage1"}, {"name": "Stage2"}]}
        result = LLMResponseNormalizer.normalize_growth_stages_field(data)
        assert len(result) == 2
        assert result[0]["name"] == "Stage1"
    
    def test_normalize_management_stages(self):
        """Test normalization of management_stages field."""
        data = {"management_stages": [{"stage": "MS1"}]}
        result = LLMResponseNormalizer.normalize_growth_stages_field(data)
        assert len(result) == 1
        assert result[0]["stage"] == "MS1"
    
    def test_normalize_japanese_field(self):
        """Test normalization of Japanese field names."""
        data = {"管理ステージ": [{"name": "ステージ1"}]}
        result = LLMResponseNormalizer.normalize_growth_stages_field(data)
        assert len(result) == 1
        assert result[0]["name"] == "ステージ1"
    
    def test_normalize_fallback_empty_list(self):
        """Test fallback to empty list when no field is found."""
        data = {}
        result = LLMResponseNormalizer.normalize_growth_stages_field(data)
        assert result == []


@pytest.mark.unit
class TestNormalizeTemperatureField:
    """Tests for normalize_temperature_field method."""
    
    def test_normalize_flat_structure(self):
        """Test normalization of flat temperature structure."""
        data = {
            "temperature": {
                "base_temperature": 10.0,
                "optimal_min": 20.0,
                "optimal_max": 26.0,
                "low_stress_threshold": 12.0,
                "high_stress_threshold": 32.0,
                "frost_threshold": 0.0,
                "sterility_risk_threshold": 35.0,
            }
        }
        result = LLMResponseNormalizer.normalize_temperature_field(data)
        assert result["base_temperature"] == 10.0
        assert result["optimal_min"] == 20.0
        assert result["optimal_max"] == 26.0
        assert result["low_stress_threshold"] == 12.0
        assert result["high_stress_threshold"] == 32.0
        assert result["frost_threshold"] == 0.0
        assert result["sterility_risk_threshold"] == 35.0
    
    def test_normalize_nested_temperature_range(self):
        """Test normalization of nested temperature range structure."""
        data = {
            "temperature": {
                "base_temperature": 10.0,
                "optimal_temperature_range": {
                    "night": 18.0,
                    "day": 25.0
                },
                "low_temperature_stress_threshold": 12.0,
                "high_temperature_stress_threshold": 32.0,
                "frost_damage_risk_temperature": 0.0,
                "high_temperature_damage_threshold": 35.0,
            }
        }
        result = LLMResponseNormalizer.normalize_temperature_field(data)
        assert result["base_temperature"] == 10.0
        assert result["optimal_min"] == 18.0  # from nested night
        assert result["optimal_max"] == 25.0  # from nested day
        assert result["low_stress_threshold"] == 12.0
        assert result["high_stress_threshold"] == 32.0
        assert result["frost_threshold"] == 0.0
        assert result["sterility_risk_threshold"] == 35.0
    
    def test_normalize_default_values(self):
        """Test that default values are used when fields are missing."""
        data = {"temperature": {}}
        result = LLMResponseNormalizer.normalize_temperature_field(data)
        assert result["base_temperature"] == 10.0
        assert result["optimal_min"] == 20.0
        assert result["optimal_max"] == 26.0
        assert result["low_stress_threshold"] == 12.0
        assert result["high_stress_threshold"] == 32.0
        assert result["frost_threshold"] == 0.0
        assert result["sterility_risk_threshold"] == 35.0
    
    def test_normalize_missing_temperature_key(self):
        """Test when temperature key is completely missing."""
        data = {}
        result = LLMResponseNormalizer.normalize_temperature_field(data)
        # Should return defaults
        assert result["base_temperature"] == 10.0
        assert result["optimal_min"] == 20.0


@pytest.mark.unit
class TestNormalizeSunshineField:
    """Tests for normalize_sunshine_field method."""
    
    def test_normalize_sunshine_standard(self):
        """Test normalization of standard sunshine field."""
        data = {
            "sunshine": {
                "minimum_sunshine_hours": 3.0,
                "target_sunshine_hours": 6.0,
            }
        }
        result = LLMResponseNormalizer.normalize_sunshine_field(data)
        assert result["minimum_sunshine_hours"] == 3.0
        assert result["target_sunshine_hours"] == 6.0
    
    def test_normalize_sunlight_requirements(self):
        """Test normalization of sunlight_requirements field."""
        data = {
            "sunlight_requirements": {
                "minimum_sunlight_hours": 4.0,
                "target_sunlight_hours": 7.0,
            }
        }
        result = LLMResponseNormalizer.normalize_sunshine_field(data)
        assert result["minimum_sunshine_hours"] == 4.0
        assert result["target_sunshine_hours"] == 7.0
    
    def test_normalize_default_values(self):
        """Test that default values are used when fields are missing."""
        data = {}
        result = LLMResponseNormalizer.normalize_sunshine_field(data)
        assert result["minimum_sunshine_hours"] == 3.0
        assert result["target_sunshine_hours"] == 6.0


@pytest.mark.unit
class TestNormalizeThermalField:
    """Tests for normalize_thermal_field method."""
    
    def test_normalize_thermal_standard(self):
        """Test normalization of standard thermal field."""
        data = {
            "thermal": {
                "required_gdd": 400.0,
            }
        }
        result = LLMResponseNormalizer.normalize_thermal_field(data)
        assert result["required_gdd"] == 400.0
    
    def test_normalize_accumulated_temperature(self):
        """Test normalization of accumulated_temperature field."""
        data = {
            "accumulated_temperature": {
                "required_gdd": 500.0,
            }
        }
        result = LLMResponseNormalizer.normalize_thermal_field(data)
        assert result["required_gdd"] == 500.0
    
    def test_normalize_default_value(self):
        """Test that default value is used when field is missing."""
        data = {}
        result = LLMResponseNormalizer.normalize_thermal_field(data)
        assert result["required_gdd"] == 400.0

