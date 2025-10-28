"""Input ports for fertilizer use cases."""

from abc import ABC, abstractmethod
from typing import Any

from agrr_core.usecase.dto.fertilizer_dto import (
    FertilizerListRequestDTO,
    FertilizerListResponseDTO,
    FertilizerDetailRequestDTO,
    FertilizerDetailResponseDTO,
)


class FertilizerListInputPort(ABC):
    """Input port for fertilizer list use case."""
    
    @abstractmethod
    async def execute(self, request: FertilizerListRequestDTO) -> FertilizerListResponseDTO:
        """Execute fertilizer list search.
        
        Args:
            request: FertilizerListRequestDTO
            
        Returns:
            FertilizerListResponseDTO
        """
        pass


class FertilizerDetailInputPort(ABC):
    """Input port for fertilizer detail use case."""
    
    @abstractmethod
    async def execute(self, request: FertilizerDetailRequestDTO) -> FertilizerDetailResponseDTO:
        """Execute fertilizer detail search.
        
        Args:
            request: FertilizerDetailRequestDTO
            
        Returns:
            FertilizerDetailResponseDTO
        """
        pass

