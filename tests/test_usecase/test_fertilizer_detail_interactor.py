"""Tests for fertilizer detail interactor."""

import pytest
from unittest.mock import AsyncMock

from agrr_core.usecase.interactors.fertilizer_detail_interactor import FertilizerDetailInteractor
from agrr_core.usecase.dto.fertilizer_dto import FertilizerDetailRequestDTO, FertilizerDetailResponseDTO
from agrr_core.entity.entities.fertilizer_entity import FertilizerDetailRequest, FertilizerDetail


class TestFertilizerDetailInteractor:
    """Tests for FertilizerDetailInteractor."""
    
    @pytest.fixture
    def mock_gateway(self):
        """Create a mock fertilizer gateway."""
        gateway = AsyncMock()
        return gateway
    
    @pytest.fixture
    def interactor(self, mock_gateway):
        """Create interactor with mock gateway."""
        return FertilizerDetailInteractor(gateway=mock_gateway)
    
    @pytest.mark.asyncio
    async def test_execute(self, interactor, mock_gateway):
        """Test execute method."""
        # Setup mock
        mock_gateway.search_detail.return_value = FertilizerDetail(
            name="尿素",
            npk="46-0-0",
            additional_info="窒素肥料",
            description="高窒素含有量の肥料",
            link="https://example.com/urea"
        )
        
        # Execute
        request = FertilizerDetailRequestDTO(fertilizer_name="尿素")
        response = await interactor.execute(request)
        
        # Verify
        assert isinstance(response, FertilizerDetailResponseDTO)
        assert response.name == "尿素"
        assert response.npk == "46-0-0"
        assert response.additional_info == "窒素肥料"
        assert response.description == "高窒素含有量の肥料"
        assert response.link == "https://example.com/urea"
        
        # Verify gateway was called correctly
        mock_gateway.search_detail.assert_called_once()
        call_args = mock_gateway.search_detail.call_args[0][0]
        assert isinstance(call_args, FertilizerDetailRequest)
        assert call_args.fertilizer_name == "尿素"
    
    @pytest.mark.asyncio
    async def test_execute_minimal(self, interactor, mock_gateway):
        """Test execute with minimal response."""
        # Setup mock
        mock_gateway.search_detail.return_value = FertilizerDetail(
            name="urea",
            npk="46-0-0"
        )
        
        # Execute
        request = FertilizerDetailRequestDTO(fertilizer_name="urea")
        response = await interactor.execute(request)
        
        # Verify
        assert isinstance(response, FertilizerDetailResponseDTO)
        assert response.name == "urea"
        assert response.npk == "46-0-0"
        assert response.additional_info is None
        assert response.description == ""
        assert response.link is None

