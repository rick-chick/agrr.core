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
    @pytest.mark.e2e
    async def test_struct_with_openai(self):
        """Test struct method with OpenAI API (requires OPENAI_API_KEY)."""
        structure = {"name": None, "value": None}
        query = "test query"
        instruction = "test instruction"
        
        result = await self.client.struct(query, structure, instruction)
        
        # Should return openai provider (since API key is configured)
        assert result["provider"] == "openai"
        assert "data" in result
        assert "schema" in result
    
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
                    "management_stages": [
                        {
                            "stage_name": "播種～育苗完了",
                            "management_focus": "温度管理",
                            "management_boundary": "本葉展開"
                        }
                    ]
                }
            }
            
            result = await self.client.step2_growth_stage_definition(crop_name, variety)
            
            # Verify struct was called with correct parameters
            mock_struct.assert_called_once()
            call_args = mock_struct.call_args
            query = call_args[0][0]
            # Check for key terms from the actual prompt template
            assert "栽培期間構成調査" in query or "期間構成" in query
            assert crop_name in query
            assert variety in query
            assert "crop_info" in call_args[0][1]
            assert "growth_periods" in call_args[0][1]
    
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
            # Step 3 no longer requires stage_name in the output structure
            # It returns only requirements (temperature, sunshine, thermal)
            assert "temperature" in structure
            assert "sunshine" in structure
            assert "thermal" in structure
            assert "base_temperature" in structure["temperature"]
            assert "optimal_min" in structure["temperature"]
            assert "minimum_sunshine_hours" in structure["sunshine"]
            assert "required_gdd" in structure["thermal"]
    
    # Note: execute_crop_requirement_flow has been removed from Framework layer
    # Flow orchestration is now handled in the Interactor layer (UseCase)
    # Individual step methods (step1, step2, step3) remain in Framework layer
    
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
    
    @pytest.mark.asyncio
    async def test_extract_crop_economics(self):
        """Test extracting crop economic information (area_per_unit and revenue_per_area)."""
        crop_name = "トマト"
        variety = "アイコ"
        
        with patch.object(self.client, 'struct', new_callable=AsyncMock) as mock_struct:
            mock_struct.return_value = {
                "data": {
                    "area_per_unit": 0.5,
                    "revenue_per_area": 3000.0
                }
            }
            
            result = await self.client.extract_crop_economics(crop_name, variety)
            
            # Verify struct was called with correct parameters
            mock_struct.assert_called_once()
            call_args = mock_struct.call_args
            query = call_args[0][0]
            assert crop_name in query
            assert variety in query
            assert "area_per_unit" in call_args[0][1]
            assert "revenue_per_area" in call_args[0][1]
            
            # Verify result structure
            assert result["data"]["area_per_unit"] == 0.5
            assert result["data"]["revenue_per_area"] == 3000.0