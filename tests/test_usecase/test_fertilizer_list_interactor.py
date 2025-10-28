"""Tests for fertilizer list interactor."""

import pytest
from unittest.mock import AsyncMock

from agrr_core.usecase.interactors.fertilizer_list_interactor import FertilizerListInteractor
from agrr_core.usecase.dto.fertilizer_dto import FertilizerListRequestDTO, FertilizerListResponseDTO
from agrr_core.entity.entities.fertilizer_entity import FertilizerListRequest, FertilizerListResult


class TestFertilizerListInteractor:
    """Tests for FertilizerListInteractor."""
    
    @pytest.fixture
    def mock_gateway(self):
        """Create a mock fertilizer gateway."""
        gateway = AsyncMock()
        return gateway
    
    @pytest.fixture
    def interactor(self, mock_gateway):
        """Create interactor with mock gateway."""
        return FertilizerListInteractor(gateway=mock_gateway)
    
    @pytest.mark.asyncio
    async def test_execute(self, interactor, mock_gateway):
        """Test execute method."""
        # Setup mock
        mock_gateway.search_list.return_value = FertilizerListResult(
            fertilizers=["尿素", "硝酸アンモニウム", "過リン酸石灰"]
        )
        
        # Execute
        request = FertilizerListRequestDTO(language="ja", limit=3)
        response = await interactor.execute(request)
        
        # Verify
        assert isinstance(response, FertilizerListResponseDTO)
        assert len(response.fertilizers) == 3
        assert response.fertilizers == ["尿素", "硝酸アンモニウム", "過リン酸石灰"]
        
        # Verify gateway was called correctly
        mock_gateway.search_list.assert_called_once()
        call_args = mock_gateway.search_list.call_args[0][0]
        assert isinstance(call_args, FertilizerListRequest)
        assert call_args.language == "ja"
        assert call_args.limit == 3
    
    @pytest.mark.asyncio
    async def test_execute_empty_list(self, interactor, mock_gateway):
        """Test execute with empty list result."""
        # Setup mock
        mock_gateway.search_list.return_value = FertilizerListResult(fertilizers=[])
        
        # Execute
        request = FertilizerListRequestDTO(language="en", limit=5)
        response = await interactor.execute(request)
        
        # Verify
        assert isinstance(response, FertilizerListResponseDTO)
        assert len(response.fertilizers) == 0
        assert response.fertilizers == []

