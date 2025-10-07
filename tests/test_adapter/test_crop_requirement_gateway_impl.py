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
    async def test_craft_with_new_flow_success(self):
        """Test craft method using new 3-step flow successfully."""
        # Setup request
        request = CropRequirementCraftRequestDTO(crop_query="トマト アイコ")
        
        # Mock LLM client with new flow method
        self.mock_llm_client.execute_crop_requirement_flow = AsyncMock()
        self.mock_llm_client.execute_crop_requirement_flow.return_value = {
            "flow_status": "completed",
            "crop_info": {
                "name": "トマト",
                "variety": "アイコ"
            },
            "stages": [
                {
                    "stage_name": "播種～育苗完了",
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 25.0,
                        "low_stress_threshold": 8.0,
                        "high_stress_threshold": 30.0,
                        "frost_threshold": 0.0,
                        "sterility_risk_threshold": None
                    },
                    "sunshine": {
                        "minimum_sunshine_hours": 4.0,
                        "target_sunshine_hours": 8.0
                    },
                    "thermal": {
                        "required_gdd": 300.0
                    }
                },
                {
                    "stage_name": "育苗完了～開花",
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 26.0,
                        "low_stress_threshold": 10.0,
                        "high_stress_threshold": 30.0,
                        "frost_threshold": 0.0,
                        "sterility_risk_threshold": None
                    },
                    "sunshine": {
                        "minimum_sunshine_hours": 4.0,
                        "target_sunshine_hours": 8.0
                    },
                    "thermal": {
                        "required_gdd": 400.0
                    }
                }
            ]
        }
        
        # Execute
        result = await self.gateway.craft(request)
        
        # Verify
        assert result.crop.name == "トマト"
        assert result.crop.crop_id == "トマト_アイコ"
        assert len(result.stage_requirements) == 2
        
        # Check first stage
        stage1 = result.stage_requirements[0]
        assert stage1.stage.name == "播種～育苗完了"
        assert stage1.stage.order == 1
        assert stage1.temperature.base_temperature == 10.0
        assert stage1.temperature.optimal_min == 20.0
        assert stage1.temperature.optimal_max == 25.0
        assert stage1.sunshine.minimum_sunshine_hours == 4.0
        assert stage1.sunshine.target_sunshine_hours == 8.0
        assert stage1.thermal.required_gdd == 300.0
        
        # Check second stage
        stage2 = result.stage_requirements[1]
        assert stage2.stage.name == "育苗完了～開花"
        assert stage2.stage.order == 2
        assert stage2.temperature.optimal_max == 26.0
        assert stage2.thermal.required_gdd == 400.0
        
        # Verify LLM client was called
        self.mock_llm_client.execute_crop_requirement_flow.assert_called_once_with("トマト アイコ")
    
    @pytest.mark.asyncio
    async def test_craft_with_new_flow_failure_fallback(self):
        """Test craft method when new flow fails and falls back to original method."""
        # Setup request
        request = CropRequirementCraftRequestDTO(crop_query="トマト アイコ")
        
        # Mock LLM client - new flow fails
        self.mock_llm_client.execute_crop_requirement_flow = AsyncMock()
        self.mock_llm_client.execute_crop_requirement_flow.return_value = {
            "flow_status": "failed",
            "error": "Test error"
        }
        
        # Mock original struct method
        self.mock_llm_client.struct = AsyncMock()
        self.mock_llm_client.struct.return_value = {
            "data": {
                "stages": [
                    {
                        "name": "Default",
                        "order": 1,
                        "temperature": {
                            "base_temperature": 10.0,
                            "optimal_min": 20.0,
                            "optimal_max": 26.0,
                            "low_stress_threshold": 12.0,
                            "high_stress_threshold": 32.0,
                            "frost_threshold": 0.0,
                            "sterility_risk_threshold": 35.0
                        },
                        "sunshine": {
                            "minimum_sunshine_hours": 3.0,
                            "target_sunshine_hours": 6.0
                        },
                        "thermal": {
                            "required_gdd": 400.0
                        }
                    }
                ]
            }
        }
        
        # Execute
        result = await self.gateway.craft(request)
        
        # Verify fallback behavior (should use default stub values)
        assert result.crop.name == "トマト アイコ"
        assert result.crop.crop_id == "トマト アイコ"
        assert len(result.stage_requirements) == 1
        
        stage = result.stage_requirements[0]
        assert stage.stage.name == "Default"
        assert stage.stage.order == 1
        assert stage.temperature.base_temperature == 10.0
        assert stage.temperature.optimal_min == 20.0
        assert stage.temperature.optimal_max == 26.0
    
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
        assert result.crop.crop_id == "トマト アイコ"
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
        request = CropRequirementCraftRequestDTO(crop_query="")
        
        # Mock LLM client
        self.mock_llm_client.execute_crop_requirement_flow = AsyncMock()
        self.mock_llm_client.execute_crop_requirement_flow.return_value = {
            "flow_status": "failed",
            "error": "Empty query"
        }
        
        # Execute
        result = await self.gateway.craft(request)
        
        # Verify stub behavior with empty query
        assert result.crop.name == "Unknown"
        assert result.crop.crop_id == "unknown"
        assert len(result.stage_requirements) == 1
        
        stage = result.stage_requirements[0]
        assert stage.stage.name == "Default"
    
    def test_parse_flow_result_with_complete_data(self):
        """Test _parse_flow_result with complete data."""
        flow_result = {
            "crop_info": {
                "name": "トマト",
                "variety": "アイコ"
            },
            "stages": [
                {
                    "stage_name": "播種～育苗完了",
                    "temperature": {
                        "base_temperature": 10.0,
                        "optimal_min": 20.0,
                        "optimal_max": 25.0,
                        "low_stress_threshold": 8.0,
                        "high_stress_threshold": 30.0,
                        "frost_threshold": 0.0,
                        "sterility_risk_threshold": None
                    },
                    "sunshine": {
                        "minimum_sunshine_hours": 4.0,
                        "target_sunshine_hours": 8.0
                    },
                    "thermal": {
                        "required_gdd": 300.0
                    }
                }
            ]
        }
        
        crop, stage_requirements = self.gateway._parse_flow_result(flow_result)
        
        # Verify crop
        assert isinstance(crop, Crop)
        assert crop.name == "トマト"
        assert crop.crop_id == "トマト_アイコ"
        
        # Verify stage requirements
        assert len(stage_requirements) == 1
        stage_req = stage_requirements[0]
        
        # Verify stage
        assert isinstance(stage_req.stage, GrowthStage)
        assert stage_req.stage.name == "播種～育苗完了"
        assert stage_req.stage.order == 1
        
        # Verify temperature profile
        assert isinstance(stage_req.temperature, TemperatureProfile)
        assert stage_req.temperature.base_temperature == 10.0
        assert stage_req.temperature.optimal_min == 20.0
        assert stage_req.temperature.optimal_max == 25.0
        assert stage_req.temperature.low_stress_threshold == 8.0
        assert stage_req.temperature.high_stress_threshold == 30.0
        assert stage_req.temperature.frost_threshold == 0.0
        assert stage_req.temperature.sterility_risk_threshold is None
        
        # Verify sunshine profile
        assert isinstance(stage_req.sunshine, SunshineProfile)
        assert stage_req.sunshine.minimum_sunshine_hours == 4.0
        assert stage_req.sunshine.target_sunshine_hours == 8.0
        
        # Verify thermal requirement
        assert isinstance(stage_req.thermal, ThermalRequirement)
        assert stage_req.thermal.required_gdd == 300.0
    
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
        assert crop.crop_id == "レタス_サニーレタス"
        
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
        assert crop.crop_id == "トマト_アイコ"
        
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
        assert crop.crop_id == "unknown_default"
        assert len(stage_requirements) == 1
