"""Tests for CropProfileGatewayImpl."""

import pytest
from unittest.mock import Mock, AsyncMock

from agrr_core.adapter.gateways.crop_profile_gateway_impl import CropProfileGatewayImpl
from agrr_core.entity.entities.crop_profile_entity import CropProfile


class TestCropProfileGatewayImpl:
    """Test cases for CropProfileGatewayImpl."""
    
    def test_init_with_llm_client(self):
        """Test initialization with LLM repository."""
        mock_llm_repo = Mock()
        gateway = CropProfileGatewayImpl(llm_repository=mock_llm_repo)
        assert gateway.llm_repo is mock_llm_repo
    
    @pytest.mark.asyncio
    async def test_extract_crop_variety(self):
        """Test extract_crop_variety method."""
        mock_llm_repo = Mock()
        mock_llm_repo.extract_crop_variety = AsyncMock(return_value={
            "crop_name": "トマト", "variety": "アイコ"
        })
        
        gateway = CropProfileGatewayImpl(llm_repository=mock_llm_repo)
        result = await gateway.extract_crop_variety("トマト アイコ")
        
        assert result["crop_name"] == "トマト"
        assert result["variety"] == "アイコ"
        mock_llm_repo.extract_crop_variety.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_define_growth_stages(self):
        """Test define_growth_stages method."""
        mock_llm_repo = Mock()
        mock_llm_repo.define_growth_stages = AsyncMock(return_value={
            "crop_info": {"name": "トマト", "variety": "アイコ"},
            "growth_periods": [{"period_name": "生育期", "order": 1, "period_description": "test"}]
        })
        
        gateway = CropProfileGatewayImpl(llm_repository=mock_llm_repo)
        result = await gateway.define_growth_stages("トマト", "アイコ")
        
        assert result["crop_info"]["name"] == "トマト"
        assert len(result["growth_periods"]) == 1
        mock_llm_repo.define_growth_stages.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_research_stage_requirements(self):
        """Test research_stage_requirements method."""
        mock_llm_repo = Mock()
        mock_llm_repo.research_stage_requirements = AsyncMock(return_value={
            "temperature": {"base_temperature": 10.0, "optimal_min": 20.0, "optimal_max": 26.0},
            "sunshine": {"minimum_sunshine_hours": 3.0, "target_sunshine_hours": 6.0},
            "thermal": {"required_gdd": 400.0}
        })
        
        gateway = CropProfileGatewayImpl(llm_repository=mock_llm_repo)
        result = await gateway.research_stage_requirements("トマト", "アイコ", "生育期", "test description")
        
        assert result["temperature"]["base_temperature"] == 10.0
        assert result["sunshine"]["minimum_sunshine_hours"] == 3.0
        assert result["thermal"]["required_gdd"] == 400.0
        mock_llm_repo.research_stage_requirements.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_crop_economics(self):
        """Test extract_crop_economics method."""
        mock_llm_repo = Mock()
        mock_llm_repo.extract_crop_economics = AsyncMock(return_value={
            "area_per_unit": 0.5, "revenue_per_area": 3000.0
        })
        
        gateway = CropProfileGatewayImpl(llm_repository=mock_llm_repo)
        result = await gateway.extract_crop_economics("トマト", "アイコ")
        
        assert result["area_per_unit"] == 0.5
        assert result["revenue_per_area"] == 3000.0
        mock_llm_repo.extract_crop_economics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_crop_family(self):
        """Test extract_crop_family method."""
        mock_llm_repo = Mock()
        mock_llm_repo.extract_crop_family = AsyncMock(return_value={
            "family_ja": "ナス科", "family_scientific": "Solanaceae"
        })
        
        gateway = CropProfileGatewayImpl(llm_repository=mock_llm_repo)
        result = await gateway.extract_crop_family("トマト", "アイコ")
        
        assert result["family_ja"] == "ナス科"
        assert result["family_scientific"] == "Solanaceae"
        mock_llm_repo.extract_crop_family.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_crop_variety_without_llm_client(self):
        """Test methods without LLM repository (should raise error)."""
        gateway = CropProfileGatewayImpl()
        
        with pytest.raises(ValueError, match="LLM"):
            await gateway.extract_crop_variety("トマト")
    
    @pytest.mark.asyncio
    async def test_get_with_repository(self):
        """Test get method with repository configured."""
        # Mock repository
        mock_repo = Mock()
        mock_aggregate = Mock(spec=CropProfile)
        mock_repo.get = AsyncMock(return_value=mock_aggregate)
        
        # Setup gateway with repository
        gateway = CropProfileGatewayImpl(profile_repository=mock_repo)
        
        # Execute
        result = await gateway.get()
        
        # Verify
        assert result == mock_aggregate
        mock_repo.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_without_repository(self):
        """Test get method without repository (should raise error)."""
        gateway = CropProfileGatewayImpl(llm_repository=None, profile_repository=None)
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Profile repository not provided"):
            await gateway.get()