"""Tests for CropRequirementGatewayImpl."""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from agrr_core.adapter.gateways.crop_requirement_gateway_impl import CropRequirementGatewayImpl
from agrr_core.usecase.dto.crop_requirement_craft_request_dto import CropRequirementCraftRequestDTO
from agrr_core.entity import Crop, GrowthStage, TemperatureProfile, SunshineProfile, ThermalRequirement, StageRequirement


class TestCropRequirementGatewayImpl:
    """Test cases for CropRequirementGatewayImpl."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_client = Mock()
        self.gateway = CropRequirementGatewayImpl(llm_client=self.mock_llm_client)
    
    def test_init_with_llm_client(self):
        """Test initialization with LLM client."""
        assert self.gateway.llm_client is not None
        assert self.gateway.llm_client == self.mock_llm_client
    
    def test_init_without_llm_client(self):
        """Test initialization without LLM client."""
        gateway = CropRequirementGatewayImpl(llm_client=None)
        assert gateway.llm_client is None
    
    @pytest.mark.asyncio
    async def test_extract_crop_variety_success(self):
        """Test extract_crop_variety method successfully."""
        # Mock LLM client
        self.mock_llm_client.step1_crop_variety_selection = AsyncMock()
        self.mock_llm_client.step1_crop_variety_selection.return_value = {
            "data": {
                "crop_name": "トマト",
                "variety": "アイコ"
            }
        }
        
        # Execute
        result = await self.gateway.extract_crop_variety("トマト アイコ")
        
        # Verify
        assert result["crop_name"] == "トマト"
        assert result["variety"] == "アイコ"
        self.mock_llm_client.step1_crop_variety_selection.assert_called_once_with("トマト アイコ")
    
    @pytest.mark.asyncio
    async def test_define_growth_stages_success(self):
        """Test define_growth_stages method successfully."""
        # Mock LLM client
        self.mock_llm_client.step2_growth_stage_definition = AsyncMock()
        self.mock_llm_client.step2_growth_stage_definition.return_value = {
            "data": {
                "crop_info": {
                    "name": "トマト",
                    "variety": "アイコ"
                },
                "management_stages": [
                    {
                        "stage_name": "播種～育苗完了",
                        "management_focus": "温度管理",
                        "management_boundary": "本葉展開"
                    }
                ]
            }
        }
        
        # Execute
        result = await self.gateway.define_growth_stages("トマト", "アイコ")
        
        # Verify
        assert result["crop_info"]["name"] == "トマト"
        assert result["crop_info"]["variety"] == "アイコ"
        assert len(result["management_stages"]) == 1
        assert result["management_stages"][0]["stage_name"] == "播種～育苗完了"
        self.mock_llm_client.step2_growth_stage_definition.assert_called_once_with("トマト", "アイコ")
    
    @pytest.mark.asyncio
    async def test_research_stage_requirements_success(self):
        """Test research_stage_requirements method successfully."""
        # Mock LLM client
        self.mock_llm_client.step3_variety_specific_research = AsyncMock()
        self.mock_llm_client.step3_variety_specific_research.return_value = {
            "data": {
                "stage_name": "播種～育苗完了",
                "temperature": {
                    "base_temperature": 10.0,
                    "optimal_min": 20.0,
                    "optimal_max": 25.0,
                    "low_stress_threshold": 8.0,
                    "high_stress_threshold": 30.0,
                    "frost_threshold": 0.0,
                    "sterility_risk_threshold": 35.0
                },
                "sunshine": {
                    "minimum_sunshine_hours": 4.0,
                    "target_sunshine_hours": 8.0
                },
                "thermal": {
                    "required_gdd": 300.0
                }
            }
        }
        
        # Execute
        result = await self.gateway.research_stage_requirements(
            "トマト", "アイコ", "播種～育苗完了", "温度管理"
        )
        
        # Verify
        assert result["stage_name"] == "播種～育苗完了"
        assert result["temperature"]["base_temperature"] == 10.0
        assert result["sunshine"]["minimum_sunshine_hours"] == 4.0
        assert result["thermal"]["required_gdd"] == 300.0
        self.mock_llm_client.step3_variety_specific_research.assert_called_once_with(
            "トマト", "アイコ", "播種～育苗完了", "温度管理"
        )
    
    @pytest.mark.asyncio
    async def test_extract_crop_variety_without_llm_client(self):
        """Test extract_crop_variety without LLM client (fallback)."""
        # Setup gateway without LLM client
        gateway = CropRequirementGatewayImpl(llm_client=None)
        
        # Execute
        result = await gateway.extract_crop_variety("トマト")
        
        # Verify fallback behavior
        assert result["crop_name"] == "トマト"
        assert result["variety"] == "default"
    
    @pytest.mark.asyncio
    async def test_define_growth_stages_without_llm_client(self):
        """Test define_growth_stages without LLM client (fallback)."""
        # Setup gateway without LLM client
        gateway = CropRequirementGatewayImpl(llm_client=None)
        
        # Execute
        result = await gateway.define_growth_stages("トマト", "アイコ")
        
        # Verify fallback behavior
        assert result["crop_info"]["name"] == "トマト"
        assert result["crop_info"]["variety"] == "アイコ"
        assert len(result["growth_periods"]) == 1
        assert result["growth_periods"][0]["period_name"] == "Default"
    
    @pytest.mark.asyncio
    async def test_research_stage_requirements_without_llm_client(self):
        """Test research_stage_requirements without LLM client (fallback)."""
        # Setup gateway without LLM client
        gateway = CropRequirementGatewayImpl(llm_client=None)
        
        # Execute
        result = await gateway.research_stage_requirements("トマト", "アイコ", "播種", "温度管理")
        
        # Verify fallback behavior (does not include stage_name in result)
        assert "temperature" in result
        assert result["temperature"]["base_temperature"] == 10.0
        assert result["sunshine"]["minimum_sunshine_hours"] == 3.0
        assert result["thermal"]["required_gdd"] == 400.0
    
    @pytest.mark.asyncio
    async def test_craft_without_llm_client(self):
        """Test craft method without LLM client (stub fallback)."""
        # Setup gateway without LLM client
        gateway = CropRequirementGatewayImpl(llm_client=None)
        request = CropRequirementCraftRequestDTO(crop_query="トマト アイコ")
        
        # Execute
        result = await gateway.craft(request)
        
        # Verify stub behavior
        assert result.crop.name == "トマト アイコ"
        assert result.crop.crop_id == "トマト アイコ".lower()  # crop_name (lowercase)
        assert result.crop.variety is None  # "default" is converted to None
        assert len(result.stage_requirements) == 1
        
        stage = result.stage_requirements[0]
        assert stage.stage.name == "Default"
        assert stage.stage.order == 1
        assert stage.temperature.base_temperature == 10.0
        assert stage.temperature.optimal_min == 20.0
        assert stage.temperature.optimal_max == 26.0
        assert stage.sunshine.minimum_sunshine_hours == 3.0
        assert stage.sunshine.target_sunshine_hours == 6.0
        assert stage.thermal.required_gdd == 400.0
    
    @pytest.mark.asyncio
    async def test_craft_with_empty_query(self):
        """Test craft method with empty query."""
        # Setup gateway without LLM client for fallback testing
        gateway = CropRequirementGatewayImpl(llm_client=None)
        request = CropRequirementCraftRequestDTO(crop_query="")
        
        # Execute (uses fallback)
        result = await gateway.craft(request)
        
        # Verify stub behavior with empty query
        # Empty query results in crop_name="" and variety="default"
        assert result.crop.name == ""
        assert result.crop.crop_id == ""  # crop_name (lowercase, empty)
        assert result.crop.variety is None  # "default" is converted to None
        assert len(result.stage_requirements) == 1
        
        stage = result.stage_requirements[0]
        assert stage.stage.name == "Default"
    
    def test_parse_flow_result_with_complete_data(self):
        """Test _parse_flow_result with complete data (Step 2 format - no temperature/sunshine/thermal yet)."""
        flow_result = {
            "crop_info": {
                "name": "トマト",
                "variety": "アイコ"
            },
            "stages": [
                {
                    "stage_name": "播種～育苗完了",
                    # Step 2 format: no temperature, sunshine, thermal data yet
                }
            ]
        }
        
        crop, stage_requirements = self.gateway._parse_flow_result(flow_result)
        
        # Verify crop
        assert isinstance(crop, Crop)
        assert crop.name == "トマト"
        assert crop.crop_id == "トマト".lower()
        assert crop.variety == "アイコ"
        
        # Verify stage requirements
        assert len(stage_requirements) == 1
        stage_req = stage_requirements[0]
        
        # Verify stage
        assert isinstance(stage_req.stage, GrowthStage)
        assert stage_req.stage.name == "播種～育苗完了"
        assert stage_req.stage.order == 1
        
        # Verify default temperature profile (Step 2 doesn't have temperature data yet)
        assert isinstance(stage_req.temperature, TemperatureProfile)
        assert stage_req.temperature.base_temperature == 10.0
        assert stage_req.temperature.optimal_min == 20.0
        assert stage_req.temperature.optimal_max == 26.0
        assert stage_req.temperature.low_stress_threshold == 12.0
        assert stage_req.temperature.high_stress_threshold == 32.0
        assert stage_req.temperature.frost_threshold == 0.0
        assert stage_req.temperature.sterility_risk_threshold == 35.0
        
        # Verify default sunshine profile
        assert isinstance(stage_req.sunshine, SunshineProfile)
        assert stage_req.sunshine.minimum_sunshine_hours == 3.0
        assert stage_req.sunshine.target_sunshine_hours == 6.0
        
        # Verify default thermal requirement
        assert isinstance(stage_req.thermal, ThermalRequirement)
        assert stage_req.thermal.required_gdd == 400.0
    
    def test_parse_flow_result_with_missing_data(self):
        """Test _parse_flow_result with missing data (should use defaults)."""
        flow_result = {
            "crop_info": {
                "name": "レタス",
                "variety": "サニーレタス"
            },
            "stages": [
                {
                    "stage_name": "播種～収穫適期",
                    # Missing temperature, sunshine, thermal data
                }
            ]
        }
        
        crop, stage_requirements = self.gateway._parse_flow_result(flow_result)
        
        # Verify crop
        assert crop.name == "レタス"
        assert crop.crop_id == "レタス".lower()
        assert crop.variety == "サニーレタス"
        
        # Verify stage requirements with defaults
        assert len(stage_requirements) == 1
        stage_req = stage_requirements[0]
        
        assert stage_req.stage.name == "播種～収穫適期"
        assert stage_req.stage.order == 1
        
        # Should use default values for missing data
        assert stage_req.temperature.base_temperature == 10.0
        assert stage_req.temperature.optimal_min == 20.0
        assert stage_req.temperature.optimal_max == 26.0
        assert stage_req.sunshine.minimum_sunshine_hours == 3.0
        assert stage_req.sunshine.target_sunshine_hours == 6.0
        assert stage_req.thermal.required_gdd == 400.0
    
    def test_parse_flow_result_with_empty_stages(self):
        """Test _parse_flow_result with empty stages."""
        flow_result = {
            "crop_info": {
                "name": "トマト",
                "variety": "アイコ"
            },
            "stages": []
        }
        
        crop, stage_requirements = self.gateway._parse_flow_result(flow_result)
        
        # Verify crop
        assert crop.name == "トマト"
        assert crop.crop_id == "トマト".lower()
        assert crop.variety == "アイコ"
        
        # Verify empty stage requirements
        assert len(stage_requirements) == 0
    
    def test_parse_flow_result_with_missing_crop_info(self):
        """Test _parse_flow_result with missing crop info."""
        flow_result = {
            "stages": [
                {
                    "stage_name": "播種～育苗完了",
                    "temperature": {"base_temperature": 10.0},
                    "sunshine": {"minimum_sunshine_hours": 4.0},
                    "thermal": {"required_gdd": 300.0}
                }
            ]
        }
        
        crop, stage_requirements = self.gateway._parse_flow_result(flow_result)
        
        # Should use defaults for missing crop info
        assert crop.name == "Unknown"
        assert crop.crop_id == "unknown"
        assert crop.variety is None  # "default" is converted to None
        assert len(stage_requirements) == 1
    
    @pytest.mark.asyncio
    async def test_load_from_file_with_revenue_per_area(self):
        """Test loading crop requirement from JSON file with revenue_per_area field."""
        # Create a test JSON file with revenue_per_area
        import tempfile
        import json
        
        test_data = {
            "crop": {
                "crop_id": "rice",
                "name": "Rice",
                "area_per_unit": 0.25,
                "variety": "Koshihikari",
                "revenue_per_area": 50000.0
            },
            "stage_requirements": [
                {
                    "stage": {"name": "Growth", "order": 1},
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 25.0,
                        "low_stress_threshold": 15.0,
                        "high_stress_threshold": 30.0,
                        "frost_threshold": 5.0
                    },
                    "sunshine": {
                        "min_hours_per_day": 8.0,
                        "optimal_hours_per_day": 10.0
                    },
                    "thermal": {
                        "required_gdd": 100.0
                    }
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file_path = f.name
        
        try:
            # Create a mock file repository
            mock_file_repo = Mock()
            mock_file_repo.read = AsyncMock(return_value=json.dumps(test_data))
            
            # Create gateway with file repository
            gateway = CropRequirementGatewayImpl(llm_client=None, file_repository=mock_file_repo)
            
            # Load from file
            result = await gateway.get(temp_file_path)
            
            # Verify crop with revenue_per_area
            assert result.crop.crop_id == "rice"
            assert result.crop.name == "Rice"
            assert result.crop.area_per_unit == 0.25
            assert result.crop.variety == "Koshihikari"
            assert result.crop.revenue_per_area == 50000.0
            
            # Verify stage requirements
            assert len(result.stage_requirements) == 1
        finally:
            # Clean up
            import os
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_load_from_file_without_revenue_per_area(self):
        """Test loading crop requirement from JSON file without revenue_per_area field (backward compatibility)."""
        # Create a test JSON file without revenue_per_area
        import tempfile
        import json
        
        test_data = {
            "crop": {
                "crop_id": "tomato",
                "name": "Tomato",
                "area_per_unit": 0.5,
                "variety": "Cherry"
            },
            "stage_requirements": [
                {
                    "stage": {"name": "Growth", "order": 1},
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 28.0,
                        "low_stress_threshold": 15.0,
                        "high_stress_threshold": 35.0,
                        "frost_threshold": 2.0
                    },
                    "sunshine": {
                        "min_hours_per_day": 6.0,
                        "optimal_hours_per_day": 8.0
                    },
                    "thermal": {
                        "required_gdd": 150.0
                    }
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file_path = f.name
        
        try:
            # Create a mock file repository
            mock_file_repo = Mock()
            mock_file_repo.read = AsyncMock(return_value=json.dumps(test_data))
            
            # Create gateway with file repository
            gateway = CropRequirementGatewayImpl(llm_client=None, file_repository=mock_file_repo)
            
            # Load from file
            result = await gateway.get(temp_file_path)
            
            # Verify crop without revenue_per_area (should be None)
            assert result.crop.crop_id == "tomato"
            assert result.crop.name == "Tomato"
            assert result.crop.area_per_unit == 0.5
            assert result.crop.variety == "Cherry"
            assert result.crop.revenue_per_area is None
            
            # Verify stage requirements
            assert len(result.stage_requirements) == 1
        finally:
            # Clean up
            import os
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_extract_crop_economics_success(self):
        """Test extract_crop_economics method successfully."""
        # Mock LLM client
        self.mock_llm_client.extract_crop_economics = AsyncMock()
        self.mock_llm_client.extract_crop_economics.return_value = {
            "data": {
                "area_per_unit": 0.5,
                "revenue_per_area": 3000.0
            }
        }
        
        # Execute
        result = await self.gateway.extract_crop_economics("トマト", "アイコ")
        
        # Verify
        assert result["area_per_unit"] == 0.5
        assert result["revenue_per_area"] == 3000.0
        self.mock_llm_client.extract_crop_economics.assert_called_once_with("トマト", "アイコ")
    
    @pytest.mark.asyncio
    async def test_extract_crop_economics_without_llm_client(self):
        """Test extract_crop_economics without LLM client (fallback)."""
        # Setup gateway without LLM client
        gateway = CropRequirementGatewayImpl(llm_client=None)
        
        # Execute
        result = await gateway.extract_crop_economics("トマト", "アイコ")
        
        # Verify fallback behavior
        assert result["area_per_unit"] == 0.25
        assert result["revenue_per_area"] is None
    
    @pytest.mark.asyncio
    async def test_extract_crop_family_success(self):
        """Test extract_crop_family method successfully."""
        # Mock LLM client
        self.mock_llm_client.extract_crop_family = AsyncMock()
        self.mock_llm_client.extract_crop_family.return_value = {
            "data": {
                "family_ja": "ナス科",
                "family_scientific": "Solanaceae"
            }
        }
        
        # Execute
        result = await self.gateway.extract_crop_family("トマト", "アイコ")
        
        # Verify
        assert result["family_ja"] == "ナス科"
        assert result["family_scientific"] == "Solanaceae"
        self.mock_llm_client.extract_crop_family.assert_called_once_with("トマト", "アイコ")
    
    @pytest.mark.asyncio
    async def test_extract_crop_family_without_llm_client(self):
        """Test extract_crop_family without LLM client (fallback)."""
        # Setup gateway without LLM client
        gateway = CropRequirementGatewayImpl(llm_client=None)
        
        # Execute
        result = await gateway.extract_crop_family("トマト", "アイコ")
        
        # Verify fallback behavior
        assert result["family_ja"] is None
        assert result["family_scientific"] is None