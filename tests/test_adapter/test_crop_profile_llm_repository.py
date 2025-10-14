"""Tests for CropProfileLLMRepository."""

import pytest
from unittest.mock import AsyncMock
from typing import Dict, Any

from agrr_core.framework.repositories.crop_profile_llm_repository import (
    CropProfileLLMRepository,
)
from agrr_core.adapter.interfaces.llm_client import LLMClient


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self):
        self.struct = AsyncMock()
    
    async def struct(self, query: str, structure: Dict[str, Any], instruction: str = None) -> Dict[str, Any]:
        """Mock struct method."""
        pass


class TestCropProfileLLMRepository:
    """Test cases for CropProfileLLMRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_client = MockLLMClient()
        self.repository = CropProfileLLMRepository(self.mock_llm_client)
    
    @pytest.mark.asyncio
    async def test_extract_crop_variety(self):
        """Test Step 1: Crop variety extraction."""
        crop_query = "トマト アイコ"
        
        self.mock_llm_client.struct.return_value = {
            "data": {
                "crop_name": "トマト",
                "variety": "アイコ"
            }
        }
        
        result = await self.repository.extract_crop_variety(crop_query)
        
        # Verify struct was called with correct parameters
        self.mock_llm_client.struct.assert_called_once()
        call_args = self.mock_llm_client.struct.call_args
        assert call_args[0][0] == crop_query
        assert "crop_name" in call_args[0][1]
        assert "variety" in call_args[0][1]
        assert "Extract crop name and variety" in call_args[0][2]
        
        # Verify result
        assert result["crop_name"] == "トマト"
        assert result["variety"] == "アイコ"
    
    @pytest.mark.asyncio
    async def test_define_growth_stages(self):
        """Test Step 2: Growth stage definition."""
        crop_name = "トマト"
        variety = "アイコ"
        
        self.mock_llm_client.struct.return_value = {
            "data": {
                "crop_info": {
                    "name": "トマト",
                    "variety": "アイコ"
                },
                "growth_periods": [
                    {
                        "period_name": "播種～育苗完了",
                        "order": 1,
                        "period_description": "発芽から本葉5-6枚まで"
                    }
                ]
            }
        }
        
        result = await self.repository.define_growth_stages(crop_name, variety)
        
        # Verify struct was called with correct parameters
        self.mock_llm_client.struct.assert_called_once()
        call_args = self.mock_llm_client.struct.call_args
        query = call_args[0][0]
        # Check for key terms from the actual prompt template
        assert "栽培期間構成調査" in query or "期間構成" in query
        assert crop_name in query
        assert variety in query
        assert "crop_info" in call_args[0][1]
        assert "growth_periods" in call_args[0][1]
        
        # Verify result
        assert result["crop_info"]["name"] == "トマト"
        assert len(result["growth_periods"]) == 1
    
    @pytest.mark.asyncio
    async def test_research_stage_requirements(self):
        """Test Step 3: Variety-specific requirement research."""
        crop_name = "トマト"
        variety = "アイコ"
        stage_name = "播種～育苗完了"
        stage_description = "発芽から本葉5-6枚まで"
        
        self.mock_llm_client.struct.return_value = {
            "data": {
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
        
        result = await self.repository.research_stage_requirements(
            crop_name, variety, stage_name, stage_description
        )
        
        # Verify struct was called with correct parameters
        self.mock_llm_client.struct.assert_called_once()
        call_args = self.mock_llm_client.struct.call_args
        query = call_args[0][0]
        assert "詳細要件調査・構造化" in query
        assert crop_name in query
        assert variety in query
        assert stage_name in query
        assert stage_description in query
        
        structure = call_args[0][1]
        assert "temperature" in structure
        assert "sunshine" in structure
        assert "thermal" in structure
        
        # Verify result
        assert result["temperature"]["base_temperature"] == 10.0
        assert result["sunshine"]["minimum_sunshine_hours"] == 4.0
        assert result["thermal"]["required_gdd"] == 300.0
    
    @pytest.mark.asyncio
    async def test_extract_crop_economics(self):
        """Test extracting crop economic information."""
        crop_name = "トマト"
        variety = "アイコ"
        
        self.mock_llm_client.struct.return_value = {
            "data": {
                "area_per_unit": 0.5,
                "revenue_per_area": 3000.0
            }
        }
        
        result = await self.repository.extract_crop_economics(crop_name, variety)
        
        # Verify struct was called with correct parameters
        self.mock_llm_client.struct.assert_called_once()
        call_args = self.mock_llm_client.struct.call_args
        query = call_args[0][0]
        assert crop_name in query
        assert variety in query
        assert "area_per_unit" in call_args[0][1]
        assert "revenue_per_area" in call_args[0][1]
        
        # Verify result
        assert result["area_per_unit"] == 0.5
        assert result["revenue_per_area"] == 3000.0
    
    @pytest.mark.asyncio
    async def test_extract_crop_family(self):
        """Test extracting crop family information."""
        crop_name = "トマト"
        variety = "アイコ"
        
        self.mock_llm_client.struct.return_value = {
            "data": {
                "family_ja": "ナス科",
                "family_scientific": "Solanaceae"
            }
        }
        
        result = await self.repository.extract_crop_family(crop_name, variety)
        
        # Verify struct was called with correct parameters
        self.mock_llm_client.struct.assert_called_once()
        call_args = self.mock_llm_client.struct.call_args
        query = call_args[0][0]
        assert crop_name in query
        assert variety in query
        assert "植物学的な科" in query or "family" in query
        assert "family_ja" in call_args[0][1]
        assert "family_scientific" in call_args[0][1]
        
        # Verify result
        assert result["family_ja"] == "ナス科"
        assert result["family_scientific"] == "Solanaceae"

