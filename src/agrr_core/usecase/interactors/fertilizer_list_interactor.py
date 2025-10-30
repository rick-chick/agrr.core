"""Interactor for listing popular fertilizers."""

from agrr_core.usecase.dto.fertilizer_dto import FertilizerListRequestDTO, FertilizerListResponseDTO
from agrr_core.usecase.gateways.fertilizer_gateway import FertilizerGateway
from agrr_core.usecase.ports.input.fertilizer_input_port import FertilizerListInputPort
from agrr_core.entity.entities.fertilizer_entity import FertilizerListRequest, FertilizerListResult

class FertilizerListInteractor(FertilizerListInputPort):
    """Interactor for searching popular fertilizers by language.
    
    This interactor searches for popular fertilizers in a given language
    using the LLM gateway and returns the fertilizer names.
    """
    
    def __init__(self, gateway: FertilizerGateway):
        """Initialize interactor.
        
        Args:
            gateway: FertilizerGateway for data access
        """
        self.gateway = gateway
    
    def execute(self, request: FertilizerListRequestDTO) -> FertilizerListResponseDTO:
        """Execute fertilizer list search.
        
        Args:
            request: FertilizerListRequestDTO with language and limit
            
        Returns:
            FertilizerListResponseDTO with list of fertilizer names
        """
        # Convert DTO to entity request
        entity_request = FertilizerListRequest(
            language=request.language,
            limit=request.limit,
            area_m2=request.area_m2
        )
        
        # Call gateway
        result: FertilizerListResult = self.gateway.search_list(entity_request)
        
        # Convert result to response DTO
        return FertilizerListResponseDTO(
            fertilizers=result.fertilizers
        )

