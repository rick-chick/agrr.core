"""Tests for CropRequirementGatewayImpl."""

import pytest
from unittest.mock import Mock, AsyncMock

from agrr_core.adapter.gateways.crop_requirement_gateway_impl import CropRequirementGatewayImpl
from agrr_core.entity.entities.crop_requirement_aggregate_entity import CropRequirementAggregate


class TestCropRequirementGatewayImpl:
    """Test cases for CropRequirementGatewayImpl."""
    
    def test_init_with_llm_client(self):
        """Test initialization with LLM client."""
        mock_llm = Mock()
        gateway = CropRequirementGatewayImpl(llm_client=mock_llm)
        assert gateway.llm_client is mock_llm
        assert gateway.llm_repo is not None
    
    @pytest.mark.asyncio
    async def test_extract_crop_variety(self):
        """Test extract_crop_variety method."""
        mock_llm = Mock()
        mock_llm.struct = AsyncMock(return_value={
            "data": {"crop_name": "トマト", "variety": "アイコ"}
        })
        
        gateway = CropRequirementGatewayImpl(llm_client=mock_llm)
        result = await gateway.extract_crop_variety("トマト アイコ")
        
        assert result["crop_name"] == "トマト"
        assert result["variety"] == "アイコ"
        mock_llm.struct.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_define_growth_stages(self):
        """Test define_growth_stages method."""
        mock_llm = Mock()
        mock_llm.struct = AsyncMock(return_value={
            "data": {
                "crop_info": {"name": "トマト", "variety": "アイコ"},
                "growth_periods": [{"period_name": "生育期", "order": 1, "period_description": "test"}]
            }
        })
        
        gateway = CropRequirementGatewayImpl(llm_client=mock_llm)
        result = await gateway.define_growth_stages("トマト", "アイコ")
        
        assert result["crop_info"]["name"] == "トマト"
        assert len(result["growth_periods"]) == 1
        mock_llm.struct.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_research_stage_requirements(self):
        """Test research_stage_requirements method."""
        mock_llm = Mock()
        mock_llm.struct = AsyncMock(return_value={
            "data": {
                "temperature": {"base_temperature": 10.0, "optimal_min": 20.0, "optimal_max": 26.0},
                "sunshine": {"minimum_sunshine_hours": 3.0, "target_sunshine_hours": 6.0},
                "thermal": {"required_gdd": 400.0}
            }
        })
        
        gateway = CropRequirementGatewayImpl(llm_client=mock_llm)
        result = await gateway.research_stage_requirements("トマト", "アイコ", "生育期", "test description")
        
        assert result["temperature"]["base_temperature"] == 10.0
        assert result["sunshine"]["minimum_sunshine_hours"] == 3.0
        assert result["thermal"]["required_gdd"] == 400.0
        mock_llm.struct.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_crop_economics(self):
        """Test extract_crop_economics method."""
        mock_llm = Mock()
        mock_llm.struct = AsyncMock(return_value={
            "data": {"area_per_unit": 0.5, "revenue_per_area": 3000.0}
        })
        
        gateway = CropRequirementGatewayImpl(llm_client=mock_llm)
        result = await gateway.extract_crop_economics("トマト", "アイコ")
        
        assert result["area_per_unit"] == 0.5
        assert result["revenue_per_area"] == 3000.0
        mock_llm.struct.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_crop_family(self):
        """Test extract_crop_family method."""
        mock_llm = Mock()
        mock_llm.struct = AsyncMock(return_value={
            "data": {"family_ja": "ナス科", "family_scientific": "Solanaceae"}
        })
        
        gateway = CropRequirementGatewayImpl(llm_client=mock_llm)
        result = await gateway.extract_crop_family("トマト", "アイコ")
        
        assert result["family_ja"] == "ナス科"
        assert result["family_scientific"] == "Solanaceae"
        mock_llm.struct.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_crop_variety_without_llm_client(self):
        """Test methods without LLM client (should raise error)."""
        gateway = CropRequirementGatewayImpl()
        
        with pytest.raises(ValueError, match="LLM client not provided"):
            await gateway.extract_crop_variety("トマト")
    
    @pytest.mark.asyncio
    async def test_get_with_repository(self):
        """Test get method with repository configured."""
        # Mock repository
        mock_repo = Mock()
        mock_aggregate = Mock(spec=CropRequirementAggregate)
        mock_repo.get = AsyncMock(return_value=mock_aggregate)
        
        # Setup gateway with repository
        gateway = CropRequirementGatewayImpl(crop_requirement_repository=mock_repo)
        
        # Execute
        result = await gateway.get()
        
        # Verify
        assert result == mock_aggregate
        mock_repo.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_without_repository(self):
        """Test get method without repository (should raise error)."""
        gateway = CropRequirementGatewayImpl()
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="CropRequirementRepository not provided"):
            await gateway.get()