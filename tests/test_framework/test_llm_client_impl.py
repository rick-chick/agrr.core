"""Tests for FrameworkLLMClient."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from agrr_core.framework.services.llm_client_impl import FrameworkLLMClient


class TestFrameworkLLMClient:
    """Test cases for FrameworkLLMClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = FrameworkLLMClient()
    
    def test_init(self):
        """Test client initialization."""
        assert isinstance(self.client, FrameworkLLMClient)
    
    @pytest.mark.asyncio
    async def test_struct_with_stub(self):
        """Test struct method with stub fallback."""
        structure = {"name": None, "value": None}
        query = "test query"
        instruction = "test instruction"
        
        result = await self.client.struct(query, structure, instruction)
        
        assert result["provider"] == "stub"
        assert "_query" in result["data"]
        assert "_instruction" in result["data"]
        assert result["data"]["_query"] == query
        assert result["data"]["_instruction"] == instruction
        assert result["structure"] == structure
    
    @pytest.mark.asyncio
    async def test_step1_crop_variety_selection(self):
        """Test Step 1: Crop variety selection."""
        crop_query = "トマト アイコ"
        
        with patch.object(self.client, 'struct', new_callable=AsyncMock) as mock_struct:
            mock_struct.return_value = {
                "data": {
                    "crop_name": "トマト",
                    "variety": "アイコ"
                }
            }
            
            result = await self.client.step1_crop_variety_selection(crop_query)
            
            # Verify struct was called with correct parameters
            mock_struct.assert_called_once()
            call_args = mock_struct.call_args
            assert call_args[0][0] == crop_query
            assert "crop_name" in call_args[0][1]
            assert "variety" in call_args[0][1]
            assert "Extract crop name and variety" in call_args[0][2]
    
    @pytest.mark.asyncio
    async def test_step2_growth_stage_definition(self):
        """Test Step 2: Growth stage definition."""
        crop_name = "トマト"
        variety = "アイコ"
        
        with patch.object(self.client, 'struct', new_callable=AsyncMock) as mock_struct:
            mock_struct.return_value = {
                "data": {
                    "crop_info": {
                        "name": "トマト",
                        "variety": "アイコ"
                    },
                    "growth_stages": [
                        {
                            "stage_name": "播種～育苗完了",
                            "description": "発芽から本葉5-6枚まで"
                        }
                    ]
                }
            }
            
            result = await self.client.step2_growth_stage_definition(crop_name, variety)
            
            # Verify struct was called with correct parameters
            mock_struct.assert_called_once()
            call_args = mock_struct.call_args
            query = call_args[0][0]
            assert "作物の生育ステージ構成調査" in query
            assert crop_name in query
            assert variety in query
            assert "crop_info" in call_args[0][1]
            assert "growth_stages" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_step3_variety_specific_research(self):
        """Test Step 3: Variety-specific requirement research."""
        crop_name = "トマト"
        variety = "アイコ"
        stage_name = "播種～育苗完了"
        stage_description = "発芽から本葉5-6枚まで"
        
        with patch.object(self.client, 'struct', new_callable=AsyncMock) as mock_struct:
            mock_struct.return_value = {
                "data": {
                    "stage_name": stage_name,
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
            }
            
            result = await self.client.step3_variety_specific_research(
                crop_name, variety, stage_name, stage_description
            )
            
            # Verify struct was called with correct parameters
            mock_struct.assert_called_once()
            call_args = mock_struct.call_args
            query = call_args[0][0]
            assert "詳細要件調査・構造化" in query
            assert crop_name in query
            assert variety in query
            assert stage_name in query
            assert stage_description in query
            
            structure = call_args[0][1]
            assert "stage_name" in structure
            assert "temperature" in structure
            assert "sunshine" in structure
            assert "thermal" in structure
            assert "base_temperature" in structure["temperature"]
            assert "optimal_min" in structure["temperature"]
            assert "minimum_sunshine_hours" in structure["sunshine"]
            assert "required_gdd" in structure["thermal"]
    
    @pytest.mark.asyncio
    async def test_execute_crop_requirement_flow_success(self):
        """Test complete flow execution with success."""
        crop_query = "トマト アイコ"
        
        # Mock the step methods
        with patch.object(self.client, 'step1_crop_variety_selection', new_callable=AsyncMock) as mock_step1, \
             patch.object(self.client, 'step2_growth_stage_definition', new_callable=AsyncMock) as mock_step2, \
             patch.object(self.client, 'step3_variety_specific_research', new_callable=AsyncMock) as mock_step3:
            
            # Setup mock returns
            mock_step1.return_value = {
                "data": {
                    "crop_name": "トマト",
                    "variety": "アイコ"
                }
            }
            
            mock_step2.return_value = {
                "data": {
                    "crop_info": {
                        "name": "トマト",
                        "variety": "アイコ"
                    },
                    "growth_stages": [
                        {
                            "stage_name": "播種～育苗完了",
                            "description": "発芽から本葉5-6枚まで"
                        },
                        {
                            "stage_name": "育苗完了～開花",
                            "description": "定植後、茎葉成長、第1花房開花まで"
                        }
                    ]
                }
            }
            
            mock_step3.return_value = {
                "data": {
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
            }
            
            result = await self.client.execute_crop_requirement_flow(crop_query)
            
            # Verify the flow execution
            assert result["flow_status"] == "completed"
            assert result["crop_info"]["name"] == "トマト"
            assert result["crop_info"]["variety"] == "アイコ"
            assert len(result["stages"]) == 2
            
            # Verify all steps were called
            mock_step1.assert_called_once_with(crop_query)
            mock_step2.assert_called_once_with("トマト", "アイコ")
            assert mock_step3.call_count == 2  # Called for each stage
    
    @pytest.mark.asyncio
    async def test_execute_crop_requirement_flow_failure(self):
        """Test complete flow execution with failure."""
        crop_query = "invalid crop"
        
        # Mock step1 to raise an exception
        with patch.object(self.client, 'step1_crop_variety_selection', new_callable=AsyncMock) as mock_step1:
            mock_step1.side_effect = Exception("Test error")
            
            result = await self.client.execute_crop_requirement_flow(crop_query)
            
            # Verify error handling
            assert result["flow_status"] == "failed"
            assert "error" in result
            assert result["error"] == "Test error"
            assert result["crop_info"]["name"] == "Unknown"
            assert result["crop_info"]["variety"] == "default"
            assert result["stages"] == []
    
    @pytest.mark.asyncio
    async def test_execute_crop_requirement_flow_with_empty_stages(self):
        """Test flow execution when no growth stages are returned."""
        crop_query = "トマト アイコ"
        
        with patch.object(self.client, 'step1_crop_variety_selection', new_callable=AsyncMock) as mock_step1, \
             patch.object(self.client, 'step2_growth_stage_definition', new_callable=AsyncMock) as mock_step2:
            
            mock_step1.return_value = {
                "data": {
                    "crop_name": "トマト",
                    "variety": "アイコ"
                }
            }
            
            mock_step2.return_value = {
                "data": {
                    "crop_info": {
                        "name": "トマト",
                        "variety": "アイコ"
                    },
                    "growth_stages": []  # Empty stages
                }
            }
            
            result = await self.client.execute_crop_requirement_flow(crop_query)
            
            # Verify handling of empty stages
            assert result["flow_status"] == "completed"
            assert result["crop_info"]["name"] == "トマト"
            assert result["crop_info"]["variety"] == "アイコ"
            assert result["stages"] == []
    
    def test_step1_query_format(self):
        """Test that Step 1 query format is correct."""
        crop_query = "トマト アイコ"
        
        # Test the query format by checking the method structure
        method = self.client.step1_crop_variety_selection
        assert method.__doc__ is not None
        assert "Extract crop name and variety" in method.__doc__
    
    def test_step2_query_format(self):
        """Test that Step 2 query format is correct."""
        # Test the query format by checking the method structure
        method = self.client.step2_growth_stage_definition
        assert method.__doc__ is not None
        assert "Define growth stages" in method.__doc__
    
    def test_step3_query_format(self):
        """Test that Step 3 query format is correct."""
        # Test the query format by checking the method structure
        method = self.client.step3_variety_specific_research
        assert method.__doc__ is not None
        assert "Research variety-specific requirements" in method.__doc__
    
    def test_flow_method_availability(self):
        """Test that the flow method is available."""
        assert hasattr(self.client, 'execute_crop_requirement_flow')
        assert callable(getattr(self.client, 'execute_crop_requirement_flow'))
        
        method = self.client.execute_crop_requirement_flow
        assert method.__doc__ is not None
        assert "Execute the complete 3-step" in method.__doc__
