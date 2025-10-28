"""Gateway interface for fertilizer information."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from agrr_core.entity.entities.fertilizer_entity import FertilizerListRequest, FertilizerListResult, FertilizerDetailRequest, FertilizerDetail


class FertilizerGateway(ABC):
    """Gateway for fertilizer information retrieval.
    
    This gateway abstracts fertilizer data access and LLM-based information retrieval.
    """

    @abstractmethod
    async def search_list(self, request: FertilizerListRequest) -> FertilizerListResult:
        """Search for popular fertilizers in a given language.
        
        Args:
            request: FertilizerListRequest containing language and limit
            
        Returns:
            FertilizerListResult with list of fertilizer names
        """
        pass

    @abstractmethod
    async def search_detail(self, request: FertilizerDetailRequest) -> FertilizerDetail:
        """Search for detailed information about a specific fertilizer.
        
        Args:
            request: FertilizerDetailRequest containing fertilizer name
            
        Returns:
            FertilizerDetail with NPK, description, and link
        """
        pass

