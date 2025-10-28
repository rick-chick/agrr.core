"""Tests for fertilizer LLM gateway."""

import pytest
from unittest.mock import AsyncMock

from agrr_core.adapter.gateways.fertilizer_llm_gateway import FertilizerLLMGateway
from agrr_core.entity.entities.fertilizer_entity import (
    FertilizerListRequest,
    FertilizerListResult,
    FertilizerDetailRequest,
    FertilizerDetail,
)


class TestFertilizerLLMGateway:
    """Tests for FertilizerLLMGateway."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def gateway(self, mock_llm_client):
        """Create gateway with mock LLM client."""
        return FertilizerLLMGateway(llm_client=mock_llm_client)
    
    @pytest.mark.asyncio
    async def test_search_list(self, gateway, mock_llm_client):
        """Test search_list method."""
        # Setup mock
        mock_llm_client.struct.return_value = {
            "data": {
                "fertilizer_products": ["ハイポネックス", "マグアンプK", "花王の農業用肥料"]
            }
        }
        
        # Execute
        request = FertilizerListRequest(language="ja", limit=3)
        result = await gateway.search_list(request)
        
        # Verify
        assert isinstance(result, FertilizerListResult)
        assert len(result.fertilizers) == 3
        assert result.fertilizers == ["ハイポネックス", "マグアンプK", "花王の農業用肥料"]
        
        # Verify LLM client was called
        mock_llm_client.struct.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_list_empty(self, gateway, mock_llm_client):
        """Test search_list with empty result."""
        # Setup mock
        mock_llm_client.struct.return_value = {
            "data": {
                "fertilizer_products": []
            }
        }
        
        # Execute
        request = FertilizerListRequest(language="en", limit=5)
        result = await gateway.search_list(request)
        
        # Verify
        assert isinstance(result, FertilizerListResult)
        assert len(result.fertilizers) == 0
    
    @pytest.mark.asyncio
    async def test_search_detail(self, gateway, mock_llm_client):
        """Test search_detail method."""
        # Setup mock
        mock_llm_client.struct.return_value = {
            "data": {
                "name": "尿素",
                "npk": "46-0-0",
                "manufacturer": "三井化学",
                "product_type": "化学肥料",
                "additional_info": "窒素肥料",
                "description": "高窒素含有量の肥料",
                "link": "https://example.com/urea"
            }
        }
        
        # Execute
        request = FertilizerDetailRequest(fertilizer_name="尿素")
        result = await gateway.search_detail(request)
        
        # Verify
        assert isinstance(result, FertilizerDetail)
        assert result.name == "尿素"
        assert result.npk == "46-0-0"
        assert result.manufacturer == "三井化学"
        assert result.product_type == "化学肥料"
        assert result.additional_info == "窒素肥料"
        assert result.description == "高窒素含有量の肥料"
        assert result.link == "https://example.com/urea"
        
        # Verify LLM client was called
        mock_llm_client.struct.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_detail_minimal(self, gateway, mock_llm_client):
        """Test search_detail with minimal fields."""
        # Setup mock
        mock_llm_client.struct.return_value = {
            "data": {
                "name": "urea",
                "npk": "46-0-0",
                "manufacturer": "",
                "product_type": "",
                "additional_info": "",
                "description": "",
                "link": ""
            }
        }
        
        # Execute
        request = FertilizerDetailRequest(fertilizer_name="urea")
        result = await gateway.search_detail(request)
        
        # Verify
        assert isinstance(result, FertilizerDetail)
        assert result.name == "urea"
        assert result.npk == "46-0-0"
        assert result.manufacturer is None
        assert result.product_type is None
        assert result.additional_info is None
        assert result.description == ""
        assert result.link is None  # Empty link becomes None
    
    @pytest.mark.asyncio
    async def test_search_list_with_area(self, gateway, mock_llm_client):
        """Test search_list method with area parameter."""
        # Setup mock
        mock_llm_client.struct.return_value = {
            "data": {
                "fertilizer_products": ["マグァンプ II Lサイズ 20kg", "アラガーデンファーム 即溶 14-6-10 20kg"]
            }
        }
        
        # Execute with area
        request = FertilizerListRequest(language="ja", limit=2, area_m2=100.0)
        result = await gateway.search_list(request)
        
        # Verify
        assert isinstance(result, FertilizerListResult)
        assert len(result.fertilizers) == 2
        assert result.fertilizers == ["マグァンプ II Lサイズ 20kg", "アラガーデンファーム 即溶 14-6-10 20kg"]
        
        # Verify LLM client was called
        mock_llm_client.struct.assert_called_once()

