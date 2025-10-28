"""Interactor for fetching fertilizer detail information."""

from agrr_core.usecase.dto.fertilizer_dto import FertilizerDetailRequestDTO, FertilizerDetailResponseDTO
from agrr_core.usecase.gateways.fertilizer_gateway import FertilizerGateway
from agrr_core.usecase.ports.input.fertilizer_input_port import FertilizerDetailInputPort
from agrr_core.entity.entities.fertilizer_entity import FertilizerDetailRequest, FertilizerDetail


class FertilizerDetailInteractor(FertilizerDetailInputPort):
    """Interactor for searching detailed fertilizer information.
    
    This interactor searches for detailed information about a specific fertilizer
    including NPK ratio, description, and links using the LLM gateway.
    """
    
    def __init__(self, gateway: FertilizerGateway):
        """Initialize interactor.
        
        Args:
            gateway: FertilizerGateway for data access
        """
        self.gateway = gateway
    
    async def execute(self, request: FertilizerDetailRequestDTO) -> FertilizerDetailResponseDTO:
        """Execute fertilizer detail search.
        
        Args:
            request: FertilizerDetailRequestDTO with fertilizer name
            
        Returns:
            FertilizerDetailResponseDTO with NPK, description, and link
        """
        # Convert DTO to entity request
        entity_request = FertilizerDetailRequest(
            fertilizer_name=request.fertilizer_name
        )
        
        # Call gateway
        result: FertilizerDetail = await self.gateway.search_detail(entity_request)
        
        # Convert result to response DTO
        return FertilizerDetailResponseDTO(
            name=result.name,
            npk=result.npk,
            manufacturer=result.manufacturer,
            product_type=result.product_type,
            additional_info=result.additional_info,
            description=result.description,
            link=result.link
        )

